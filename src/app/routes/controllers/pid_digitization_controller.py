from pydantic import Json
from app.config import config
from app.models.enums.inference_result import InferenceResult
from app.models.enums.job_status import JobStatus
from app.models.job_status_details import JobStatusDetails
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.text_detection.text_detection_inference_response import TextDetectionInferenceResponse
from app.models.graph_construction.graph_construction_request import GraphConstructionInferenceRequest
from app.services import (
    storage_path_template_builder,
    symbol_detection,
    text_detection,
    line_detection,
    graph_construction,
    graph_persistence
)
from app.services.blob_storage_client import blob_storage_client
from app.models.bounding_box import BoundingBox
from app.models.enums.job_step import JobStep
from app.models.line_detection.line_detection_response import LineDetectionInferenceResponse
from app.utils.image_utils import validate_normalized_bounding_box
from fastapi import APIRouter, Form, UploadFile, HTTPException, File, Body, Path, status
from fastapi.concurrency import run_in_threadpool
import json
import logger_config
from typing import Optional, Union
from datetime import datetime
from app.queue_consumer import submit_job
from app.models.graph_construction.graph_construction_response import GraphConstructionInferenceResponse
from app.models.image_response import ImageResponse
from fastapi.responses import StreamingResponse
import io


logger = logger_config.get_logger(__name__)
router = APIRouter(
    prefix='/api/pid-digitization',
    tags=['pid-digitization']
)


def _get_corrected_inference_result_path(
    inference_result_type: InferenceResult
):
    corrected_inference_result_path_map = {
        InferenceResult.symbol_detection: InferenceResult.text_detection,
        InferenceResult.text_detection: InferenceResult.graph_construction
    }
    return corrected_inference_result_path_map[inference_result_type]


def _exists_file(
    inference_result_path: str
):
    try:
        file_exists = blob_storage_client.blob_exists(inference_result_path)
    except Exception as e:
        logger.error(f'Exception while checking if blob exists: {e}')
        raise HTTPException(status_code=500, detail='Internal server error while checking if blob exists.')
    return file_exists


def _download_file(
    inference_result_path: str
):
    try:
        inference_results_bytes = blob_storage_client.download_bytes(inference_result_path)
    except Exception as e:
        logger.error(f'Exception while downloading inference results: {e}')
        raise HTTPException(status_code=500, detail='Internal server error while downloading.')
    return inference_results_bytes


def _check_if_job_exists(
        pid_id: str,
        inference_result_path: str,
        timeout: int
):
    job_status_path = storage_path_template_builder.build_inference_job_status_path(pid_id, inference_result_path)

    if _exists_file(job_status_path):
        job_status_bytes = _download_file(job_status_path)
        job_status_details = json.loads(job_status_bytes, object_hook=lambda d: JobStatusDetails(**d))

        job_status_to_wait_timeout_list = [JobStatus.submitted, JobStatus.in_progress]

        if job_status_details.status in job_status_to_wait_timeout_list and \
                datetime.utcnow().timestamp() - job_status_details.updated_at.timestamp() <= timeout:
            raise HTTPException(status_code=409,
                                detail=f'Graph construction job already exists for pid id {pid_id}.')


def _update_job_status(
        pid_id: str, job_step: JobStep, status: JobStatus, message: Optional[str] = None
):
    job_status_path = storage_path_template_builder\
        .build_inference_job_status_path(pid_id,
                                         InferenceResult.graph_construction)
    dt = datetime.utcnow().isoformat()
    job_status_details = JobStatusDetails(status=status, step=job_step,
                                          message=message, updated_at=dt)
    blob_storage_client.upload_bytes(job_status_path,
                                     json.dumps(job_status_details.dict(), default=str))


