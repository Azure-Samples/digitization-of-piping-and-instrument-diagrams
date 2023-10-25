from enum import Enum


class InferenceResult(str, Enum):
    '''Enum for the inference result type'''
    symbol_detection = "symbol-detection"
    text_detection = "text-detection"
    graph_construction = "graph-construction"
    line_detection = "line-detection"
    graph_persistence = "graph-persistence"
