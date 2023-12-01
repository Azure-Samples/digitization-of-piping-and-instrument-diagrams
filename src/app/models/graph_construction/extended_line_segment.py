# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.line_detection.line_segment import LineSegment


class ExtendedLineSegment(LineSegment):
    """
    This class represents the line segment extension
    """
    slope: float
