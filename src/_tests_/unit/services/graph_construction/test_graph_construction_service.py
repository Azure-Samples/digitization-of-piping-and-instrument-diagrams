import os
import parameterized
import unittest
from unittest.mock import MagicMock
import networkx as nx
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.graph_construction.graph_construction_service import initialize_graph
from app.models.enums.graph_node_type import GraphNodeType
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.line_detection.line_segment import LineSegment
from app.models.line_detection.line_detection_response import LineDetectionInferenceResponse


class TestGraphConstructionService(unittest.TestCase):
    def test_happy_convert_symbols_lines_to_nodes(self):
        # arrange
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
                topY=0.4,
                bottomX=0.5,
                bottomY=0.5,
                text_associated='tag',
            )
        ]

        line_detection_results = [
            LineSegment(
                startX=0.1,
                startY=0.1,
                endX=0.2,
                endY=0.2
            ),
            LineSegment(
                startX=0.4,
                startY=0.4,
                endX=0.5,
                endY=0.5
            )
        ]

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        # assert
        self.assertEqual(len(graph.G.nodes), 4)

        node = graph.G.nodes['s-1']
        self.assertEqual(node['type'], GraphNodeType.symbol)
        self.assertEqual(node['label'], 'lmi')
        self.assertEqual(node['topX'], 0.1)
        self.assertEqual(node['topY'], 0.1)
        self.assertEqual(node['bottomX'], 0.2)
        self.assertEqual(node['bottomY'], 0.2)
        self.assertEqual(node['text_associated'], 'lmi')

        node = graph.G.nodes['s-2']
        self.assertEqual(node['type'], GraphNodeType.symbol)
        self.assertEqual(node['label'], 'tag')
        self.assertEqual(node['topX'], 0.4)
        self.assertEqual(node['topY'], 0.4)
        self.assertEqual(node['bottomX'], 0.5)
        self.assertEqual(node['bottomY'], 0.5)
        self.assertEqual(node['text_associated'], 'tag')

        node = graph.G.nodes['l-0']
        self.assertEqual(node['type'], GraphNodeType.line)
        self.assertEqual(node['startX'], 0.1)
        self.assertEqual(node['startY'], 0.1)
        self.assertEqual(node['endX'], 0.2)
        self.assertEqual(node['endY'], 0.2)

        node = graph.G.nodes['l-1']
        self.assertEqual(node['type'], GraphNodeType.line)
        self.assertEqual(node['startX'], 0.4)
        self.assertEqual(node['startY'], 0.4)
        self.assertEqual(node['endX'], 0.5)
        self.assertEqual(node['endY'], 0.5)

    def test_happy_convert_symbols_lines_to_nodes_when_no_lines(self):
        # arrange
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
                topY=0.4,
                bottomX=0.5,
                bottomY=0.5,
                text_associated='tag',
            )
        ]

        line_detection_results = []

        # act
        graph = initialize_graph(text_and_symbols_associated_list, line_detection_results)

        # assert
        self.assertEqual(len(graph.G.nodes), 2)

        node = graph.G.nodes['s-1']
        self.assertEqual(node['type'], GraphNodeType.symbol)
        self.assertEqual(node['label'], 'lmi')
        self.assertEqual(node['topX'], 0.1)
        self.assertEqual(node['topY'], 0.1)
        self.assertEqual(node['bottomX'], 0.2)
        self.assertEqual(node['bottomY'], 0.2)
        self.assertEqual(node['text_associated'], 'lmi')

        node = graph.G.nodes['s-2']
        self.assertEqual(node['type'], GraphNodeType.symbol)
        self.assertEqual(node['label'], 'tag')
        self.assertEqual(node['topX'], 0.4)
        self.assertEqual(node['topY'], 0.4)
        self.assertEqual(node['bottomX'], 0.5)
        self.assertEqual(node['bottomY'], 0.5)
        self.assertEqual(node['text_associated'], 'tag')
