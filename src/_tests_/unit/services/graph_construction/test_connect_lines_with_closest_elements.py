# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.enums.graph_node_type import GraphNodeType
from app.services.graph_construction.connect_lines_with_closest_elements import connect_lines_with_closest_elements, create_line_from_boundingbox
from app.models.text_detection.text_recognized import TextRecognized
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.line_detection.line_segment import LineSegment
from app.services.graph_construction.graph_construction_service import initialize_graph
from app.models.bounding_box import BoundingBox

class TestConnectLinesWithClosestElements(unittest.TestCase):
    def test_happy_path_with_three_lines_one_symbols_one_text_one_line_unknown(self):
        # arrange
        line_connection_candidates = {}
        line_connection_candidates['0'] = {
            "start": {"node": "1", "type": GraphNodeType.symbol, "distance": 0.001, "intersection": False},
            "end": {"node": "1", "type": GraphNodeType.line, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['1'] = {
            "start": {"node": "0", "type": GraphNodeType.line, "distance": 0.001, "intersection": False},
            "end": {"node": "0", "type": GraphNodeType.text, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['2'] = {
            "start": {"node": "0", "type": GraphNodeType.text, "distance": 0.001, "intersection": False},
            "end": {"node": "0", "type": GraphNodeType.unknown, "distance": 0.001, "intersection": False},
        }

        all_text = [
            TextRecognized(
                topX=0.4,
                topY=0.1,
                bottomX=0.5,
                bottomY=0.2,
                text="text1"),
            TextRecognized(
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                text="lmi"),
        ]

        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='lmi',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                text_associated='lmi',
            )
        ]

        line_detection_results = [
            LineSegment(
                startX=0.2,
                startY=0.15,
                endX=0.3,
                endY=0.15
            ),
            LineSegment(
                startX=0.3,
                startY=0.15,
                endX=0.4,
                endY=0.15
            ),
            LineSegment(
                startX=0.5,
                startY=0.15,
                endX=0.6,
                endY=0.15
            )
        ]

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        connect_lines_with_closest_elements(graph, line_connection_candidates, all_text, line_detection_results)

        # assert
        g = graph.G

        self.assertEqual(len(g.nodes), 5)
        self.assertEqual(len(g.edges), 4)

        neighbors = list(g.neighbors('l-0'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('s-1' in neighbors)
        self.assertTrue('l-1' in neighbors)

        neighbors = list(g.neighbors('l-1'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('l-t-0' in neighbors)
        self.assertTrue('l-0' in neighbors)

        l_1_node = g.nodes['l-1']
        self.assertEqual(l_1_node['text_associated'], 'text1')

        neighbors = list(g.neighbors('l-2'))
        self.assertEqual(len(neighbors), 1)
        self.assertTrue('l-t-0' in neighbors)

    def test_happy_path_with_three_lines_one_symbols_one_text_all_connected(self):
        # arrange
        line_connection_candidates = {}
        line_connection_candidates['0'] = {
            "start": {"node": "1", "type": GraphNodeType.symbol, "distance": 0.001, "intersection": False},
            "end": {"node": "1", "type": GraphNodeType.line, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['1'] = {
            "start": {"node": "0", "type": GraphNodeType.line, "distance": 0.001, "intersection": False},
            "end": {"node": "0", "type": GraphNodeType.text, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['2'] = {
            "start": {"node": "0", "type": GraphNodeType.text, "distance": 0.001, "intersection": False},
        }

        all_text = [
            TextRecognized(
                topX=0.4,
                topY=0.1,
                bottomX=0.5,
                bottomY=0.2,
                text="text1")
        ]

        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='lmi',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                text_associated='lmi',
            )
        ]

        line_detection_results = [
            LineSegment(
                startX=0.2,
                startY=0.15,
                endX=0.3,
                endY=0.15
            ),
            LineSegment(
                startX=0.3,
                startY=0.15,
                endX=0.4,
                endY=0.15
            ),
            LineSegment(
                startX=0.5,
                startY=0.15,
                endX=0.6,
                endY=0.15
            )
        ]

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        connect_lines_with_closest_elements(graph, line_connection_candidates, all_text, line_detection_results)

        # assert
        g = graph.G

        self.assertEqual(len(g.nodes), 5)
        self.assertEqual(len(g.edges), 4)

        neighbors = list(g.neighbors('l-0'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('s-1' in neighbors)
        self.assertTrue('l-1' in neighbors)

        neighbors = list(g.neighbors('l-1'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('l-t-0' in neighbors)
        self.assertTrue('l-0' in neighbors)

        neighbors = list(g.neighbors('l-2'))
        self.assertEqual(len(neighbors), 1)
        self.assertTrue('l-t-0' in neighbors)

    def test_happy_path_with_two_lines_one_symbols_one_text_all_connected(self):
        # arrange
        line_connection_candidates = {}
        line_connection_candidates['0'] = {
            "start": {"node": "1", "type": GraphNodeType.symbol, "distance": 0.001, "intersection": False},
            "end": {"node": "1", "type": GraphNodeType.line, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['1'] = {
            "start": {"node": "0", "type": GraphNodeType.line, "distance": 0.001, "intersection": False},
            "end": {"node": "0", "type": GraphNodeType.text, "distance": 0.001, "intersection": False}
        }

        all_text = [
            TextRecognized(
                topX=0.4,
                topY=0.1,
                bottomX=0.5,
                bottomY=0.2,
                text="text1")
        ]

        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='lmi',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                text_associated='lmi',
            )
        ]

        line_detection_results = [
            LineSegment(
                startX=0.2,
                startY=0.15,
                endX=0.3,
                endY=0.15
            ),
            LineSegment(
                startX=0.3,
                startY=0.15,
                endX=0.4,
                endY=0.15
            )
        ]

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        connect_lines_with_closest_elements(graph, line_connection_candidates, all_text, line_detection_results)

        # assert
        g = graph.G

        self.assertEqual(len(g.nodes), 4)
        self.assertEqual(len(g.edges), 3)

        neighbors = list(g.neighbors('l-0'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('s-1' in neighbors)
        self.assertTrue('l-1' in neighbors)

        neighbors = list(g.neighbors('l-1'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('l-t-0' in neighbors)
        self.assertTrue('l-0' in neighbors)

    def test_happy_path_with_two_lines_two_symbols_all_connected(self):
        # arrange
        line_connection_candidates = {}
        line_connection_candidates['0'] = {
            "start": {"node": "1", "type": GraphNodeType.symbol, "distance": 0.001, "intersection": False},
            "end": {"node": "1", "type": GraphNodeType.line, "distance": 0.001, "intersection": False}
        }

        line_connection_candidates['1'] = {
            "start": {"node": "0", "type": GraphNodeType.line, "distance": 0.001, "intersection": False},
            "end": {"node": "2", "type": GraphNodeType.symbol, "distance": 0.001, "intersection": False}
        }

        all_text = [
            TextRecognized(topX=50, topY=50, bottomX=80, bottomY=80,
                           text="text1"),
            TextRecognized(topX=20, topY=20, bottomX=30, bottomY=30,
                           text="text3"),
        ]

        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='lmi',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                text_associated='lmi',
            ),
            SymbolAndTextAssociated(
                id=2,
                label='tag',
                score=None,
                topX=0.4,
                topY=0.1,
                bottomX=0.5,
                bottomY=0.2,
                text_associated='tag',
            )
        ]

        line_detection_results = [
            LineSegment(
                startX=0.2,
                startY=0.15,
                endX=0.3,
                endY=0.15
            ),
            LineSegment(
                startX=0.3,
                startY=0.15,
                endX=0.4,
                endY=0.15
            )
        ]

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        connect_lines_with_closest_elements(graph, line_connection_candidates, all_text, line_detection_results)

        # assert
        g = graph.G

        self.assertEqual(len(g.nodes), 4)
        self.assertEqual(len(g.edges), 3)

        neighbors = list(g.neighbors('l-0'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('s-1' in neighbors)
        self.assertTrue('l-1' in neighbors)

        neighbors = list(g.neighbors('l-1'))
        self.assertEqual(len(neighbors), 2)
        self.assertTrue('s-2' in neighbors)
        self.assertTrue('l-0' in neighbors)

    def test_happy_path_create_line_from_boundingbox_text_connected_from_left(self):
        # arrange
        boundingbox = BoundingBox(
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.3)

        line = LineSegment(
            startX=0.0,
            startY=0.15,
            endX=0.1,
            endY=0.15)

        # act
        line_segment = create_line_from_boundingbox(boundingbox, line)

        # assert
        self.assertEqual(line_segment.startX, 0.1)
        self.assertEqual(line_segment.startY, 0.15)
        self.assertEqual(line_segment.endX, 0.2)
        self.assertEqual(line_segment.endY, 0.15)

    def test_happy_path_create_line_from_boundingbox_text_connected_from_right(self):
        # arrange
        boundingbox = BoundingBox(
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.3)

        line = LineSegment(
            startX=0.2,
            startY=0.15,
            endX=0.3,
            endY=0.15)

        # act
        line_segment = create_line_from_boundingbox(boundingbox, line)

        # assert
        self.assertEqual(line_segment.startX, 0.1)
        self.assertEqual(line_segment.startY, 0.15)
        self.assertEqual(line_segment.endX, 0.2)
        self.assertEqual(line_segment.endY, 0.15)

    def test_happy_path_create_line_from_boundingbox_text_connected_from_top(self):
        # arrange
        boundingbox = BoundingBox(
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.3)

        line = LineSegment(
            startX=0.15,
            startY=0.3,
            endX=0.15,
            endY=0.4)

        # act
        line_segment = create_line_from_boundingbox(boundingbox, line)

        # assert
        self.assertEqual(line_segment.startX, 0.15)
        self.assertEqual(line_segment.startY, 0.1)
        self.assertEqual(line_segment.endX, 0.15)
        self.assertEqual(line_segment.endY, 0.3)

    def test_happy_path_create_line_from_boundingbox_text_connected_from_bottom(self):
        # arrange
        boundingbox = BoundingBox(
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.3)

        line = LineSegment(
            startX=0.15,
            startY=0.0,
            endX=0.15,
            endY=0.1)

        # act
        line_segment = create_line_from_boundingbox(boundingbox, line)

        # assert
        self.assertEqual(line_segment.startX, 0.15)
        self.assertEqual(line_segment.startY, 0.1)
        self.assertEqual(line_segment.endX, 0.15)
        self.assertEqual(line_segment.endY, 0.3)


