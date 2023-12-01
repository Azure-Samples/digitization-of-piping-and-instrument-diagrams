# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
from unittest.mock import MagicMock
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.enums.graph_node_type import GraphNodeType
from app.services.graph_construction.graph_service import GraphService
from app.services.graph_construction.post_find_symbol_connectivities import post_find_symbol_connectivities

from app.models.bounding_box import BoundingBox
from app.models.graph_construction.connected_symbols_connection_item import ConnectedSymbolsConnectionItem
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_construction.traversal_connection import TraversalConnection
from app.models.enums.flow_direction import FlowDirection
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig


class TestPostFindSymbolConnectivities(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        def get_node_mock(arg):
            if arg == 'l-1':
                return {
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.line,
                    'startX': 10,
                    'startY': 10,
                    'endX': 10,
                    'endY': 10,
                }
            elif arg == 'l-2':
                return {
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.line,
                    'startX': 11,
                    'startY': 11,
                    'endX': 11,
                    'endY': 11,
                }
            elif arg == 'l-3':
                return {
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.line,
                    'startX': 12,
                    'startY': 12,
                    'endX': 12,
                    'endY': 12,
                }
            elif arg == 's-l-1':
                return {
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.symbol,
                    'topX': 20,
                    'topY': 20,
                    'bottomX': 20,
                    'bottomY': 20,
                }
            elif arg == 's-1':
                return {
                    SymbolNodeKeysConfig.LABEL_KEY: 'equipment',
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.symbol,
                    SymbolNodeKeysConfig.TOP_X_KEY: 0,
                    SymbolNodeKeysConfig.TOP_Y_KEY: 0,
                    SymbolNodeKeysConfig.BOTTOM_X_KEY: 0,
                    SymbolNodeKeysConfig.BOTTOM_Y_KEY: 0,
                    SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'equipment 1'
                }
            elif arg == 's-2':
                return {
                    SymbolNodeKeysConfig.LABEL_KEY: 'equipment',
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.symbol,
                    SymbolNodeKeysConfig.TOP_X_KEY: 1,
                    SymbolNodeKeysConfig.TOP_Y_KEY: 1,
                    SymbolNodeKeysConfig.BOTTOM_X_KEY: 1,
                    SymbolNodeKeysConfig.BOTTOM_Y_KEY: 1,
                    SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'equipment 2'
                }
            elif arg == 's-3':
                return {
                    SymbolNodeKeysConfig.LABEL_KEY: 'sensor',
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.symbol,
                    SymbolNodeKeysConfig.TOP_X_KEY: 2,
                    SymbolNodeKeysConfig.TOP_Y_KEY: 2,
                    SymbolNodeKeysConfig.BOTTOM_X_KEY: 2,
                    SymbolNodeKeysConfig.BOTTOM_Y_KEY: 2,
                    SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'sensor 1'
                }
            elif arg == 's-4':
                return {
                    SymbolNodeKeysConfig.LABEL_KEY: 'sensor',
                    SymbolNodeKeysConfig.TYPE_KEY: GraphNodeType.symbol,
                    SymbolNodeKeysConfig.TOP_X_KEY: 3,
                    SymbolNodeKeysConfig.TOP_Y_KEY: 3,
                    SymbolNodeKeysConfig.BOTTOM_X_KEY: 3,
                    SymbolNodeKeysConfig.BOTTOM_Y_KEY: 3,
                    SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'sensor 2'
                }

        mock_graph_service = MagicMock(GraphService)
        mock_graph_service.get_node = get_node_mock

        symbol_connections = {
            's-1': [
                TraversalConnection(
                    node_id='s-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['l-1', 's-l-1'],
                ),
                TraversalConnection(
                    node_id='s-4',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['l-2'],
                ),
            ],
            's-2': [
                TraversalConnection(
                    node_id='s-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['l-3'],
                )
            ],
            's-3': [],
            's-4': [],
        }

        flow_direction_asset_ids = {'s-1'}
        valve_symbol_ids = {'s-2'}

        # act
        result = post_find_symbol_connectivities(
            symbol_connections=symbol_connections,
            flow_direction_asset_ids=flow_direction_asset_ids,
            graph_service=mock_graph_service,
            asset_valve_symbol_ids=valve_symbol_ids
        )

        # assert
        assert result == [
            ConnectedSymbolsItem(
                id=1,
                label='equipment',
                text_associated='equipment 1',
                bounding_box=BoundingBox(
                    topX=0,
                    topY=0,
                    bottomX=0,
                    bottomY=0,
                ),
                connections=[
                    ConnectedSymbolsConnectionItem(
                        id=2,
                        label='equipment',
                        text_associated='equipment 2',
                        flow_direction=FlowDirection.downstream,
                        bounding_box=BoundingBox(
                            topX=1,
                            topY=1,
                            bottomX=1,
                            bottomY=1,
                        ),
                        segments=[
                            BoundingBox(
                                topX=10,
                                topY=10,
                                bottomX=10,
                                bottomY=10,
                            ),
                            BoundingBox(
                                topX=20,
                                topY=20,
                                bottomX=20,
                                bottomY=20,
                            ),
                        ]
                    ),
                    ConnectedSymbolsConnectionItem(
                        id=4,
                        label='sensor',
                        text_associated='sensor 2',
                        flow_direction=FlowDirection.unknown,
                        bounding_box=BoundingBox(
                            topX=3,
                            topY=3,
                            bottomX=3,
                            bottomY=3,
                        ),
                        segments=[
                            BoundingBox(
                                topX=11,
                                topY=11,
                                bottomX=11,
                                bottomY=11,
                            ),
                        ]
                    ),
                ]
            ),
            ConnectedSymbolsItem(
                id=2,
                label='equipment',
                text_associated='equipment 2',
                bounding_box=BoundingBox(
                    topX=1,
                    topY=1,
                    bottomX=1,
                    bottomY=1,
                ),
                connections=[
                    ConnectedSymbolsConnectionItem(
                        id=3,
                        label='sensor',
                        text_associated='sensor 1',
                        flow_direction=FlowDirection.unknown,
                        bounding_box=BoundingBox(
                            topX=2,
                            topY=2,
                            bottomX=2,
                            bottomY=2,
                        ),
                        segments=[
                            BoundingBox(
                                topX=12,
                                topY=12,
                                bottomX=12,
                                bottomY=12,
                            ),
                        ]
                    ),
                ]
            ),
            ConnectedSymbolsItem(
                id=3,
                label='sensor',
                text_associated='sensor 1',
                bounding_box=BoundingBox(
                    topX=2,
                    topY=2,
                    bottomX=2,
                    bottomY=2,
                ),
                connections=[]
            ),
            ConnectedSymbolsItem(
                id=4,
                label='sensor',
                text_associated='sensor 2',
                bounding_box=BoundingBox(
                    topX=3,
                    topY=3,
                    bottomX=3,
                    bottomY=3,
                ),
                connections=[]
            ),
        ]
