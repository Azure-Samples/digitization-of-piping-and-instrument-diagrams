# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from enum import Enum


class GraphNodeType(int, Enum):
    '''Enum for the graph node types'''
    unknown = 0
    line = 1
    symbol = 2
    text = 3  # Not used for creating the graph, just as a intermediate for candidate matching
