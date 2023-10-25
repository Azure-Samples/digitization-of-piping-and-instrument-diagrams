from enum import Enum


class JobStep(str, Enum):
    '''Enum for the job step'''
    line_detection = "line_detection"
    graph_construction = "graph_construction"
    graph_persistence = "graph_persistence"
