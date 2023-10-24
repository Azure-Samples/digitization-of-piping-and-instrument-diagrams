from typing import Optional
from app.models.enums.graph_node_type import GraphNodeType
from pydantic import BaseModel


class ConnectionCandidate(BaseModel):
    node: str = None
    type: GraphNodeType = GraphNodeType.unknown
    distance: Optional[float] = None
    intersection: bool = False
