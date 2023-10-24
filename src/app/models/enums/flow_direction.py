from enum import Enum


class FlowDirection(str, Enum):
    '''Enum for the flow direction'''
    unknown = "unknown"
    upstream = "upstream"
    downstream = "downstream"
