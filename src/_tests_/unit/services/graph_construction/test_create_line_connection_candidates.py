from http.client import HTTPException
import math
import os
import sys
from unittest.mock import MagicMock, patch
import unittest
import pytest
from shapely import LineString, Polygon, Point

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.graph_construction.extended_line_segment \
    import ExtendedLineSegment
from app.models.line_detection.line_segment import LineSegment
from app.services.graph_construction.create_line_connection_candidates import \
  create_line_connection_candidates_helper, \
  create_line_connection_candidates, \
  create_line_to_line_connection_candidates
from app.models.enums.graph_node_type import GraphNodeType
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.text_detection.text_recognized import TextRecognized
from app.models.bounding_box import BoundingBox
from app.utils import shapely_utils


class TestCreateLineConnectionCandidates(unittest.TestCase):
    maxDiff = None
    graph_line_buffer = 0.001
    graph_distance_threshold_for_symbols = 0.001
    graph_distance_threshold_for_text = 0.001
    graph_distance_threshold_for_lines = 0.01

    def test_happy_path_simple_symbol_text(self):
        # Arrange
        line_segments = [LineSegment(startX=0.1, startY=0.5, endX=0.9, endY=0.5)]
        extended_line_segments = [ExtendedLineSegment(startX=0.05, startY=0.5, endX=0.95, endY=0.5, slope=0.0)]
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(**{'id': '0', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.05, 'bottomY': 0.05}),
            SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.45, 'bottomX': 1.0, 'bottomY': 0.55})]
        text_results = [
            TextRecognized(**{'topX': 0.1, 'topY': 0.5, 'bottomX': 0.2, 'bottomY': 0.51, 'text': 'test'})
        ]

        expected_result_candidates = {
            '0': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            }
        }

        # Act
        actual_result_candidates = create_line_connection_candidates(
            line_segments,
            extended_line_segments,
            text_and_symbols_associated_list,
            text_results,
            self.graph_line_buffer,
            self.graph_distance_threshold_for_symbols,
            self.graph_distance_threshold_for_text,
            self.graph_distance_threshold_for_lines)

        # Assert
        self.assertEqual(actual_result_candidates, expected_result_candidates)

    def test_happy_path_multiple_lines_adjacent(self):
        # Arrange
        line_segments = [  # T-junction
            LineSegment(startX=0.1, startY=0.5, endX=0.5, endY=0.5),
            LineSegment(startX=0.5, startY=0.5, endX=0.9, endY=0.5)]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.05, startY=0.5, endX=0.45, endY=0.5, slope=0.0),
            ExtendedLineSegment(startX=0.45, startY=0.5, endX=0.95, endY=0.5, slope=0.0)]
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(**{'id': '0', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.05, 'bottomY': 0.05}),
            SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.45, 'bottomX': 1.0, 'bottomY': 0.55}),
            SymbolAndTextAssociated(**{'id': '2', 'label': 'test', 'score': 0.9, 'topX': 0.5, 'topY': 0.9, 'bottomX': 0.55, 'bottomY': 1.0})]
        text_results = [
            TextRecognized(**{'topX': 0.1, 'topY': 0.5, 'bottomX': 0.2, 'bottomY': 0.51, 'text': 'test'})
        ]

        expected_result_candidates = {
            '0': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.line,
                    'distance': 0.0,
                    'intersection': False
                }
            },
            '1': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.line,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
        }

        # Act
        actual_result_candidates = create_line_connection_candidates(
            line_segments,
            extended_line_segments,
            text_and_symbols_associated_list,
            text_results,
            self.graph_line_buffer,
            self.graph_distance_threshold_for_symbols,
            self.graph_distance_threshold_for_text,
            self.graph_distance_threshold_for_lines)

        # Assert
        self.assertEqual(actual_result_candidates, expected_result_candidates)

    def test_happy_path_multiple_lines_with_t_junction(self):
        # Arrange
        line_segments = [  # T-junction
            LineSegment(startX=0.1, startY=0.5, endX=0.9, endY=0.5),
            LineSegment(startX=0.5, startY=0.5, endX=0.5, endY=0.9)]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.05, startY=0.5, endX=0.95, endY=0.5, slope=0.0),
            ExtendedLineSegment(startX=0.5, startY=0.45, endX=0.5, endY=0.95, slope=math.inf)]
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(**{'id': '0', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.05, 'bottomY': 0.05}),
            SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.45, 'bottomX': 1.0, 'bottomY': 0.55}),
            SymbolAndTextAssociated(**{'id': '2', 'label': 'test', 'score': 0.9, 'topX': 0.5, 'topY': 0.9, 'bottomX': 0.55, 'bottomY': 1.0})]
        text_results = [
            TextRecognized(**{'topX': 0.1, 'topY': 0.5, 'bottomX': 0.2, 'bottomY': 0.51, 'text': 'test'})
        ]

        expected_result_candidates = {
            '0': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
            '1': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.line,
                    'distance': 0.0,
                    'intersection': True
                },
                'end': {
                    'node': '2',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
        }

        # Act
        actual_result_candidates = create_line_connection_candidates(
            line_segments,
            extended_line_segments,
            text_and_symbols_associated_list,
            text_results,
            self.graph_line_buffer,
            self.graph_distance_threshold_for_symbols,
            self.graph_distance_threshold_for_text,
            self.graph_distance_threshold_for_lines)

        # Assert
        self.assertEqual(actual_result_candidates, expected_result_candidates)

    def test_happy_path_multiple_lines_with_four_way_intersection(self):
        # Arrange
        line_segments = [  # 4-way intersection
            LineSegment(startX=0.1, startY=0.5, endX=0.9, endY=0.5),
            LineSegment(startX=0.5, startY=0.1, endX=0.5, endY=0.9)]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.05, startY=0.5, endX=0.95, endY=0.5, slope=0.0),
            ExtendedLineSegment(startX=0.5, startY=0.05, endX=0.5, endY=0.95, slope=math.inf)]
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(**{'id': '0', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.05, 'bottomY': 0.05}),
            SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.45, 'bottomX': 1.0, 'bottomY': 0.55}),
            SymbolAndTextAssociated(**{'id': '2', 'label': 'test', 'score': 0.9, 'topX': 0.5, 'topY': 0.9, 'bottomX': 0.55, 'bottomY': 1.0}),
            SymbolAndTextAssociated(**{'id': '3', 'label': 'test', 'score': 0.9, 'topX': 0.45, 'topY': 0.1, 'bottomX': 0.55, 'bottomY': 0.15})]
        text_results = [
            TextRecognized(**{'topX': 0.1, 'topY': 0.5, 'bottomX': 0.2, 'bottomY': 0.51, 'text': 'test'})
        ]

        expected_result_candidates = {
            '0': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
            '1': {
                'start': {
                    'node': '3',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '2',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
        }

        # Act
        actual_result_candidates = create_line_connection_candidates(
            line_segments,
            extended_line_segments,
            text_and_symbols_associated_list,
            text_results,
            self.graph_line_buffer,
            self.graph_distance_threshold_for_symbols,
            self.graph_distance_threshold_for_text,
            self.graph_distance_threshold_for_lines)

        # Assert
        self.assertEqual(actual_result_candidates, expected_result_candidates)

    def test_happy_path_multiple_lines_no_intersection(self):
        # Arrange
        line_segments = [  # Two parallel lines
            LineSegment(startX=0.1, startY=0.5, endX=0.9, endY=0.5),
            LineSegment(startX=0.1, startY=0.1, endX=0.9, endY=0.1)]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.05, startY=0.5, endX=0.95, endY=0.5, slope=0.0),
            ExtendedLineSegment(startX=0.05, startY=0.1, endX=0.95, endY=0.1, slope=0.0)]
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(**{'id': '0', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.05, 'bottomY': 0.05}),
            SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.45, 'bottomX': 1.0, 'bottomY': 0.55}),
            SymbolAndTextAssociated(**{'id': '2', 'label': 'test', 'score': 0.9, 'topX': 0.9, 'topY': 0.1, 'bottomX': 0.95, 'bottomY': 0.15})]
        text_results = [
            TextRecognized(**{'topX': 0.1, 'topY': 0.5, 'bottomX': 0.2, 'bottomY': 0.51, 'text': 'test'}),
            TextRecognized(**{'topX': 0.1, 'topY': 0.1, 'bottomX': 0.2, 'bottomY': 0.11, 'text': 'test'})
        ]

        expected_result_candidates = {
            '0': {
                'start': {
                    'node': '0',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '1',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
            '1': {
                'start': {
                    'node': '1',
                    'type': GraphNodeType.text,
                    'distance': 0.0,
                    'intersection': False
                },
                'end': {
                    'node': '2',
                    'type': GraphNodeType.symbol,
                    'distance': 0.0,
                    'intersection': False
                }
            },
        }

        # Act
        actual_result_candidates = create_line_connection_candidates(
            line_segments,
            extended_line_segments,
            text_and_symbols_associated_list,
            text_results,
            self.graph_line_buffer,
            self.graph_distance_threshold_for_symbols,
            self.graph_distance_threshold_for_text,
            self.graph_distance_threshold_for_lines)

        # Assert
        self.assertEqual(actual_result_candidates, expected_result_candidates)


class TestCreateLineConnectionCandidatesHelper(unittest.TestCase):

    graph_distance_threshold_for_symbols = 0.001

    def test_happy_path_no_intersection_returns_candidates_unchanged(self):
        # Arrange
        symbol_item = SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.1, 'topY': 0.1, 'bottomX': 0.2, 'bottomY': 0.2})
        symbol_id = str(symbol_item.id)
        line_polygon_extended = LineString([(0.0, 0.0), (0.0, 0.0)])  # Note no intersection with symbol item
        start_point = Point((0.0, 0.0))
        end_point = Point((0.0, 0.0))
        node_type = GraphNodeType.symbol
        current_connection_candidates = {}

        # Act
        result_candidates = create_line_connection_candidates_helper(
                symbol_item,
                symbol_id,
                line_polygon_extended,
                start_point,
                end_point,
                node_type,
                self.graph_distance_threshold_for_symbols,
                current_connection_candidates)

        # Assert
        assert result_candidates == current_connection_candidates

    def test_happy_path_updates_candidate_if_not_already_set(self):
        # Arrange
        symbol_item = SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.0, 'bottomY': 0.0})
        symbol_id = str(symbol_item.id)
        line_polygon_extended = LineString([(0.0, 0.0), (1.0, 0.0)])
        start_point = Point((0.0, 0.0))
        end_point = Point((1.0, 0.0))
        node_type = GraphNodeType.symbol

        # Note 'start' node in below is not set, so we expect it to be set to the input symbol_item
        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': '0',
                'type': GraphNodeType.symbol,
                'distance': 0.1,
                'intersection': False
            }
        }

        expected_result_candidates = {
            'start': {
                'node': '1',
                'type': GraphNodeType.symbol,
                'distance': 0.0,
                'intersection': False
            },
            'end': {
                'node': '0',
                'type': GraphNodeType.symbol,
                'distance': 0.1,
                'intersection': False
            }
        }

        # Act
        result_candidates = create_line_connection_candidates_helper(
                symbol_item,
                symbol_id,
                line_polygon_extended,
                start_point,
                end_point,
                node_type,
                self.graph_distance_threshold_for_symbols,
                current_connection_candidates)

        # Assert
        assert result_candidates == expected_result_candidates

    def test_happy_path_updates_candidate_not_meeting_distance_threshold(self):
        # Arrange
        symbol_item = SymbolAndTextAssociated(**{'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.895, 'topY': 0.140, 'bottomX': 0.913, 'bottomY': 0.181})
        symbol_id = str(symbol_item.id)
        line_polygon_extended = LineString([(0.904, 0.0), (0.904, 0.335)])   # vertical line
        line_polygon_extended = line_polygon_extended.buffer(0.001)
        start_point = Point((0.904, 0.030))
        end_point = Point((0.904, 0.135))
        node_type = GraphNodeType.symbol

        # Note 'start' and 'end' nodes in below are not set, so we expect not to be updated as this
        # symbol and line are not connection candidates
        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
        }

        expected_result_candidates = dict(current_connection_candidates)  # an unmodified copy of current_connection_candidates

        # Act
        result_candidates = create_line_connection_candidates_helper(
                symbol_item,
                symbol_id,
                line_polygon_extended,
                start_point,
                end_point,
                node_type,
                self.graph_distance_threshold_for_symbols,
                current_connection_candidates)

        # Assert
        assert result_candidates == expected_result_candidates

    def test_happy_path_updates_candidate_if_new_distance_is_smaller(self):
        # Arrange
        symbol_item = SymbolAndTextAssociated(**{'id': '2', 'label': 'test', 'score': 0.9, 'topX': 0.0, 'topY': 0.0, 'bottomX': 0.0, 'bottomY': 0.0})
        symbol_id = str(symbol_item.id)
        line_polygon_extended = LineString([(0.0, 0.0), (1.0, 0.0)])
        start_point = Point((0.0, 0.0))
        end_point = Point((1.0, 0.0))
        node_type = GraphNodeType.symbol

        # Note 'start' node in below has a larger distance than the distance
        # from the input symbol_item, so we expect it to be updated
        current_connection_candidates = {
            'start': {
                'node': '1',
                'type': GraphNodeType.symbol,
                'distance': 0.2,
                'intersection': False
            },
            'end': {
                'node': '0',
                'type': GraphNodeType.symbol,
                'distance': 0.1,
                'intersection': False
            }
        }

        expected_result_candidates = {
            'start': {
                'node': '2',
                'type': GraphNodeType.symbol,
                'distance': 0.0,
                'intersection': False
            },
            'end': {
                'node': '0',
                'type': GraphNodeType.symbol,
                'distance': 0.1,
                'intersection': False
            }
        }

        # Act
        result_candidates = create_line_connection_candidates_helper(
                symbol_item,
                symbol_id,
                line_polygon_extended,
                start_point,
                end_point,
                node_type,
                self.graph_distance_threshold_for_symbols,
                current_connection_candidates)

        # Assert
        assert result_candidates == expected_result_candidates

    def test_invalid_item_bounding_box_raises_value_error(self):
        # Arrange
        # Invalid bounding box for this symbol item - missing topY, bottomX, bottomY
        symbol_item = {'id': '1', 'label': 'test', 'score': 0.9, 'topX': 0.1}
        symbol_id = symbol_item['id']
        line_polygon_extended = MagicMock()
        start_point = MagicMock()
        end_point = MagicMock()
        node_type = GraphNodeType.symbol
        current_connection_candidates = MagicMock()

        # Act
        with pytest.raises(ValueError) as e:
            create_line_connection_candidates_helper(
                symbol_item,
                symbol_id,
                line_polygon_extended,
                start_point,
                end_point,
                node_type,
                self.graph_distance_threshold_for_symbols,
                current_connection_candidates)

        # Assert
        assert e.type == ValueError
        assert 'Item does not have proper bounding box' in str(e.value)


class TestCreateLineToLineConnectionCandidates(unittest.TestCase):

    graph_line_buffer = 0.01
    line_distance_threshold = 0.02

    def test_horizontal_lines_not_touching(self):
        '''
        Test case to verify that the polygon intersection condition is not satisfied
        when considering two distant horizontal lines.
        '''
        # Arrange
        # Mock input data for 2 horizontal lines that are not close enough to be considered touching
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.4),
            LineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.8),
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.19, endX=0.31, endY=0.41, slope=1.0),
            ExtendedLineSegment(startX=0.49, startY=0.59, endX=0.71, endY=0.81, slope=1.0),
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point(source_line_segment.startX, source_line_segment.startY),
            Point(source_line_segment.endX, source_line_segment.endY),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        self.assertEqual(result, current_connection_candidates)

    def test_horizontal_lines_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two close horizontal lines
        that can be considered touching, and Case 2 condition is met.
        '''
        # Arrange
        # Mock input data for 2 horizontal line segments that are close to each other
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.2),
            LineSegment(startX=0.31, startY=0.2, endX=0.6, endY=0.2)
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.31, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.30, startY=0.2, endX=0.61, endY=0.2, slope=0.0)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_lines_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two horizontal lines
        with a common point where Case 2 condition is met.
        '''
        # Arrange
        # Mock input data for 2 horizontal line segments that are touching at a common point
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.2),
            LineSegment(startX=0.3, startY=0.2, endX=0.6, endY=0.2)
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.31, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.29, startY=0.2, endX=0.61, endY=0.2, slope=0.0)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_vertical_lines_not_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two vertical lines
        that are not close enough to be considered touching.
        '''
        # Arrange
        # Mock input data for vertical line segments that are not close enough to be considered touching
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.1, endY=0.3),
            LineSegment(startX=0.1, startY=0.4, endX=0.1, endY=0.6)
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.1, startY=0.19, endX=0.1, endY=0.31, slope=math.inf),
            ExtendedLineSegment(startX=0.1, startY=0.39, endX=0.1, endY=0.61, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        self.assertEqual(result, current_connection_candidates)

    def test_vertical_lines_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two vertical lines
        that are close enough to be considered touching and Case 2 condition is met.
        '''
        # Arrange
        # Mock input data for vertical line segments that are close to each other
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.1, endY=0.38),
            LineSegment(startX=0.1, startY=0.39, endX=0.1, endY=0.6)
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.1, startY=0.19, endX=0.1, endY=0.39, slope=math.inf),
            ExtendedLineSegment(startX=0.1, startY=0.38, endX=0.1, endY=0.61, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False,
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_vertical_lines_touching(self):
        '''
        Test to make sure the polygon intersects condition is met and candidate matching is true for 2 vertical lines
        that have a common point and Case 2 condition is met
        '''
        # Arrange
        # Mock input data for 2 vertical line segments that are touching
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.1, endY=0.4),
            LineSegment(startX=0.1, startY=0.4, endX=0.1, endY=0.6)
        ]
        extended_line_segments = [
            ExtendedLineSegment(startX=0.1, startY=0.19, endX=0.1, endY=0.41, slope=math.inf),
            ExtendedLineSegment(startX=0.1, startY=0.39, endX=0.1, endY=0.61, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': '1',
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False,
            },
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_vertical_lines_not_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are not close enough to be considered touching.
        '''
        # Arrange
        # Mock input data for horizontal and vertical line segments that are not close enough to be considered touching
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.2),  # horizontal
            LineSegment(startX=0.4, startY=0.2, endX=0.4, endY=0.4)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.31, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.4, startY=0.19, endX=0.4, endY=0.41, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        self.assertEqual(result, current_connection_candidates)

    def test_horizontal_vertical_lines_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are close enough to be considered touching and Case 2 condition is met
        '''
        # Arrange

        # Mock input data
        # horizontal and vertical line segments that are not touching each other
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.2),  # horizontal
            LineSegment(startX=0.31, startY=0.2, endX=0.31, endY=0.4)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.31, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.31, startY=0.19, endX=0.31, endY=0.41, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_vertical_lines_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are touching each other and Case 2 condition is met
        '''
        # Arrange
        # Mock input data for horizontal and vertical line segments that are touching each other
        line_segments = [
            LineSegment(startX=0.1222, startY=0.2333, endX=0.3444, endY=0.2333),  # horizontal
            LineSegment(startX=0.3444, startY=0.2444, endX=0.3444, endY=0.45555)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.1122, startY=0.2333, endX=0.3544, endY=0.2333, slope=0.0),
            ExtendedLineSegment(startX=0.3444, startY=0.2344, endX=0.3444, endY=0.46555, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end': {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.011099999999999999,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_vertical_lines_touching_with_existing_connection_lowdistance(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are touching each other and Case 2 condition is not met because of previously found closer candidate
        '''
        # Arrange
        # Mock input data
        # horizontal and vertical line segments that are touching each other
        line_segments = [
            LineSegment(startX=0.1222, startY=0.2333, endX=0.3444, endY=0.2333),  # horizontal
            LineSegment(startX=0.3444, startY=0.2444, endX=0.3444, endY=0.45555)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.1122, startY=0.2333, endX=0.3544, endY=0.2333, slope=0.0),
            ExtendedLineSegment(startX=0.3444, startY=0.2344, endX=0.3444, endY=0.46555, slope=math.inf)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "5",
                'type': GraphNodeType.line,
                'distance': 0.00199,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point((source_line_segment.startX, source_line_segment.startY)),
            Point((source_line_segment.endX, source_line_segment.endY)),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        self.assertEqual(result, current_connection_candidates)

    def test_horizontal_angled_lines_not_touching(self):
        '''
        Test case to verify polygon intersection condition is not met
        '''
        # Arrange
        # Mock input data for horizontal and angled line segments that that are not close enough to be considered touching
        line_segments = [
            LineSegment(startX=0.1, startY=0.3, endX=0.6, endY=0.3),  # horizontal
            LineSegment(startX=0.12, startY=0.29, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.3, endX=0.61, endY=0.3, slope=0.0),
            ExtendedLineSegment(startX=0.11, startY=0.28184, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        self.assertEqual(result, current_connection_candidates)

    def test_horizontal_angled_lines_close(self):
        '''
        Test case to verify polygon intersection condition is met for horizontal
        and angled lines that are close to each other but not touching.
        Case 1 is for the start point of the horizontal line
        '''
        # Arrange
        # Mock input data for horizontal and angled line segments that are close to each other
        line_segments = [
            LineSegment(startX=0.1, startY=0.3, endX=0.6, endY=0.3),  # horizontal
            LineSegment(startX=0.11, startY=0.29, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.3, endX=0.61, endY=0.3, slope=0.0),
            ExtendedLineSegment(startX=0.1, startY=0.28184, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.014142135623730954,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)  # check to see that horizontal and angled lines are connected

    def test_horizontal_angled_lines_touching(self):
        '''
        Test case for horizontal and angled lines that are touching each other
        Case 1 is met for the start point of the horizontal line
        '''
        # Arrange
        # Mock input data
        # horizontal and angled line segments that are touching each other
        line_segments = [
            LineSegment(startX=0.1, startY=0.3, endX=0.6, endY=0.3),  # horizontal
            LineSegment(startX=0.1, startY=0.3, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.3, endX=0.61, endY=0.3, slope=0.0),
            ExtendedLineSegment(startX=0.1, startY=0.28184, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_vertical_angled_lines_not_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a vertical and angled line
        that are not close enough to be considered touching.
        '''
        # Arrange
        # Mock input data
        # vertical and angled line segments that are not close enough to be considered touching
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.3, endY=0.6),  # vertical
            LineSegment(startX=0.1, startY=0.3, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.09, endX=0.3, endY=0.61, slope=0.0),
            ExtendedLineSegment(startX=0.1, startY=0.28184, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        self.assertEqual(result, current_connection_candidates)

    def test_vertical_angled_lines_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a vertical and angled line
        that are close enough to be considered touching.
        Case 1 is met
        '''
        # Arrange
        # Mock input data for vertical and angled line segments that are close to each other
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.3, endY=0.6),  # vertical
            LineSegment(startX=0.29, startY=0.11, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.09, endX=0.3, endY=0.61, slope=0.0),
            ExtendedLineSegment(startX=0.29, startY=0.11, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.014142135623730954,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_vertical_angled_lines_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a vertical and angled line
        that are touching each other.
        Case 2 is met
        '''
        # Arrange
        # Mock input data
        # vertical and angled line segments that are touching each other
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.3, endY=0.6),  # vertical
            LineSegment(startX=0.3, startY=0.6, endX=0.5, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.09, endX=0.3, endY=0.61, slope=0.0),
            ExtendedLineSegment(startX=0.3, startY=0.6, endX=0.51, endY=0.60816, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_angled_lines_not_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two angled lines
        that are not touching each other.
        '''
        # Arrange
        # Mock input data for two angled line segments that are not close enough to be touching each other
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6),  # angled
            LineSegment(startX=0.6, startY=0.1, endX=0.8, endY=0.6),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6, slope=0.81579),
            ExtendedLineSegment(startX=0.6, startY=0.1, endX=0.8, endY=0.6, slope=0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        self.assertEqual(result, current_connection_candidates)

    def test_angled_lines_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two angled lines
        that are close enough to be touching each other.
        Case 2 is met
        '''
        # Arrange
        # Mock input data for two angled line segments that are close enough to be touching each other
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6),  # angled
            LineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.1),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6, slope=0.81579),
            ExtendedLineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.1, slope=-0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_angled_lines_touching(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for two angled lines
        that are touching each other. Case 2 is met
        '''
        # Arrange
        # Mock input data for two angled line segments that are touching each other
        line_segments = [
            LineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6),  # angled
            LineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.1),  # angled
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.3, startY=0.1, endX=0.5, endY=0.6, slope=0.81579),
            ExtendedLineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.1, slope=-0.81579)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_vertical_line_tjunction_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are close to each other and form a T junction and case 4 condition is met
        '''
        # Arrange
        # Mock input data
        # horizontal and vertical line segments that are touching each other and form a T junction
        line_segments = [
            LineSegment(startX=0.1, startY=0.3, endX=0.3, endY=0.3),  # horizontal
            LineSegment(startX=0.31, startY=0.1, endX=0.31, endY=0.5)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.3, endX=0.31, endY=0.3, slope=0.0),
            ExtendedLineSegment(startX=0.31, startY=0.09, endX=0.31, endY=0.51, slope=math.inf)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point(source_line_segment.startX, source_line_segment.startY),
            Point(source_line_segment.endX, source_line_segment.endY),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': True
            }
        }

        self.assertEqual(result, expected_result)

    def test_vertical_horizontal_line_tjunction_close(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are close to each other and form a T junction and case 3 condition is met
        '''
        # Arrange
        # Mock input data for a horizontal and vertical line segments that are touching each other and form a T junction
        line_segments = [
            LineSegment(startX=0.1, startY=0.1, endX=0.1, endY=0.4),  # vertical
            LineSegment(startX=0.11, startY=0.2, endX=0.4, endY=0.2)  # horizontal
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.1, startY=0.09, endX=0.1, endY=0.41, slope=math.inf),
            ExtendedLineSegment(startX=0.1, startY=0.2, endX=0.41, endY=0.2, slope=0.0)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[1]
        extended_source_line_segment = extended_line_segments[1]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[0],
            extended_line_segments[0],
            "1",
            "0",
            line_polygon_extended,
            Point(source_line_segment.startX, source_line_segment.startY),
            Point(source_line_segment.endX, source_line_segment.endY),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.009999999999999995,
                'intersection': True
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)

    def test_horizontal_vertical_2_lines_4way_junction(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are intersecting each other and no Case condition is met because of 4 way junction
        '''
        # Arrange
        # Mock input data for horizontal and vertical line segments that are touching each other and form a 4 way junction
        line_segments = [
            LineSegment(startX=0.2, startY=0.5, endX=0.6, endY=0.5),  # horizontal
            LineSegment(startX=0.4, startY=0.3, endX=0.4, endY=0.7)  # vertical
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.19, startY=0.5, endX=0.61, endY=0.5, slope=0.0),
            ExtendedLineSegment(startX=0.4, startY=0.29, endX=0.4, endY=0.71, slope=math.inf)
        ]

        current_connection_candidates = {
            'start': {'node': None, 'type': GraphNodeType.unknown, 'distance': None, 'intersection': False},
            'end': {'node': None, 'type': GraphNodeType.unknown, 'distance': None, 'intersection': False}
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            Point(source_line_segment.startX, source_line_segment.startY),
            Point(source_line_segment.endX, source_line_segment.endY),
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        self.assertEqual(result, current_connection_candidates)

    def test_horizontal_vertical_3_lines_4way_junction_with_gap(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for a horizontal and vertical line
        that are intersecting each other and no Case condition is met because of 4 way junction with gap
        first case 4 condition is met and then case 2 condition is met
        '''
        # Arrange
        # Mock input data for horizontal and vertical line segments that are touching each other
        # and form a 4 way junction with gap
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.31, endY=0.2),  # horizontal
            LineSegment(startX=0.32, startY=0.1, endX=0.32, endY=0.4),  # vertical
            LineSegment(startX=0.32, startY=0.2, endX=0.5, endY=0.2)  # horizontal
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.32, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.32, startY=0.09, endX=0.32, endY=0.41, slope=math.inf),
            ExtendedLineSegment(startX=0.31, startY=0.2, endX=0.51, endY=0.2, slope=0.0)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }
        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': True
            }
        }

        self.assertEqual(result, expected_result)  # case 3 condition is met

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[2],
            extended_line_segments[2],
            "2",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "2",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)  # case 2 is met

    def test_horizontal_vertical_3_lines_4way_junction_with_nogap(self):
        '''
        Test case to verify polygon intersection condition and candidate matching for 2 horizontal and vertical lines
        that are intersecting each other and no Case condition is met because of 4 way junction with no gap
        and case 4 is first met and then case 2 is met
        '''
        # Arrange
        # Mock input data for 2 horizontal and 1 vertical line segments that are touching each other
        # and form a 4 way junction with horizontal lines having no gap
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.31, endY=0.2),  # horizontal
            LineSegment(startX=0.32, startY=0.1, endX=0.32, endY=0.4),  # vertical
            LineSegment(startX=0.31, startY=0.2, endX=0.5, endY=0.2)  # horizontal
        ]

        extended_line_segments = [
            ExtendedLineSegment(startX=0.09, startY=0.2, endX=0.32, endY=0.2, slope=0.0),
            ExtendedLineSegment(startX=0.32, startY=0.09, endX=0.32, endY=0.41, slope=math.inf),
            ExtendedLineSegment(startX=0.3, startY=0.2, endX=0.51, endY=0.2, slope=0.0)
        ]

        current_connection_candidates = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            }
        }

        source_line_segment = line_segments[0]
        extended_source_line_segment = extended_line_segments[0]

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        start_point = Point(source_line_segment.startX, source_line_segment.startY)
        end_point = Point(source_line_segment.endX, source_line_segment.endY)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[1],
            extended_line_segments[1],
            "1",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "1",
                'type': GraphNodeType.line,
                'distance': 0.010000000000000009,
                'intersection': True
            }
        }

        self.assertEqual(result, expected_result)  # check to see that horizontal and vertical lines are connected

        line_polygon_extended = shapely_utils.convert_line_to_line_string(extended_source_line_segment).buffer(0.001)

        # Act
        result = create_line_to_line_connection_candidates(
            line_segments[2],
            extended_line_segments[2],
            "2",
            "0",
            line_polygon_extended,
            start_point,
            end_point,
            current_connection_candidates,
            self.line_distance_threshold,
            self.graph_line_buffer
        )

        # Assert
        expected_result = {
            'start':
            {
                'node': None,
                'type': GraphNodeType.unknown,
                'distance': None,
                'intersection': False
            },
            'end':
            {
                'node': "2",
                'type': GraphNodeType.line,
                'distance': 0.0,
                'intersection': False
            }
        }

        self.assertEqual(result, expected_result)  # check to see that horizontal lines are connected