@router.post(
    '/symbol-detection/{pid_id}',
    response_model=SymbolDetectionInferenceResponse
)
async def detect_symbols(
    pid_id: str,
    bounding_box_inclusive_str: Json = Form({'topX': 0.0, 'topY': 0.0, 'bottomX': 1.0, 'bottomY': 1.0},
                                            description="The bounding box of the P&ID image without extraneous legend information."
                                                        + "This should be provided as a JSON string with the following format: "
                                                        + "{\"topX\": 0.0, \"topY\": 0.0, \"bottomX\": 1.0, \"bottomY\": 1.0}. "
                                                        + " The coordinates should be normalized to the range [0, 1]."
                                                        + " The default value is the entire image."),
    file: UploadFile = File(..., description="The P&ID image to detect symbols in."),
):
    '''Detects symbols in an image and returns the bounding boxes of the detected symbols.

    param pid: The PID.
    param bounding_box_inclusive_str: The bounding box of the P&ID image without extraneous legend information.
    param file: The image to detect symbols in.
    return: The bounding boxes of the detected symbols.
    rtype: symbol_detection.ObjectDetectionPrediction
    '''

    try:
        bounding_box_inclusive = BoundingBox(**bounding_box_inclusive_str)
        validate_normalized_bounding_box(bounding_box_inclusive)
    except ValueError as e:
        logger.warning(f'The bounding box provided for isolating the P&ID graph for image {pid_id} has invalid coordinates: {e}')
        raise HTTPException(status_code=400,
                            detail=f'The bounding_box_inclusive_str JSON string value provided for P&ID image {pid_id} is invalid.'
                            + ' Make sure that all coordinates (topX, topY, bottomX, bottomY) are present and in the range [0, 1].')

    logger.info(f"Detecting symbols for pid id {pid_id}")
    image_bytes = await file.read()

    output_image_path = storage_path_template_builder.build_output_image_path(pid_id,
                                                                              InferenceResult.symbol_detection,
                                                                              InferenceResult.symbol_detection.value)
    result = await symbol_detection.run_inferencing(
        pid_id,
        bounding_box_inclusive,
        config.inference_score_threshold,
        image_bytes,
        output_image_path,
    )
    return result


@router.post(
    '/text-detection/{pid_id}',
    response_model=TextDetectionInferenceResponse
)
async def detect_text(
    pid_id: str = Path(..., description="The P&ID image id"),
    corrected_symbol_detection_results: SymbolDetectionInferenceResponse = Body(..., description="The corrected symbol detection \
                                                                                inference results"),
):
    '''
    This endpoint takes in the P&ID image id to download the original image and recognize the texts of the image.
    Additionally, it takes in the corrected symbol detected inference results which will be stored and used to
    associate a text with a symbol.

    Returns the text detection inference results, which includes all text detected and
    the text and symbols associated on a P&ID image.
    '''

    logger.info(f"Detecting text for pid id {pid_id}")
    pid_image_path = storage_path_template_builder.build_image_path(pid_id, InferenceResult.symbol_detection)

    if not _exists_file(pid_image_path):
        logger.warning(f'Image not found for pid id {pid_id}')
        raise HTTPException(status_code=422,
                            detail=f'Pid image {pid_id} does not exist. Run symbol detection first.')

    bounding_box_inclusive = corrected_symbol_detection_results.bounding_box_inclusive

    if bounding_box_inclusive is not None:
        try:
            validate_normalized_bounding_box(bounding_box_inclusive)
        except ValueError as e:
            logger.warning(f'The bounding box provided for isolating the P&ID graph for image {pid_id} has invalid coordinates: {e}')
            raise HTTPException(status_code=400,
                                detail=f'The bounding_box_inclusive value provided for P&ID image {pid_id} is invalid.'
                                + ' Make sure that coordinates are normalized and in the range [0, 1].')

    pid_image = _download_file(pid_image_path)

    debug_image_text_path = storage_path_template_builder.build_debug_image_path(pid_id, InferenceResult.text_detection, 'text')
    output_image_symbol_and_text_path = storage_path_template_builder.build_output_image_path(pid_id,
                                                                                              InferenceResult.text_detection,
                                                                                              InferenceResult.text_detection.value)

    # sending the request in this manner will not block other requests
    # the request will take a bit longer to complete, but the other requests can go through in the meantime
    result = await run_in_threadpool(
        text_detection.run_inferencing,
        pid_id,
        corrected_symbol_detection_results,
        pid_image,
        config.text_detection_area_intersection_ratio_threshold,
        config.text_detection_distance_threshold,
        config.symbol_label_prefixes_with_text,
        debug_image_text_path,
        output_image_symbol_and_text_path)
    return result


