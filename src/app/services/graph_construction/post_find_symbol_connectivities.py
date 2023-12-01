# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.services.graph_construction.graph_service import GraphService
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.services.graph_construction.utils.id_builder_util import get_int_id_from_node_id
from app.models.bounding_box import BoundingBox
from app.models.graph_construction.connected_symbols_connection_item import ConnectedSymbolsConnectionItem
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.enums.graph_node_type import GraphNodeType
from app.models.graph_construction.traversal_connection import TraversalConnection
from app.models.line_detection.line_segment import LineSegment
from app.models.enums.flow_direction import FlowDirection


def _node_to_bounding_box(node: dict):
    '''Converts the node to a bounding box

    :param node: The node
    :type node: dict
    :return: The bounding box
    :rtype: BoundingBox
    '''

    if node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.symbol:
        return BoundingBox(**node)
    else:
        line_segment = LineSegment(**node)
        return BoundingBox(
            topX=line_segment.startX,
            topY=line_segment.startY,
            bottomX=line_segment.endX,
            bottomY=line_segment.endY
        )


def post_find_symbol_connectivities(
    graph_service: GraphService,
    symbol_connections: dict[str, list[TraversalConnection]],
    flow_direction_asset_ids: set[str],
    asset_valve_symbol_ids: set[str]
):
    '''Builds the output from the symbol connections and asset map.

    :param graph_service: The graph service
    :type graph_service: GraphService
    :param symbol_connections: The symbol connections
    :type symbol_connections: dict
    :param flow_direction_asset_ids: The flow direction asset ids
    :type flow_direction_asset_ids: set
    :param asset_valve_symbol_ids: The asset valve symbol ids
    :type asset_valve_symbol_ids: set
    :return: The output
    :rtype: list[ConnectedSymbolsItem]
    '''
    process_flow_assets = flow_direction_asset_ids.union(asset_valve_symbol_ids)

    output: list[ConnectedSymbolsItem] = []
    for asset_symbol_id, connected_nodes in symbol_connections.items():
        container_asset_data = graph_service.get_node(asset_symbol_id)
        connected_symbols: list[ConnectedSymbolsConnectionItem] = []
        for traversal_connection in connected_nodes:
            connected_node = traversal_connection.node_id
            visited_ids = traversal_connection.visited_ids

            should_have_flow_direction = (
                asset_symbol_id in process_flow_assets and
                connected_node in process_flow_assets
            )

            flow_direction = traversal_connection.flow_direction if should_have_flow_direction else FlowDirection.unknown

            # get the bounding boxes of the connected node
            segments = [_node_to_bounding_box(graph_service.get_node(node_id)) for node_id in visited_ids]

            asset_data = graph_service.get_node(connected_node)
            connected_symbol = ConnectedSymbolsConnectionItem(
                id=get_int_id_from_node_id(connected_node),
                label=asset_data[SymbolNodeKeysConfig.LABEL_KEY],
                text_associated=asset_data[SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY],
                segments=segments,
                flow_direction=flow_direction,
                bounding_box=BoundingBox(
                    topX=asset_data[SymbolNodeKeysConfig.TOP_X_KEY],
                    topY=asset_data[SymbolNodeKeysConfig.TOP_Y_KEY],
                    bottomX=asset_data[SymbolNodeKeysConfig.BOTTOM_X_KEY],
                    bottomY=asset_data[SymbolNodeKeysConfig.BOTTOM_Y_KEY],
                ))
            connected_symbols.append(connected_symbol)
        symbol_item = ConnectedSymbolsItem(
            id=get_int_id_from_node_id(asset_symbol_id),
            label=container_asset_data[SymbolNodeKeysConfig.LABEL_KEY],
            text_associated=container_asset_data[SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY],
            connections=connected_symbols,
            bounding_box=BoundingBox(
                    topX=container_asset_data[SymbolNodeKeysConfig.TOP_X_KEY],
                    topY=container_asset_data[SymbolNodeKeysConfig.TOP_Y_KEY],
                    bottomX=container_asset_data[SymbolNodeKeysConfig.BOTTOM_X_KEY],
                    bottomY=container_asset_data[SymbolNodeKeysConfig.BOTTOM_Y_KEY],
                ),
        )
        output.append(symbol_item)
    return output
