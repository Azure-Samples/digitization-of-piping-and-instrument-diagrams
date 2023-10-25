from typing import Optional
from ..text_detection.text_detection_inference_response import TextDetectionInferenceResponse
from ..bounding_box import BoundingBox


class GraphConstructionInferenceRequest(TextDetectionInferenceResponse):
    """
    This class represents the parameters used in the Hough Transform algorithm.
    """
    hough_threshold: Optional[int]
    hough_min_line_length: Optional[int]
    hough_max_line_gap: Optional[int]
    hough_rho: Optional[float]
    hough_theta: Optional[int]
    thinning_enabled: Optional[bool]
    bounding_box_inclusive: Optional[BoundingBox]
    propagation_pass_exhaustive_search: bool = False
