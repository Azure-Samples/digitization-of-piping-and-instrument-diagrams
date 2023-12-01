# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
from unittest.mock import MagicMock, patch, call
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.enums.graph_node_type import GraphNodeType
from app.models.line_detection.line_segment import LineSegment
from app.models.graph_construction.extended_line_segment import ExtendedLineSegment
from app.models.enums.arrow_direction import ArrowDirection
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.services.graph_construction.connect_lines_with_arrows import get_polygon_sides_with_arrow_orientation, connect_lines_with_arrows
import shapely
import numpy as np


class TestConnectLinesWithArrows(unittest.TestCase):

    def test_happy_path_get_polygon_sides_with_arrow_orientation(self):
        # arrange
        # Bounding box coordinates
        topX = 0.641
        topY = 0.025
        bottomX = 0.66
        bottomY = 0.06

        coords = (
            (topX, topY),
            (bottomX, topY),
            (bottomX, bottomY),
            (topX, bottomY)
        )

        polygon = shapely.Polygon(coords)

        # act
        actual = get_polygon_sides_with_arrow_orientation(polygon)

        # assert

        assert len(actual) == 4
        assert actual[0][0] == shapely.LineString([(topX, topY), (bottomX, topY)])
        assert actual[0][1] == ArrowDirection.down

        assert actual[1][0] == shapely.LineString([(bottomX, topY), (bottomX, bottomY)])
        assert actual[1][1] == ArrowDirection.left

        assert actual[2][0] == shapely.LineString([(bottomX, bottomY), (topX, bottomY)])
        assert actual[2][1] == ArrowDirection.up

        assert actual[2][0] == shapely.LineString([(bottomX, bottomY), (topX, bottomY)])
        assert actual[3][1] == ArrowDirection.right

    def test_connect_lines_with_arrows_single_line_top_direction(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.4,
                        'topY': 0.1,
                        'bottomX': 0.6,
                        'bottomY': 0.3,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.5,   # line 0 connected to arrow from top side
                        startY=0.3,
                        endX=0.5,
                        endY=1.0)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.5,
                                startY=0.299,
                                endX=0.5,
                                endY=1.0,
                                slope=np.inf),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-0'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.up)

    def test_connect_lines_with_arrows_single_line_right_direction(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.7,
                        'topY': 0.4,
                        'bottomX': 0.9,
                        'bottomY': 0.6,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.0,   # line 0 connected to arrow from top side
                        startY=0.5,
                        endX=0.7,
                        endY=0.5)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.0,
                                startY=0.5,
                                endX=0.701,
                                endY=0.5,
                                slope=0.0),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-0'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.right)

    def test_connect_lines_with_arrows_single_line_bottom_direction(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.4,
                        'topY': 0.7,
                        'bottomX': 0.6,
                        'bottomY': 0.9,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.5,   # line 0 connected to arrow from top side
                        startY=0.0,
                        endX=0.5,
                        endY=0.7)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.5,
                                startY=0.0,
                                endX=0.5,
                                endY=0.701,
                                slope=np.inf),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-0'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.down)

    def test_connect_lines_with_arrows_single_line_left_direction(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.1,
                        'topY': 0.4,
                        'bottomX': 0.3,
                        'bottomY': 0.6,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.3,   # line 0 connected to arrow from left side
                        startY=0.5,
                        endX=1.0,
                        endY=0.5)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.299,   # line 0 connected to arrow from left side
                                startY=0.5,
                                endX=1.0,
                                endY=0.5,
                                slope=np.inf),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-0'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.left)

    def test_connect_lines_with_arrows_single_line_non_centered(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.4,
                        'topY': 0.7,
                        'bottomX': 0.6,
                        'bottomY': 0.9,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.4,   # line 0 connected to arrow from top side
                        startY=0.0,
                        endX=0.4,
                        endY=0.7)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.4,
                                startY=0.0,
                                endX=0.4,
                                endY=0.701,
                                slope=np.inf),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], [])
        self.assertEqual(node['arrow_direction'], ArrowDirection.unknown)

    def test_connect_lines_with_arrows_multiple_lines_case_1(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.4,
                        'topY': 0.4,
                        'bottomX': 0.6,
                        'bottomY': 0.6,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0', 'l-1']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.5,   # line 0 connected to arrow from top side
                        startY=0.0,
                        endX=0.5,
                        endY=0.4),
            LineSegment(startX=0.5,   # line 1 connected to arrow from bottom side
                        startY=0.6,
                        endX=0.5,
                        endY=1.0)
        ]

        # Increase of 0.001 in the Y coordinate of the line segment
        extended_lines = [
            ExtendedLineSegment(startX=0.5,
                                startY=0.0,
                                endX=0.5,
                                endY=0.401,
                                slope=0.0),
            ExtendedLineSegment(startX=0.5,
                                startY=0.599,
                                endX=0.5,
                                endY=1.0,
                                slope=0.0)
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], [])
        self.assertEqual(node['arrow_direction'], ArrowDirection.unknown)

    def test_connect_lines_with_arrows_multiple_lines_case_2(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.1,
                        'topY': 0.1,
                        'bottomX': 0.3,
                        'bottomY': 0.3,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0', 'l-1']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.3,   # line 0 connected to arrow from right side
                        startY=0.1,
                        endX=1.0,
                        endY=0.1),
            LineSegment(startX=0.2,   # line 1 connected to arrow from bottom side
                        startY=0.3,
                        endX=0.2,
                        endY=1.0)
        ]

        # Increase of 0.001
        extended_lines = [
            ExtendedLineSegment(startX=0.299,   # line 0 connected to arrow from right side
                                startY=0.1,
                                endX=1.0,
                                endY=0.1,
                                slope=0.0),
            ExtendedLineSegment(startX=0.2,   # line 1 connected to arrow from bottom side
                                startY=0.299,
                                endX=0.2,
                                endY=1.0,
                                slope=np.inf)
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-1'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.up)

    def test_connect_lines_with_arrows_multiple_lines_case_3(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.1,
                        'topY': 0.4,
                        'bottomX': 0.3,
                        'bottomY': 0.6,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            return ['l-0', 'l-1', 'l-2']

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.1,   # line 0 connected to arrow from top side
                        startY=0.0,
                        endX=0.1,
                        endY=0.4),
            LineSegment(startX=0.1,   # line 1 connected to arrow from bottom side
                        startY=0.6,
                        endX=0.1,
                        endY=1.0),
            LineSegment(startX=0.3,   # line 2 connected to arrow from right side
                        startY=0.5,
                        endX=1.0,
                        endY=0.5)
        ]

        # Increase of 0.001
        extended_lines = [
            ExtendedLineSegment(startX=0.1,
                                startY=0.0,
                                endX=0.1,
                                endY=0.401,
                                slope=np.inf),
            ExtendedLineSegment(startX=0.1,
                                startY=0.599,
                                endX=0.1,
                                endY=1.0,
                                slope=np.inf),
            ExtendedLineSegment(startX=0.299,
                                startY=0.5,
                                endX=1.0,
                                endY=0.5,
                                slope=0.0)
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-2'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.left)

    def test_connect_lines_with_arrows_multiple_symbols_and_lines(self):
        def get_symbol_nodes_by_key(type, key):
            arrow_symbols = [
                (
                    's-1',
                    {
                        'topX': 0.1,
                        'topY': 0.1,
                        'bottomX': 0.3,
                        'bottomY': 0.3,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 1
                    }
                ),
                (
                    's-2',
                    {
                        'topX': 0.7,
                        'topY': 0.7,
                        'bottomX': 0.9,
                        'bottomY': 0.9,
                        'label': '24',
                        'score': None,
                        'text': '',
                        'type': GraphNodeType.symbol,
                        'id': 2
                    }
                ),
                (
                    's-3',
                    {
                        'topX': 0.7,
                        'topY': 0.2,
                        'bottomX': 0.9,
                        'bottomY': 0.4,
                        'label': '1',  # Not an arrow symbol
                        'score': None,
                        'text': 'LG-12345',
                        'type': GraphNodeType.symbol,
                        'id': 3
                    }
                )
            ]
            return arrow_symbols

        def get_neighbors(node_id):
            if node_id == 's-1':
                return ['l-0', 'l-1']
            elif node_id == 's-2':
                return ['l-2', 'l-3']
            return []

        # arrange
        mock_graph = MagicMock()
        mock_graph.get_symbol_nodes_by_key = MagicMock(wraps=get_symbol_nodes_by_key)
        mock_graph.get_neighbors = MagicMock(wraps=get_neighbors)

        config_mock = MagicMock()
        config_mock.arrow_symbol_label = '24'
        config_mock.centroid_distance_threshold = 0.5

        line_segments = [
            LineSegment(startX=0.3,   # line 0 connected to arrow s-1 from right side
                        startY=0.1,
                        endX=1.0,
                        endY=0.1),
            LineSegment(startX=0.2,   # line 1 connected to arrow s-1 from bottom side
                        startY=0.3,
                        endX=0.2,
                        endY=1.0),
            LineSegment(startX=0.9,   # line 2 connected to arrow s-2 from right side
                        startY=0.8,
                        endX=1.0,
                        endY=0.8),
            LineSegment(startX=0.7,   # line 2 connected to arrow s-2 from bottom side
                        startY=0.9,
                        endX=0.7,
                        endY=1.0),
        ]

        # Increase of 0.001
        extended_lines = [
            ExtendedLineSegment(startX=0.299,
                                startY=0.1,
                                endX=1.0,
                                endY=0.1,
                                slope=0.0),
            ExtendedLineSegment(startX=0.2,
                                startY=0.299,
                                endX=0.2,
                                endY=1.0,
                                slope=np.inf),
            ExtendedLineSegment(startX=0.899,
                                startY=0.8,
                                endX=1.0,
                                endY=0.8,
                                slope=0.0),
            ExtendedLineSegment(startX=0.7,
                                startY=0.899,
                                endX=0.7,
                                endY=1.0,
                                slope=np.inf),
        ]

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                   config_mock):
            arrow_nodes = connect_lines_with_arrows(mock_graph, line_segments, extended_lines)

        # assert
        node = arrow_nodes[0]

        self.assertEqual(node['id'], 1)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-1'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.up)

        node = arrow_nodes[1]

        self.assertEqual(node['id'], 2)
        self.assertEqual(node[SymbolNodeKeysConfig.SOURCES_KEY], ['l-2'])
        self.assertEqual(node['arrow_direction'], ArrowDirection.left)

        self.assertTrue('s-3' not in arrow_nodes)
