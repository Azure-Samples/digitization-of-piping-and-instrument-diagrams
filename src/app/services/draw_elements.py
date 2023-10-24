import cv2
import numpy as np
from app.models.bounding_box import BoundingBox
from app.models.image_details import ImageDetails
from app.utils.image_utils import denormalize_coordinates
from typing import Optional
from app.models.line_detection.line_segment import LineSegment


VALID_COLOR = (0, 155, 0)
INVALID_COLOR = (0, 0, 255)
BOX_THICKNESS = 2
FONT_SCALE = 0.5
FONT_THICKNESS = 2
LINE_THICKNESS = 2


def draw_annotation_on_image(
    id: Optional[int],
    image: bytes,
    image_details: ImageDetails,
    bounding_box: BoundingBox,
    label: Optional[str],
    valid_bit: Optional[int],
    valid_color: tuple,
    invalid_color: tuple
):
    '''
        Draws the annotation on the image.

        :param image: The image.
        :type image: cv2.Mat
        :param bounding_box: The bounding box.
        :type bounding_box: BoundingBox
        :param label: The label.
        :type label: str
        :param valid_bit: The valid bit.
        :type valid_bit: int
        :param valid_color: The valid color.
        :type valid_color: tuple
        :invalid_color: The invalid color.
        :type invalid_color: tuple
    '''

    # get the bounding box coordinates
    bottomX, topX, bottomY, topY = denormalize_coordinates(
            bounding_box.bottomX,
            bounding_box.topX,
            bounding_box.bottomY,
            bounding_box.topY,
            image_details.height,
            image_details.width)

    x1 = int(topX)
    x2 = int(bottomX)
    y1 = int(topY)
    y2 = int(bottomY)

    if valid_bit is None:
        color = valid_color if label else invalid_color
    else:
        color = valid_color if valid_bit == 1 else invalid_color
    label = label or ''
    label = f'{id}: {label}' if id is not None else label

    # draw the bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), color, BOX_THICKNESS)
    cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, color, FONT_THICKNESS)


def draw_line(
        image: bytes,
        image_details: ImageDetails,
        line_segment: LineSegment,
        color: tuple
):
    x1, x2, y1, y2 = denormalize_coordinates(
        line_segment.startX,
        line_segment.endX,
        line_segment.startY,
        line_segment.endY,
        image_details.height,
        image_details.width)

    cv2.line(image, (x1, y1), (x2, y2), color, LINE_THICKNESS)


def draw_bounding_boxes(
    image_bytes: bytes,
    image_details: ImageDetails,
    ids: Optional[list[int]],
    bounding_boxes: list[BoundingBox],
    annotations: list[Optional[str]],
    valid_bit_array: Optional[list[int]] = None
) -> cv2.Mat:
    '''Draws the bounding boxes on the image.

    :param image_bytes: The image bytes.
    :type image_bytes: bytes
    :param image_details: The image details.
    :type image_details: ImageDetails
    :param bounding_boxes: The bounding boxes.
    :type bounding_boxes: list[BoundingBox]
    :param annotations: The annotations.
    :type annotations: list[str]
    :param valid_bit_array: The valid bit array.
    :type valid_bit_array: list[int]
    :return: The image with the bounding boxes drawn on it.
    :rtype: cv2.Mat'''

    if len(bounding_boxes) != len(annotations):
        raise ValueError('The number of bounding boxes must match the number of annotations.')

    ids = ids if ids else [None] * len(bounding_boxes)

    if len(ids) != len(bounding_boxes):
        raise ValueError('The number of ids must match the number of bounding boxes.')

    valid_bit_array = valid_bit_array if valid_bit_array else [None] * len(bounding_boxes)

    if len(valid_bit_array) != len(bounding_boxes):
        raise ValueError('The number of valid bit arrays must match the number of bounding boxes.')

    # convert the bytes to a cv2 image
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    for id, bounding_box, label, valid_bit in zip(ids, bounding_boxes, annotations, valid_bit_array):
        draw_annotation_on_image(
            id,
            image,
            image_details,
            bounding_box,
            label,
            valid_bit,
            VALID_COLOR,
            INVALID_COLOR)

    return image
