from pydantic import BaseModel


class BaseNode(BaseModel):
    '''This class represents the base node in the graph database.'''
    id: str
    attributes: dict = None
