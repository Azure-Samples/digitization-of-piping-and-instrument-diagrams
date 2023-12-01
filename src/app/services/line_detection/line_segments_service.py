# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from logger_config import get_logger
import time
import cv2
import numpy as np
from app.models.line_detection.line_segment import LineSegment
from app.models.bounding_box import BoundingBox
from typing import Optional
from app.utils.image_utils import is_data_element_within_bounding_box

logger = get_logger(__name__)


def detect_line_segments(pid_id: str,
                         preprocessed_image: np.ndarray,
                         image_height: int,
                         image_width: int,
                         max_line_gap: int,
                         threshold: int,
                         min_line_length: int,
                         rho: float,
                         theta_param: float,
                         bounding_box_inclusive:
                             Optional[BoundingBox],
                         ) -> list[LineSegment]:

    """
    Detects the line segments in the image using the text detection
    results and request params
    pid_id: The pid id
    preprocessed_image: The preprocessed image
    image_height: The image height
    image_width: The image width
    bounding_box_inclusive: The bounding box to reduce noise in this detection phase
    within which the lines will be returned
    max_line_gap: The maximum allowed gap between line segments
    to treat them as a single line
    threshold: The accumulator threshold parameter
    min_line_length: The min line length
    rho: The distance resolution of the accumulator in pixels
    theta_param: The angle resolution of the accumulator in radians
    :return: A list of line segments
    """
    logger.info('Starting to detect line segments using Hough transform')

    start = time.perf_counter()

    # Apply the Hough line transform to detect lines
    # rho: Distance resolution of the accumulator in pixels.
    # theta: Angle resolution of the accumulator in radians.
    # threshold: Accumulator threshold parameter.
    # Only those lines are returned that get enough votes ( >threshold ).
    # minLineLength: Minimum line length.
    # Line segments shorter than this are rejected.
    # maxLineGap: Maximum allowed gap between line segments
    # to treat them as a single line.
    hough_results_line_segments = cv2.HoughLinesP(
        preprocessed_image, rho=rho,
        theta=np.pi/theta_param,
        threshold=threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    output_line_segments = []

    for line in hough_results_line_segments:
        x1, y1, x2, y2 = line[0]

        '''sorting start and end points of the line segment such that
        left most point is start and right most is end for horizontal lines
        and top most point is start and bottom most is end for vertical lines
        this will help with line flow'''
        # Check if the line segment is horizontal
        if y1 == y2:
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
        # Check if the line segment is vertical
        elif x1 == x2:
            if y1 > y2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
        # The line segment is angled
        else:
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
            elif x1 == x2 and y1 > y2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1

        '''include lines that are within defined
        bounding box's coordinates (topX, topY, bottomX and bottomY)
        to avoid noise for line detection'''
        if is_data_element_within_bounding_box(bounding_box_inclusive, x1, y1, x2, y2):
            # Add the detected line to the list of line segments
            # and also normalise the coordinates
            output_line_segments.append(LineSegment(
                startX=x1/image_width,
                startY=y1/image_height,
                endX=x2/image_width,
                endY=y2/image_height
            ))

    end = time.perf_counter()

    logger.info('Completed detecting line segments after {:.4f} seconds'
                .format(end - start))

    return output_line_segments


if __name__ == "__main__":
    import argparse
    import os
    import json
    from app.services.blob_storage_client import blob_storage_client

    blob_storage_client.init()

    parser = argparse.ArgumentParser(
        description='Run line segment detection on the given image.')
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
        "--preprocessed-image-path",
        type=str,
        dest="preprocessed_image_path",
        help="The path to the preprocessed image",
        required=True
    )
    parser.add_argument(
        "--relevant-bounding-box-for-detection",
        dest="bounding_box_inclusive",
        type=json.loads,
        help="coordinates to exclude legend and outerbox border lines"
    )
    parser.add_argument(
        "--image-height",
        dest="image_height",
        type=int,
        help="image height"
    )
    parser.add_argument(
        "--image-width",
        dest="image_width",
        type=int,
        help="image width"
    )

    args = parser.parse_args()

    pid_id = args.pid_id
    image_path = args.image_path
    preprocessed_image_path = args.preprocessed_image_path
    bounding_box_inclusive = \
        args.bounding_box_inclusive

    if bounding_box_inclusive is not None:
        bounding_box = BoundingBox(
            topX=bounding_box_inclusive["topX"],
            topY=bounding_box_inclusive["topY"],
            bottomX=bounding_box_inclusive["bottomX"],
            bottomY=bounding_box_inclusive["bottomY"]
        )
    else:
        bounding_box = None

    if not os.path.exists(image_path):
        raise ValueError(f"Image path {image_path} does not exist")

    if not os.path.exists(preprocessed_image_path):
        raise ValueError(
            f"Preprocessed Image path {preprocessed_image_path} does not exist"
        )

    # get bytes from image_path file
    with open(image_path, "rb") as file:
        image_bytes = file.read()

    gray = cv2.cvtColor(cv2.imread(preprocessed_image_path),
                        cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    lines_list = detect_line_segments(
        pid_id, thresh,
        bounding_box,
        image_height=args.image_height,
        image_width=args.image_width
    )

    filename = os.path.splitext(os.path.basename(image_path))[0]
    results_output_path = os.path.join(os.path.dirname(__file__), 'output',
                                       filename + '_line_segments.json')
    # write lines_list to json file
    with open(results_output_path, 'w') as f:
        json.dump([line.__dict__ for line in lines_list], f, indent=4)
