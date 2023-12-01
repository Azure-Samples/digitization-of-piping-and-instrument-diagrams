# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from enum import Enum


class ArrowDirection(str, Enum):
    '''Enum for the flow direction'''
    unknown = "unknown"
    up = "up"
    left = "left"
    down = "down"
    right = "right"