@router.post(
    '/graph-construction/{pid_id}',
    status_code=status.HTTP_202_ACCEPTED
)
async def detect_lines_and_construct_graph(
    pid_id: str = Path(..., description="The P&ID image id"),
    graph_construction_request: GraphConstructionInferenceRequest = Body(..., description="The corrected text detection \
                                                                                inference results"),
):
    '''
    This endpoint takes in the P&ID image id and the text response and then will build an asset connected
    graph based on the line segments, text detection results and symbol associations.
    '''
    logger.info(f"Submitting graph construction job for pid id {pid_id}")
    pid_image_path = storage_path_template_builder.build_image_path(pid_id, InferenceResult.symbol_detection)

    if not _exists_file(pid_image_path):
        logger.warning(f'Image not found for pid id {pid_id}')
        raise HTTPException(status_code=422,
                            detail=f'Pid image {pid_id} does not exist. Run symbol detection first.')

    bounding_box_inclusive = graph_construction_request.bounding_box_inclusive

    if bounding_box_inclusive is not None:
        try:
            validate_normalized_bounding_box(bounding_box_inclusive)
        except ValueError as e:
            logger.warning(f'The bounding box provided for isolating the P&ID graph for image {pid_id} has invalid coordinates: {e}')
            raise HTTPException(status_code=400,
                                detail=f'The bounding_box_inclusive value provided for P&ID image {pid_id} is invalid.'
                                + ' Make sure that coordinates are normalized and in the range [0, 1].')

    _check_if_job_exists(pid_id, InferenceResult.graph_construction, config.line_detection_job_timeout_seconds)
    _update_job_status(pid_id, JobStep.line_detection, JobStatus.submitted)

    submit_job(func=process_line_detection_and_graph_construction_job, args=(pid_id, graph_construction_request,))

    return {"message": "Graph construction job submitted successfully."}


@router.post(
    '/graph-persistence/{pid_id}',
    status_code=status.HTTP_201_CREATED
)
async def persist_graph(
    pid_id: str = Path(..., description="The P&ID image id"),
    graph_persistence_request: GraphConstructionInferenceResponse = Body(..., description="Persist the final graph \
                                                                                into the graph database"),
):
    '''
    For the given P&ID image id, the graph output (if any) from the prior step is persisted in the graph database.
    '''
    logger.info(f"Storing the graph into the database for pid id {pid_id}")

    try:
        await run_in_threadpool(graph_persistence.persist, pid_id, graph_persistence_request.connected_symbols)
        logger.info(f"Graph persistence for pid id {pid_id} completed successfully")
    except Exception as e:
        logger.error(f'An unexpected error occurred during persisting the graph into the database for {pid_id}: {e}')
        raise HTTPException(status_code=500,
                            detail=f'An unexpected error happened during persisting the graph into the database for {pid_id}: {e}')

    return {"message": "Graph was successfully stored into the database."}


def process_line_detection_and_graph_construction_job(pid_id: str, text_detection_results: GraphConstructionInferenceRequest):
    line_detection_results = process_line_detection(pid_id, text_detection_results)
    process_graph_construction(pid_id, text_detection_results, line_detection_results)


