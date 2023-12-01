# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.text_detection.text_detection_inference_response import TextDetectionInferenceResponse
from app.models.text_detection.text_recognized import TextRecognized
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.bounding_box import BoundingBox
from app.services.draw_elements import draw_bounding_boxes
from app.services.text_detection.symbol_to_text_correlation_service import correlate_symbols_with_text
from app.services.text_detection.utils.ocr_client import ocr_client
from app.services.text_detection.utils.text_detection_image_preprocessor import TextDetectionImagePreprocessor
from app.utils.image_utils import normalize_coordinates
from app.utils.regex_utils import (
    does_string_contain_at_least_one_number_and_one_letter,
    does_string_contain_only_one_number_or_one_fraction)
import cv2
from fastapi import HTTPException
import io
from logger_config import get_logger
from typing import Optional

from app.config import config


logger = get_logger(__name__)


def _convert_text_detection_to_text_details(
    text_detection_results,
    image_height: int,
    image_width: int
):
    '''Converts the text detection results to text details.

    :param text_detection_results: The text detection results.
    :param image_height: The height of the image.
    :type image_height: int
    :param image_width: The width of the image.
    :type image_width: int
    :return: The text details.
    :rtype: Generator[TextRecognized, None, None]
    '''
    for text_detection_result in text_detection_results:
        text = text_detection_result[0]
        bounding_box = text_detection_result[1]
        x1, y1 = bounding_box[0]
        x2, y2 = bounding_box[1]
        x3, y3 = bounding_box[2]
        x4, y4 = bounding_box[3]
        top_x = min(x1, x2, x3, x4)
        top_y = min(y1, y2, y3, y4)
        bottom_x = max(x1, x2, x3, x4)
        bottom_y = max(y1, y2, y3, y4)
        top_x, top_y, bottom_x, bottom_y = normalize_coordinates(
            top_x,
            top_y,
            bottom_x,
            bottom_y,
            image_height,
            image_width
        )
        yield TextRecognized(
            text=text,
            topX=top_x,
            topY=top_y,
            bottomX=bottom_x,
            bottomY=bottom_y
        )


