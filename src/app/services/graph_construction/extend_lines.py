# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.line_detection.line_segment import LineSegment
import math

from app.models.graph_construction.extended_line_segment \
                                                import ExtendedLineSegment


def get_slope_between_points(x1, y1, x2, y2):
    '''
    Returns the slope between two points.
    '''
    x_delta = x2 - x1
    if x_delta == 0:
        return math.inf
    return (y2 - y1) / x_delta


def extend_lines(
        line_segments: list[LineSegment],
        line_segment_padding_default: float,
        ) -> list[ExtendedLineSegment]:
    """
    Extend lines to the edges of the image
    :param line_segments: list of line segments
    :param image_details: image details
    :return: list of extended line segments
    """
    padding = line_segment_padding_default
    extended_line_segments = []

    for line in line_segments:
        slope = get_slope_between_points(line.startX, line.startY,
                                         line.endX, line.endY)

        b = 0
        # If the slope is not infinite (i.e., the line is not vertical)
        if slope != math.inf:
            # Calculate the y-intercept (b) using the formula y = mx + b
            b = line.startY - slope * line.startX

        if slope == math.inf:
            # Vertical line case: Only adjust the top and bottom y-coordinates
            start_x = line.startX
            start_y = max(line.startY - padding, 0)
            end_x = line.endX
            end_y = min(line.endY + padding, 1)
        else:
            # Non-vertical line case: Adjust both the top
            # and bottom x-coordinates
            # Calculate the adjusted y-coordinate
            # using the slope-intercept form
            start_x = max(line.startX - padding, 0)
            start_y = slope * start_x + b
            end_x = min(line.endX + padding, 1)
            end_y = slope * end_x + b

        # Create a new ExtendedLineSegment object with
        # the adjusted coordinates and slope
        extended_line_segments.append(
            ExtendedLineSegment(
                startX=round(start_x, 5),
                startY=round(start_y, 5),
                endX=round(end_x, 5),
                endY=round(end_y, 5),
                slope=round(slope, 5)
            )
        )

    return extended_line_segments
