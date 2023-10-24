from pydantic import BaseModel


class ImageDetails(BaseModel):
    """
    This class represents the details of a P&ID image.
    """
    format: str = 'png'
    width: int
    height: int
