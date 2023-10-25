from pydantic import BaseModel


class BaseEdge(BaseModel):
    '''This class represents the base edge defining relationship in graph database.'''
    from_id: str
    to_id: str
