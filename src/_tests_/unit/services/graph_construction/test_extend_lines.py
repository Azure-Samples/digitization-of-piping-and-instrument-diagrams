# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import math
import os
import sys
from unittest.mock import MagicMock, patch
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.graph_construction.extended_line_segment \
    import ExtendedLineSegment
from app.models.line_detection.line_segment import LineSegment
from app.services.graph_construction.extend_lines import extend_lines


input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')


class TestExtendLines(unittest.TestCase):

    line_segment_padding_default = 0.01

    def test_extend_lines_with_vertical_line(self):

        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.1, endY=0.5),
            LineSegment(startX=0.3, startY=0.4, endX=0.3, endY=0.7),
        ]
        expected_result = [
            ExtendedLineSegment(startX=0.1, startY=0.19, endX=0.1, endY=0.51,
                                slope=math.inf),
            ExtendedLineSegment(startX=0.3, startY=0.39, endX=0.3, endY=0.71,
                                slope=math.inf),
        ]

        result = extend_lines(line_segments, self.line_segment_padding_default)

        self.assertEqual(result, expected_result)

    def test_extend_lines_with_non_vertical_line(self):

        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.4),
            LineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.8),
        ]
        expected_result = [
            ExtendedLineSegment(startX=0.09, startY=0.19,
                                endX=0.31, endY=0.41,
                                slope=1.0),
            ExtendedLineSegment(startX=0.49, startY=0.59, endX=0.71, endY=0.81,
                                slope=1.0),
        ]

        result = extend_lines(line_segments, self.line_segment_padding_default)

        self.assertEqual(result, expected_result)

    def test_extend_lines_with_padding_zero(self):

        line_segment_padding = 0.0
        line_segments = [
            LineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.4),
            LineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.8),
        ]

        expected_result = [
            ExtendedLineSegment(startX=0.1, startY=0.2, endX=0.3, endY=0.4,
                                slope=1.0),
            ExtendedLineSegment(startX=0.5, startY=0.6, endX=0.7, endY=0.8,
                                slope=1.0),
        ]

        result = extend_lines(line_segments, line_segment_padding)

        self.assertEqual(result, expected_result)
