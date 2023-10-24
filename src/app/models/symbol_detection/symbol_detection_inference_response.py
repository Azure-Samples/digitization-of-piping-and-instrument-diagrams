from typing import Optional
from app.models.image_details import ImageDetails
from app.models.symbol_detection.label import Label
from pydantic import BaseModel

from app.models.bounding_box import BoundingBox


class SymbolDetectionInferenceResponse(BaseModel):
    """
    This class represents the symbol detection inference results; which includes
    all symbols detected, and the symbols and text associated on a P&ID image.
    """
    image_url: str
    image_details: ImageDetails
    bounding_box_inclusive: Optional[BoundingBox]
    label: list[Label]
