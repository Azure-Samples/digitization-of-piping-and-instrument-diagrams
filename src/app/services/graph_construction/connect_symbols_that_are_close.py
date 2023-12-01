# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.utils.shapely_utils import (bounding_box_to_polygon,
                                     is_high_overlap_in_horizontal_region,
                                     is_high_overlap_in_vertical_region,
                                     horizontal_shape_padding,
                                     vertical_shape_padding)
from app.services.graph_construction.graph_service import GraphService
from app.config import config
from app.services.graph_construction.utils.id_builder_util import create_node_id
from app.services.graph_construction.create_lines import create_line_between_two_boundingbox
from app.models.enums.graph_node_type import GraphNodeType
from logger_config import get_logger


logger = get_logger(__name__)


def connect_symbols_that_are_close(
    graph: GraphService,
    text_and_symbols_associated_list: list[SymbolAndTextAssociated],
    graph_symbol_to_symbol_distance_threshold: float
) -> GraphService:
    """
        Connects symbols that are close
        :param graph: Graph
        :param text_and_symbols_associated_list: Text and symbols associated list
        :return: Graph
    """

    symbols_with_low_degree = []  # lower than 2

    # Rule 1: Find symbols with low degree
    for symbol in text_and_symbols_associated_list:

        # In terms of process flow, all symbols must be connected to at least two other symbols
        if graph.get_degree(create_node_id(GraphNodeType.symbol, symbol.id)) < 2 or \
           symbol.label.startswith('Equipment/'):
            symbols_with_low_degree.append(symbol)

    logger.info(f'Number of symbols with low degree: {len(symbols_with_low_degree)}')

    # Rule 2: Connect symbols that are horizontally or vertically aligned and close.
    for i, symbol1 in enumerate(symbols_with_low_degree):
        for symbol2 in symbols_with_low_degree[i:]:
            if symbol1.id == symbol2.id:
                continue

            # Filter out symbols that are not in the mapping
            if symbol1.label.startswith(tuple(config.symbol_label_prefixes_to_connect_if_close)) and \
               symbol2.label.startswith(tuple(config.symbol_label_prefixes_to_connect_if_close)):
                connect(graph, symbol1, symbol2, graph_symbol_to_symbol_distance_threshold)

    return graph


def connect(graph: GraphService,
            symbol1: SymbolAndTextAssociated,
            symbol2: SymbolAndTextAssociated,
            graph_symbol_to_symbol_distance_threshold: float):
    symbol1_polygon = bounding_box_to_polygon(symbol1)
    symbol2_polygon = bounding_box_to_polygon(symbol2)

    if symbol1_polygon.distance(symbol2_polygon) > graph_symbol_to_symbol_distance_threshold:
        return

    did_horizontal_meet_criteria = False
    did_vertical_meet_criteria = False

    symbol1_horizontal_padding_polygon = horizontal_shape_padding(symbol1, graph_symbol_to_symbol_distance_threshold)
    symbol2_horizontal_padding_polygon = horizontal_shape_padding(symbol2, graph_symbol_to_symbol_distance_threshold)
    if symbol1_horizontal_padding_polygon.intersects(symbol2_horizontal_padding_polygon):
        did_horizontal_meet_criteria = is_high_overlap_in_vertical_region(
            symbol1_horizontal_padding_polygon,
            symbol2_horizontal_padding_polygon, config.graph_symbol_to_symbol_overlap_region_threshold)

    symbol1_vertical_padding_polygon = vertical_shape_padding(symbol1, graph_symbol_to_symbol_distance_threshold)
    symbol2_vertical_padding_polygon = vertical_shape_padding(symbol2, graph_symbol_to_symbol_distance_threshold)
    if symbol1_vertical_padding_polygon.intersects(symbol2_vertical_padding_polygon):
        did_vertical_meet_criteria = is_high_overlap_in_horizontal_region(
            symbol1_vertical_padding_polygon,
            symbol2_vertical_padding_polygon,
            config.graph_symbol_to_symbol_overlap_region_threshold)

    if not did_horizontal_meet_criteria and not did_vertical_meet_criteria:
        return

    symbol1_id = create_node_id(GraphNodeType.symbol, symbol1.id)
    symbol2_id = create_node_id(GraphNodeType.symbol, symbol2.id)

    logger.info(f'Connecting symbol {symbol1_id} with symbol {symbol2_id} because they are close')

    new_line = create_line_between_two_boundingbox(symbol1, symbol2)

    graph.add_node(f'l-{symbol1_id}-{symbol2_id}', node_type=GraphNodeType.line, **new_line.dict())
    graph.add_edge(symbol1_id, symbol2_id)
