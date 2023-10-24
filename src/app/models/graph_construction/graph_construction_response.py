from pydantic import BaseModel
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.image_details import ImageDetails


class GraphConstructionInferenceResponse(BaseModel):
    '''This class represents the container of connected symbols'''
    image_url: str
    image_details: ImageDetails
    connected_symbols: list[ConnectedSymbolsItem]
