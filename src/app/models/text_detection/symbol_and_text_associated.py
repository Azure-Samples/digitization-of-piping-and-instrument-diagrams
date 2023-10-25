from app.models.symbol_detection.label import Label
from typing import Optional


class SymbolAndTextAssociated(Label):
    """
    Class that represents the symbol detected properties and the text associated within the symbol
    """
    text_associated: Optional[str]