def process_line_detection(pid_id: str, text_detection_results: GraphConstructionInferenceRequest):
    _update_job_status(pid_id, JobStep.line_detection, JobStatus.in_progress)

    pid_image_path = storage_path_template_builder.build_image_path(pid_id, InferenceResult.symbol_detection)
    pid_image = _download_file(pid_image_path)

    debug_image_preprocessed_path = storage_path_template_builder.build_debug_image_path(pid_id,
                                                                                         InferenceResult.graph_construction,
                                                                                         'preprocessed')
    debug_image_preprocessed_before_thinning_path = storage_path_template_builder.build_debug_image_path(
        pid_id, InferenceResult.graph_construction, 'preprocessed_before_thinning')
    output_image_line_segments_path = storage_path_template_builder.build_output_image_path(pid_id,
                                                                                            InferenceResult.graph_construction,
                                                                                            InferenceResult.line_detection.value)

    try:
        logger.info(f"Start line detection job for pid id {pid_id}")

        enable_thinning = config.enable_thinning_preprocessing_line_detection if text_detection_results.thinning_enabled is None \
            else text_detection_results.thinning_enabled
        threshold = config.line_detection_hough_threshold if text_detection_results.hough_threshold is None \
            else text_detection_results.hough_threshold

        # Validation for line detection parameters based on configured detect_dotted_lines value
        # Mirrors the validator in config.py
        if config.detect_dotted_lines is False:
            max_line_gap = None
            min_line_length = config.line_detection_hough_min_line_length
        else:
            max_line_gap = config.line_detection_hough_max_line_gap if text_detection_results.hough_max_line_gap is None \
                  else text_detection_results.hough_max_line_gap
            min_line_length = config.line_detection_hough_min_line_length if text_detection_results.hough_min_line_length is None \
                else text_detection_results.hough_min_line_length

        rho = config.line_detection_hough_rho if text_detection_results.hough_rho is None \
            else text_detection_results.hough_rho
        theta = config.line_detection_hough_theta if text_detection_results.hough_theta is None \
            else text_detection_results.hough_theta

        # Call line detection phase
        line_detection_response = line_detection.detect_lines(
            pid_id,
            pid_image,
            text_detection_results,
            enable_thinning,
            threshold,
            max_line_gap,
            min_line_length,
            rho,
            theta,
            text_detection_results.bounding_box_inclusive,
            text_detection_results.image_details.height,
            text_detection_results.image_details.width,
            debug_image_preprocessed_path,
            debug_image_preprocessed_before_thinning_path,
            output_image_line_segments_path
        )

        line_detection_response_path = storage_path_template_builder.build_inference_response_path(pid_id,
                                                                                                   InferenceResult.graph_construction,
                                                                                                   InferenceResult.line_detection.value)
        blob_storage_client.upload_bytes(line_detection_response_path, json.dumps(line_detection_response.dict()))

        logger.info(f"Line detection job for pid id {pid_id} completed successfully")
        _update_job_status(pid_id, JobStep.line_detection, JobStatus.done)

        return line_detection_response
    except Exception as ex:
        logger.error(f"An error has occurred in line detection job: {ex}")
        _update_job_status(pid_id, JobStep.line_detection, JobStatus.failure, str(ex))


def process_graph_construction(
        pid_id, text_detection_results: GraphConstructionInferenceRequest,
        line_detection_results: LineDetectionInferenceResponse):

    _update_job_status(pid_id, JobStep.graph_construction, JobStatus.in_progress)

    pid_image_path = storage_path_template_builder.build_image_path(pid_id, InferenceResult.symbol_detection)
    pid_image = _download_file(pid_image_path)

    output_image_graph_path = storage_path_template_builder.build_output_image_path(pid_id,
                                                                                    InferenceResult.graph_construction,
                                                                                    InferenceResult.graph_construction.value)
    debug_image_graph_connections_path = storage_path_template_builder.build_debug_image_path(pid_id,
                                                                                              InferenceResult.graph_construction,
                                                                                              'graph_connections')
    debug_image_graph_with_lines_and_symbols_path = storage_path_template_builder.build_debug_image_path(
        pid_id, InferenceResult.graph_construction, 'graph_with_lines_and_symbols')

    try:
        logger.info(f"Start graph construction job for pid id {pid_id}")

        # Call graph construction phase
        connected_symbols, arrow_nodes = graph_construction.construct_graph(pid_id,
                                                                            pid_image,
                                                                            text_detection_results,
                                                                            line_detection_results,
                                                                            output_image_graph_path,
                                                                            debug_image_graph_connections_path,
                                                                            debug_image_graph_with_lines_and_symbols_path,
                                                                            config.symbol_label_prefixes_to_include_in_graph_image_output)

        arrows_line_source_response_path = storage_path_template_builder.build_inference_response_path(pid_id,
                                                                                                       InferenceResult.graph_construction,
                                                                                                       'arrows_line_source')
        blob_storage_client.upload_bytes(arrows_line_source_response_path, json.dumps(arrow_nodes))

        graph_construction_response = GraphConstructionInferenceResponse(
            image_url=text_detection_results.image_url,
            image_details=text_detection_results.image_details,
            connected_symbols=connected_symbols)

        graph_construction_response_path = storage_path_template_builder.build_inference_response_path(
            pid_id,
            InferenceResult.graph_construction,
            InferenceResult.graph_construction.value)
        blob_storage_client.upload_bytes(graph_construction_response_path, json.dumps(graph_construction_response.dict()))

        logger.info(f"Graph construction job for pid id {pid_id} completed successfully")
        _update_job_status(pid_id, JobStep.graph_construction, JobStatus.done)
        return graph_construction_response
    except Exception as ex:
        logger.error(f"An error has occurred in graph construction job: {ex}")
        _update_job_status(pid_id, JobStep.graph_construction, JobStatus.failure, str(ex))
        return None


