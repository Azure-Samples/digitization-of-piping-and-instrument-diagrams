from pydantic import BaseModel
from app.models.enums.flow_direction import FlowDirection


class TraversalConnection(BaseModel):
    '''This class represents a connection in the graph when traversing.'''
    node_id: str = str()
    flow_direction: FlowDirection = FlowDirection.unknown
    visited_ids: list[str] = []
