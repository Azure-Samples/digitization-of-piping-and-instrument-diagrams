# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.services.graph_construction.utils.id_builder_util import get_int_id_from_node_id, get_node_type_from_node_id
from app.utils.shapely_utils import bounding_box_to_polygon, convert_line_to_line_string, get_polygon_sides
from app.models.enums.graph_node_type import GraphNodeType
from app.models.symbol_detection.label import Label
from app.models.enums.arrow_direction import ArrowDirection
from app.models.line_detection.line_segment import LineSegment
from app.models.graph_construction.extended_line_segment import ExtendedLineSegment
from app.services.graph_construction.graph_service import GraphService
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.config import config
from typing import Tuple
import shapely


def connect_lines_with_arrows(
    graph: GraphService,
    line_segments: list[LineSegment],
    extended_lines: list[ExtendedLineSegment]
):
    """
        Connects lines with arrows
        :param graph: GraphService
        :param line_segments: Line segments
        :param extended_lines: Extended lines
        :return: Arrow nodes dictionary
    """

    arrow_line_dictionary = {}

    arrow_nodes = graph.get_symbol_nodes_by_key(SymbolNodeKeysConfig.LABEL_KEY, config.arrow_symbol_label)

    for arrow_node_id, arrow_node in arrow_nodes:
        arrow_label = Label.parse_obj(arrow_node)

        for node_id in graph.get_neighbors(arrow_node_id):
            if get_node_type_from_node_id(node_id) == GraphNodeType.line:  # Check to verify that the node is a line
                line_id = get_int_id_from_node_id(node_id)
                line_segment = line_segments[line_id]
                extended_line = extended_lines[line_id]

                # No need to continue if the source line is determined as unknown
                if node_id in arrow_line_dictionary and \
                   arrow_line_dictionary[node_id][1] == ArrowDirection.unknown:
                    break

                candidate_matching_for_source_line_to_arrow(arrow_node_id,
                                                            arrow_label,
                                                            node_id,
                                                            line_segment,
                                                            extended_line,
                                                            arrow_line_dictionary)

    for arrow_node_id, arrow_node in arrow_nodes:
        # If arrow node is not in the dictionary, it means that it is not connected to any centered line
        # Therefore, defaults to unknown direction
        if arrow_node_id not in arrow_line_dictionary:
            arrow_line_dictionary[arrow_node_id] = (None, ArrowDirection.unknown)

        candidate = arrow_line_dictionary[arrow_node_id]
        update_arrow_properties(arrow_node, candidate)

    # Exclude node id from graph
    arrow_data = list(map(lambda x: x[1].copy(), arrow_nodes))

    # convert set to list
    for arrow in arrow_data:
        arrow[SymbolNodeKeysConfig.SOURCES_KEY] = list(arrow[SymbolNodeKeysConfig.SOURCES_KEY])
    return arrow_data


def candidate_matching_for_source_line_to_arrow(arrow_node_id: str,
                                                arrow_label: Label,
                                                line_id: str,
                                                line: LineSegment,
                                                extended_line: ExtendedLineSegment,
                                                arrow_line_dictionary: dict):
    symbol_polygon = bounding_box_to_polygon(arrow_label)
    extended_linestring = convert_line_to_line_string(extended_line)

    # Sanity check when there are associations between the line and the arrow that do not intersect
    if not extended_linestring.intersects(symbol_polygon):
        return

    intersection_line_string = extended_linestring.intersection(symbol_polygon)
    point1 = shapely.Point(intersection_line_string.coords[0])
    point2 = shapely.Point(intersection_line_string.coords[1])

    # Get the closest point from the non-extended lines to the intersected points
    # Result. Min distance from start/end point of the line to the intersected points
    start_point = shapely.Point(line.startX, line.startY)
    end_point = shapely.Point(line.endX, line.endY)

    distance_point1 = min(point1.distance(start_point), point1.distance(end_point))
    distance_point2 = min(point2.distance(start_point), point2.distance(end_point))

    closest_point = None
    if distance_point1 < distance_point2:
        closest_point = point1
    else:
        closest_point = point2

    # Check the side of the polygon that the closest point is on
    linestrings_from_polygon = get_polygon_sides_with_arrow_orientation(symbol_polygon)

    for line_side, arrow_direction in linestrings_from_polygon:
        # No need to continue if the source line is determined as unknown
        if not closest_point.intersects(line_side):
            continue

        center_point = line_side.centroid
        distance = center_point.distance(closest_point) / (line_side.length / 2)

        # Distance threshold to check if the line is close enough to the center of the polygon
        if distance < config.centroid_distance_threshold:
            if arrow_node_id not in arrow_line_dictionary:
                arrow_line_dictionary[arrow_node_id] = (line_id, arrow_direction)
            else:
                arrow_line_dictionary[arrow_node_id] = (None, ArrowDirection.unknown)


def update_arrow_properties(arrow_label, candidate: Tuple[str, ArrowDirection]):
    source_line_id, arrow_direction = candidate

    # Set new arrow properties
    arrow_label[SymbolNodeKeysConfig.SOURCES_KEY] = {source_line_id} if source_line_id is not None else set()
    arrow_label['arrow_direction'] = arrow_direction


def get_polygon_sides_with_arrow_orientation(polygon: shapely.Polygon) -> list[(shapely.LineString, ArrowDirection)]:
    polygon_sides = get_polygon_sides(polygon)  # Order: Top, Right, Botton, Left
    assert len(polygon_sides) == 4  # A bounding box should have 4 sides

    # Based on the side order, we can infer the arrow direction
    arrow_direction_list = [ArrowDirection.down, ArrowDirection.left, ArrowDirection.up, ArrowDirection.right]
    return list(zip(polygon_sides, arrow_direction_list))
