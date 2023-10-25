from app.models.bounding_box import BoundingBox
from typing import Optional


class Label(BoundingBox):
    """
    This class represents a tagged label of a symbol detected on a P&ID image.
    """
    id: int
    label: str
    score: Optional[float]