@router.get(
    '/{inference_result_type}/{pid_id}',
    response_model=Union[SymbolDetectionInferenceResponse, TextDetectionInferenceResponse,
                         LineDetectionInferenceResponse, GraphConstructionInferenceResponse]
)
async def get_inference_results(
    inference_result_type: InferenceResult,
    pid_id: str
):
    '''Gets the inference results for a given pid id and inference result type.

    param pid: The PID id.
    param inference_result_type: The inference result type.
    return: The inference results.
    rtype: symbol_detection.InferenceResponse
    '''

    logger.info(f"Getting inference results for pid {pid_id} and inference result type of {inference_result_type}")

    # Check if corrected inference results exist
    inference_result_path = None
    if inference_result_type == InferenceResult.symbol_detection or \
       inference_result_type == InferenceResult.text_detection:
        inference_result_path = storage_path_template_builder.build_inference_request_path(pid_id, _get_corrected_inference_result_path(
            inference_result_type))

    if inference_result_path is None or not _exists_file(inference_result_path):
        if inference_result_type == InferenceResult.symbol_detection or inference_result_type == InferenceResult.text_detection:
            inference_result_path = storage_path_template_builder.build_inference_response_path(pid_id, inference_result_type)
        elif inference_result_type == InferenceResult.line_detection or inference_result_type == InferenceResult.graph_construction:
            inference_result_path = storage_path_template_builder.build_inference_response_path(pid_id,
                                                                                                InferenceResult.graph_construction,
                                                                                                inference_result_type.value)
        elif inference_result_type == InferenceResult.graph_persistence:
            inference_result_path = storage_path_template_builder.build_inference_response_path(pid_id,
                                                                                                InferenceResult.graph_persistence)

        if not _exists_file(inference_result_path):
            logger.warning(f'Inference results not found for pid id {pid_id}')
            raise HTTPException(status_code=404, detail=f'Inference results not found for pid {pid_id}.')

    inference_results_bytes = _download_file(inference_result_path)

    headers = {'Content-Disposition': f'attachment; filename={inference_result_type.value}.json'}

    return StreamingResponse(io.BytesIO(inference_results_bytes), headers=headers)


@router.get(
    '/graph-construction/{pid_id}/status'
)
async def get_job_status(
    pid_id: str
):
    '''Gets the inference job status for a given pid id .
    param pid: The PID id.
    return: The JobStatus of pid_id.
    rtype: JobStatus
    '''

    logger.info(f"Getting job status for pid {pid_id}")

    # Check if corrected inference results exist
    inference_status_path = storage_path_template_builder.build_inference_job_status_path(pid_id, InferenceResult.graph_construction)

    if not _exists_file(inference_status_path):
        logger.warning(f'Inference results not found for pid id {pid_id}')
        raise HTTPException(status_code=404, detail=f'Inference results not found for pid {pid_id}.')

    inference_results_bytes = _download_file(inference_status_path)
    return json.loads(inference_results_bytes)


@router.get(
    '/{inference_result_type}/{pid_id}/images'
)
async def get_output_inference_images(
    pid_id: str,
    inference_result_type: InferenceResult
):
    '''
    Gets the inference output image for a given pid id and inference result type.
    param pid: The PID id.
    param inference_result_type: The inference result type.
    rtype: ImageResponse
    The inference output image has information overlayed on the original image
    that provides user insight into what was done in the inferencing service.
    '''

    postfix = inference_result_type.value

    if inference_result_type == InferenceResult.line_detection:
        inference_result_type = InferenceResult.graph_construction
        postfix = InferenceResult.line_detection.value

    output_image_path = storage_path_template_builder.build_output_image_path(pid_id,
                                                                              inference_result_type,
                                                                              postfix)

    if not _exists_file(output_image_path):
        logger.warning(f'Inference image not found for pid id {pid_id} and inference result type {inference_result_type}')
        raise HTTPException(status_code=404,
                            detail=f'Inference image not found for pid id {pid_id} and inference result type {inference_result_type}')

    image = _download_file(output_image_path)

    # file name with pid and detection step
    file_name = f'{pid_id}_{postfix}.png'
    return ImageResponse(image=image, filename=file_name)
