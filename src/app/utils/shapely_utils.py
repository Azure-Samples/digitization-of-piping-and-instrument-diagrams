# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.bounding_box import BoundingBox
import shapely

from app.models.line_detection.line_segment import LineSegment


def is_high_overlap(
    polygon_1: shapely.Polygon,
    polygon_2: shapely.Polygon,
    area_threshold: float
):
    '''Gets the ratio of the text overlap to the symbol.

    :param polygon_1: The text polygon.
    :type polygon_1: shapely.Polygon
    :param polygon_2: The symbol polygon.
    :type polygon_2: shapely.Polygon
    :param area_threshold: The threshold for the area of the text polygon.
    :type area_threshold: float
    :return: Whether the ratio of the text overlap to the symbol is greater than the threshold.
    :rtype: bool'''
    if not polygon_1.intersects(polygon_2):
        return False

    intersection = polygon_1.intersection(polygon_2)
    intersection_area = intersection.area
    polygon_1_area = polygon_1.area
    overlap_ratio = intersection_area / polygon_1_area

    return overlap_ratio > area_threshold


def bounding_box_to_polygon(bounding_box: BoundingBox):
    '''Converts a bounding box to coordinates.

    :param bounding_box: The bounding box.
    :type bounding_box: BoundingBox
    :return: The coordinates.
    :rtype: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    '''
    coords = (
        (bounding_box.topX, bounding_box.topY),
        (bounding_box.bottomX, bounding_box.topY),
        (bounding_box.bottomX, bounding_box.bottomY),
        (bounding_box.topX, bounding_box.bottomY)
    )
    polygon = shapely.Polygon(coords)
    return polygon


def convert_line_to_line_string(line: LineSegment):
    return shapely.LineString([
        (line.startX, line.startY),
        (line.endX, line.endY)
    ])


def get_polygon_sides(polygon: shapely.Polygon) -> list[shapely.LineString]:

    """
    When the shapely.Polygon represents a bounding box, this function
    returns the polygon sides of a bounding box in the following order:

    1. Top line
    2. Right line
    3. Bottom line
    4. Left line

    :param polygon: shapely.Polygon
    :return: list of shapely.LineString
    """
    b = polygon.boundary.coords
    linestrings_from_polygon = [shapely.LineString(b[k:k+2]) for k in range(len(b) - 1)]
    return linestrings_from_polygon


def is_high_overlap_in_horizontal_region(symbol1: shapely.Polygon,
                                         symbol2: shapely.Polygon,
                                         graph_symbol_to_symbol_overlap_region_threshold: float):
    symbol1_x1 = symbol1.exterior.coords[0][0]
    symbol1_x2 = symbol1.exterior.coords[2][0]

    symbol2_x1 = symbol2.exterior.coords[0][0]
    symbol2_x2 = symbol2.exterior.coords[2][0]

    # check that x1 and x2 are in the right orientation
    if symbol1_x1 > symbol1_x2:
        symbol1_x1, symbol1_x2 = symbol1_x2, symbol1_x1

    if symbol2_x1 > symbol2_x2:
        symbol2_x1, symbol2_x2 = symbol2_x2, symbol2_x1

    symbol1_x_dist = symbol1_x2 - symbol1_x1
    symbol2_x_dist = symbol2_x2 - symbol2_x1

    x_intersection_region = min(symbol1_x2, symbol2_x2) - max(symbol1_x1, symbol2_x1)

    if (x_intersection_region) / symbol1_x_dist >= graph_symbol_to_symbol_overlap_region_threshold:
        return True

    if (x_intersection_region) / symbol2_x_dist >= graph_symbol_to_symbol_overlap_region_threshold:
        return True

    return False


def is_high_overlap_in_vertical_region(symbol1: shapely.Polygon,
                                       symbol2: shapely.Polygon,
                                       graph_symbol_to_symbol_overlap_region_threshold: float):
    symbol1_y1 = symbol1.exterior.coords[0][1]
    symbol1_y2 = symbol1.exterior.coords[2][1]

    symbol2_y1 = symbol2.exterior.coords[0][1]
    symbol2_y2 = symbol2.exterior.coords[2][1]

    # check that y1 and y2 are in the right orientation
    if symbol1_y1 > symbol1_y2:
        symbol1_y1, symbol1_y2 = symbol1_y2, symbol1_y1

    if symbol2_y1 > symbol2_y2:
        symbol2_y1, symbol2_y2 = symbol2_y2, symbol2_y1

    symbol1_y_dist = symbol1_y2 - symbol1_y1
    symbol2_y_dist = symbol2_y2 - symbol2_y1

    y_intersection_region = min(symbol1_y2, symbol2_y2) - max(symbol1_y1, symbol2_y1)

    if (y_intersection_region / symbol1_y_dist) >= graph_symbol_to_symbol_overlap_region_threshold:
        return True

    if (y_intersection_region / symbol2_y_dist) >= graph_symbol_to_symbol_overlap_region_threshold:
        return True

    return False


def horizontal_shape_padding(bounding_box: BoundingBox, padding_distance: float):
    shape_padding = padding_distance / 2
    bounding_box_copy = bounding_box.copy()
    bounding_box_copy.bottomX = bounding_box_copy.bottomX + shape_padding
    bounding_box_copy.topX = bounding_box_copy.topX - shape_padding

    return bounding_box_to_polygon(bounding_box_copy)


def vertical_shape_padding(bounding_box: BoundingBox, padding_distance: float):
    shape_padding = padding_distance / 2
    bounding_box_copy = bounding_box.copy()
    bounding_box_copy.bottomY = bounding_box_copy.bottomY + shape_padding
    bounding_box_copy.topY = bounding_box_copy.topY - shape_padding

    return bounding_box_to_polygon(bounding_box_copy)
