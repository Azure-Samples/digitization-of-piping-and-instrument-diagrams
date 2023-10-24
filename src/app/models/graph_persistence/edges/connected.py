from typing import Optional
from app.models.graph_persistence.edges.base_edge import BaseEdge
from app.models.bounding_box import BoundingBox


class Connected(BaseEdge):
    '''This class represents the traversal path between asset nodes in the graph.'''
    segments: Optional[list[BoundingBox]] = None
