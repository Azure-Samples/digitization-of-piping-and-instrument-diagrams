import cv2
import numpy as np
from typing import Optional, Tuple

from app.models.bounding_box import BoundingBox


def denormalize_coordinates(x1: float, x2: float, y1: float, y2: float, image_height: int, image_width: int):
    '''Denormalizes the coordinates.

    :param x1: The x1 coordinate.
    :type x1: float
    :param x2: The x2 coordinate.
    :type x2: float
    :param y1: The y1 coordinate.
    :type y1: float
    :param y2: The y2 coordinate.
    :type y2: float
    :param image_height: The height of the image.
    :type image_height: int
    :param image_width: The width of the image.
    :type image_width: int
    :return: The denormalized bounding box coordinates.
    :rtype: Tuple[int, int, int, int]'''

    return (
        int(x1 * image_width),
        int(x2 * image_width),
        int(y1 * image_height),
        int(y2 * image_height))


def normalize_coordinates(top_x: float, top_y: float, bottom_x: float, bottom_y: float, height: int, width: int):
    '''Normalizes the coordinates.

    :param top_x: The top x coordinate.
    :type top_x: float
    :param top_y: The top y coordinate.
    :type top_y: float
    :param bottom_x: The bottom x coordinate.
    :type bottom_x: float
    :param bottom_y: The bottom y coordinate.
    :type bottom_y: float
    :param height: The height of the image.
    :type height: int
    :param width: The width of the image.
    :type width: int
    :return: The normalized coordinates.
    :rtype: Tuple[float, float, float, float]
    '''

    return (
        top_x / width,
        top_y / height,
        bottom_x / width,
        bottom_y / height
    )


def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    '''Gets the dimensions of the image.

    :param image_bytes: The image bytes.
    :type image_bytes: bytes
    :return: The image dimensions.
    :rtype: Tuple[int, int]'''
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), -1)
    h, w = image.shape[:2]
    return h, w


def validate_normalized_bounding_box(bounding_box: BoundingBox):
    def _is_valid(coordinate: float):
        if coordinate < 0 or coordinate > 1:
            return False
        return True

    if not _is_valid(bounding_box.topX) or \
       not _is_valid(bounding_box.topY) or \
       not _is_valid(bounding_box.bottomX) or \
       not _is_valid(bounding_box.bottomY) or \
       bounding_box.topX > bounding_box.bottomX or \
       bounding_box.topY > bounding_box.bottomY:
        raise ValueError('Invalid bounding_box_inclusive coordinates. Normalized coordinates must be between 0 and 1.')


def is_data_element_within_bounding_box(bounding_box_inclusive: Optional[BoundingBox],
                                        topX: float,
                                        topY: float,
                                        bottomX: float,
                                        bottomY: float) -> bool:
    '''
    Checks if a data element is within the defined bounding box's coordinates.

    bounding_box_inclusive: BoundingBox coordinates provided to filter the data
    topX: float - Data element start or top X coordinate
    topY: float - Data element start or top Y coordinate
    bottomX: float - Data element end or bottom X coordinate
    bottomY: float - Data element end or bottom Y coordinate
    Returns: bool - True if the data element is within the bounding box, False otherwise
    '''

    if bounding_box_inclusive is None or (topX >= bounding_box_inclusive.topX and bottomX <= bounding_box_inclusive.bottomX
       and topY >= bounding_box_inclusive.topY and bottomY <= bounding_box_inclusive.bottomY):
        return True

    return False