def run_inferencing(
    pid_id: str,
    symbol_detection_inference_results: SymbolDetectionInferenceResponse,
    image: bytes,
    area_threshold: float,
    distance_threshold: float,
    symbol_label_prefixes_with_text: set[str],
    debug_image_text_path: Optional[str],
    output_image_symbol_and_text_path: Optional[str]
) -> TextDetectionInferenceResponse:
    '''Runs inferencing on the image.

    :param pid_id: The pid id.
    :type pid_id: str
    :param symbol_detection_inference_results: The symbol detection inference results.
    :type symbol_detection_inference_results: SymbolDetectionInferenceResponse
    :param image: The image.
    :type image: bytes
    :param area_threshold: The area threshold.
    :type area_threshold: float
    :param distance_threshold: The distance threshold.
    :type distance_threshold: float
    :param symbol_label_prefixes_with_text: The symbol label prefixes with text.
    :type symbol_label_prefixes_with_text: set[str]
    :param debug_image_text_path: The debug image text path.
    :type debug_image_text_path: Optional[str]
    :param output_image_symbol_and_text_path: The debug image symbol and text path.
    :type output_image_symbol_and_text_path: Optional[str]
    :return: The text detection inference results.
    :rtype: TextDetectionInferenceResponse'''
    logger.info(f"Running inferencing for pid id {pid_id}")

    symbol_label_prefixes_with_text_lowered_tuple: tuple[str] = tuple(sorted([elem.lower() for elem in symbol_label_prefixes_with_text]))

    image_byte_stream = io.BytesIO(image)
    if (config.enable_preprocessing_text_detection):
        preprocessed_image = TextDetectionImagePreprocessor.preprocess(image)
        image_byte_stream = io.BytesIO(preprocessed_image)
    try:
        text_detection_inference_results = ocr_client.read_text(image_byte_stream)
    except Exception as e:
        logger.error(f'There was an error performing OCR on the image: {e}')
        raise HTTPException(status_code=500, detail='There was an internal issue performing OCR on the image.')

    text_details = _convert_text_detection_to_text_details(
        text_detection_inference_results,
        symbol_detection_inference_results.image_details.height,
        symbol_detection_inference_results.image_details.width
    )
    text_details = list(text_details)
    text_and_symbols_associated_list = correlate_symbols_with_text(
        text_details,
        symbol_detection_inference_results,
        area_threshold,
        distance_threshold,
        symbol_label_prefixes_with_text_lowered_tuple
    )

    inference_response = TextDetectionInferenceResponse(
        image_url=f'{pid_id}.png',
        image_details=symbol_detection_inference_results.image_details,
        bounding_box_inclusive=symbol_detection_inference_results.bounding_box_inclusive,
        all_text_list=text_details,
        text_and_symbols_associated_list=text_and_symbols_associated_list
    )

    logger.info(f"Saving images for pid id {pid_id}")
    # drawing text and symbol associated information image
    pruned_text_and_symbols_associated_list = []

    for result in text_and_symbols_associated_list:
        if result.text_associated is None or \
           does_string_contain_only_one_number_or_one_fraction(result.text_associated):
            continue

        if result.label.lower().startswith(symbol_label_prefixes_with_text_lowered_tuple):
            pruned_text_and_symbols_associated_list.append(result)

    ids: list[int] = [
        result.id for result in pruned_text_and_symbols_associated_list
    ]
    bounding_boxes: list[BoundingBox] = [
        BoundingBox(**result.dict()) for result in pruned_text_and_symbols_associated_list
    ]
    labels = [
        result.text_associated for result in pruned_text_and_symbols_associated_list
    ]
    valid_bit_array = [
        1 if does_string_contain_at_least_one_number_and_one_letter(result.text_associated or '') else 0
        for result in pruned_text_and_symbols_associated_list
    ]
    debug_symbol_with_text_image = draw_bounding_boxes(
        image,
        symbol_detection_inference_results.image_details,
        ids,
        bounding_boxes,
        labels,
        valid_bit_array)

    if (config.debug and debug_image_text_path):
        bounding_boxes: list[BoundingBox] = [
            BoundingBox(**result.dict()) for result in text_details
        ]
        labels = [result.text if result.text else '' for result in text_details]
        debug_text_image = draw_bounding_boxes(
            image,
            symbol_detection_inference_results.image_details,
            None,
            bounding_boxes,
            labels
        )

    try:
        cv2.imwrite(output_image_symbol_and_text_path, debug_symbol_with_text_image)
        if (config.debug and debug_image_text_path):
            cv2.imwrite(debug_image_text_path, debug_text_image)
    except Exception as e:
        logger.error(f"Error saving text detection output images: {e}")

    return inference_response


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Run text detection on the given image.')
    parser.add_argument(
        "--pid-id",
        type=str,
        dest="pid_id",
        help="The pid id",
        required=True
    )
    parser.add_argument(
        "--symbol-detection-inference-results-path",
        type=str,
        dest="symbol_detection_inference_results_path",
        help="The path to the symbol detection inference results",
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
        "--area-threshold",
        type=float,
        dest="area_threshold",
        help="The area threshold",
        default=0.8
    )
    parser.add_argument(
        "--distance-threshold",
        type=float,
        dest="distance_threshold",
        help="The distance threshold",
        default=0.01,
    )
    parser.add_argument(
        "--symbol-label-prefixes-with-text",
        type=str,
        dest="symbol_label_prefixes_with_text",
        help="A comma separated list of symbols that should have text",
        default="Instrument/,Equipment/,Piping/Endpoint/Pagination",
    )

    args = parser.parse_args()

    pid_id = args.pid_id
    symbol_detection_inference_results_path = args.symbol_detection_inference_results_path
    image_path = args.image_path
    area_threshold = args.area_threshold
    distance_threshold = args.distance_threshold
    symbol_label_prefixes_with_text = args.symbol_label_prefixes_with_text

    symbol_label_prefixes_with_text = symbol_label_prefixes_with_text.split(',')
    symbol_label_prefixes_with_text = set(symbol_label_prefixes_with_text)

    if not os.path.exists(symbol_detection_inference_results_path):
        raise ValueError(f"Symbol detection inference results path {symbol_detection_inference_results_path} does not exist")

    if not os.path.exists(image_path):
        raise ValueError(f"Image path {image_path} does not exist")

    with open(symbol_detection_inference_results_path, 'rb') as f:
        symbol_detection_inference_results = SymbolDetectionInferenceResponse.parse_raw(f.read())

    with open(image_path, 'rb') as f:
        image = f.read()

    print('Calling text detection endpoint')
    debug_image_symbols_and_text_path = os.path.join(os.path.dirname(__file__), 'output', f'{pid_id}.png')
    debug_image_text_path = os.path.join(os.path.dirname(__file__), 'output', f'{pid_id}_text.png')
    results_output_path = os.path.join(os.path.dirname(__file__), 'output', f'{pid_id}.json')

    inference_response = run_inferencing(
        pid_id,
        symbol_detection_inference_results,
        image,
        area_threshold,
        distance_threshold,
        symbol_label_prefixes_with_text,
        debug_image_text_path,
        debug_image_symbols_and_text_path
    )

    print('Saving output')
    with open(results_output_path, 'w') as f:
        f.write(inference_response.json())
