# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel


class LineSegment(BaseModel):
    """
    This class represents the line segment detected on a P&ID image.
    """
    startX: float
    startY: float
    endX: float
    endY: float
