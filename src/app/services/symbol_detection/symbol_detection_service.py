# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from typing import Optional
from app.config import config
from app.models.symbol_detection import symbol_detection_inference_response
from app.models.symbol_detection.label import Label
from app.models.image_details import ImageDetails
from app.models.bounding_box import BoundingBox
from app.services.draw_elements import draw_bounding_boxes
from app.services.symbol_detection.symbol_detection_endpoint_client import symbol_detection_endpoint_client
from app.services.symbol_detection.utils.symbol_pruning_utils import prune_overlapping_symbols
from app.utils import image_utils
import cv2
from fastapi import HTTPException
import logger_config
from requests import HTTPError


logger = logger_config.get_logger(__name__)


async def run_inferencing(
    pid_id: str,
    bounding_box_inclusive: Optional[BoundingBox],
    inference_score_threshold: float,
    image_bytes: bytes,
    output_image_path: str
):
    '''Detects symbols in an image and returns the bounding boxes of the detected symbols.

    param pid: The PID.
    param image: The image to detect symbols in.
    param symbol_detection_endpoint_client: The symbol detection endpoint client.
    return: The bounding boxes of the detected symbols.
    rtype: symbol_detection.ObjectDetectionPrediction'''
    inference_result = None
    try:
        inference_result = symbol_detection_endpoint_client.send_request(image_bytes)
        logger.info(f'Symbol detection response successfully received for pid id {pid_id}')
    except HTTPError as e:
        logger.warning(f'Http error while calling symbol detection endpoint: {e}')

        status_code = e.response.status_code
        error_message = e.response.text

        if status_code < 500:
            raise HTTPException(status_code=status_code, detail=error_message)
        raise HTTPException(status_code=500, detail='There was an error while fetching the symbol detection results.')
    except Exception as e:
        logger.error(f'Exception while calling symbol detection endpoint: {e}')
        raise HTTPException(status_code=500, detail='Internal server error while fetching the symbol detection results.')

    image_height, image_width = image_utils.get_image_dimensions(image_bytes)
    image_details = ImageDetails(height=image_height, width=image_width)
    filtered_labels: list[Label] = []
    i = 0
    for prediction in inference_result['boxes']:
        # Only consider symbols that meet the required score threshold
        if prediction['score'] < inference_score_threshold:
            continue

        # Only consider symbols within the bounding box of the main content area
        if image_utils.is_data_element_within_bounding_box(bounding_box_inclusive,
                                                           prediction['box']['topX'],
                                                           prediction['box']['topY'],
                                                           prediction['box']['bottomX'],
                                                           prediction['box']['bottomY']):
            filtered_label = Label(
                id=i,
                topX=prediction['box']['topX'],
                bottomX=prediction['box']['bottomX'],
                topY=prediction['box']['topY'],
                bottomY=prediction['box']['bottomY'],
                label=prediction['label'],
                score=prediction['score'])
            filtered_labels.append(filtered_label)
            i += 1

    filtered_labels = prune_overlapping_symbols(filtered_labels, config.symbol_overlap_threshold)
    inference_results = symbol_detection_inference_response.SymbolDetectionInferenceResponse(
        image_details=image_details,
        image_url=f'{pid_id}.png',
        bounding_box_inclusive=bounding_box_inclusive,
        label=filtered_labels)

    # drawing the image with the boxes

    logger.debug('Drawing bounding boxes on image')
    ids: list[int] = [label.id for label in inference_results.label]
    bounding_boxes: list[BoundingBox] = [BoundingBox(**label.dict()) for label in inference_results.label]

    labels: list[str | None] = []
    for label in inference_results.label:
        # try to get the sub category from category/subcategory/display name
        if '/' in label.label:
            labels.append(label.label.split('/')[1])
        else:
            labels.append(label.label)

    bounding_box_image = draw_bounding_boxes(
        image_bytes,
        inference_results.image_details,
        ids,
        bounding_boxes,
        labels)

    try:
        cv2.imwrite(output_image_path, bounding_box_image)
    except Exception as e:
        logger.error(f'Exception while uploading to blob storage: {e}')

    # return the boxes
    return inference_results


if __name__ == "__main__":
    import argparse
    import asyncio
    import json
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pid-id",
        type=str,
        dest="pid_id",
        help="The pid id",
        required=True
    )
    parser.add_argument(
        "--image-path",
        type=str,
        dest="image_path",
        help="The path to the image",
        required=True
    )
    parser.add_argument(
        "--bounding-box-inclusive",
        type=BoundingBox,
        dest="bounding_box_inclusive",
        help="The normalized bounding box to consider for the image",
        default=BoundingBox(topX=0.0, topY=0.0, bottomX=1.0, bottomY=1.0)
    )
    parser.add_argument(
        "--inference-score-threshold",
        type=float,
        dest="inference_score_threshold",
        help="The inference score threshold",
        default=0.1
    )

    args = parser.parse_args()

    pid_id = args.pid_id
    image_path = args.image_path
    inference_score_threshold = args.inference_score_threshold
    bounding_box_inclusive = args.bounding_box_inclusive

    if not os.path.exists(image_path):
        raise Exception(f'Image path {image_path} does not exist')

    with open(args.image_path, 'rb') as f:
        image_bytes = f.read()

    print('Calling symbol detection endpoint')
    output_image_path = os.path.join(os.path.dirname(__file__), 'output', f'{pid_id}.png')
    results_output_path = os.path.join(os.path.dirname(__file__), 'output', f'{pid_id}.json')

    result = asyncio.run(run_inferencing(
        pid_id=pid_id,
        inference_score_threshold=inference_score_threshold,
        bounding_box_inclusive=bounding_box_inclusive,
        image_bytes=image_bytes,
        output_image_path=output_image_path
    ))

    # save the output
    print('Saving output')
    with open(results_output_path, 'w') as f:
        f.write(json.dumps(result.dict()))
