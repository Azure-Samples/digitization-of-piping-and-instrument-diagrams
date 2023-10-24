from app.models.image_details import ImageDetails
from app.models.bounding_box import BoundingBox
from .text_recognized import TextRecognized
from .symbol_and_text_associated import SymbolAndTextAssociated
from pydantic import BaseModel
from typing import Optional


class TextDetectionInferenceResponse(BaseModel):
    """
    This class represents the text detection inference results; which includes
    all text detected, and the text and symbols associated on a P&ID image.
    """
    image_url: str
    image_details: ImageDetails
    bounding_box_inclusive: Optional[BoundingBox]
    all_text_list: list[TextRecognized]
    text_and_symbols_associated_list: list[SymbolAndTextAssociated]
