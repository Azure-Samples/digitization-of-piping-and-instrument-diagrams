# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel
from app.models.line_detection.line_segment import LineSegment
from app.models.image_details import ImageDetails


class LineDetectionInferenceResponse(BaseModel):
    """
    This class represents the response of the line detection service.
    """
    image_url: str
    image_details: ImageDetails
    line_segments_count: int
    line_segments: list[LineSegment]
