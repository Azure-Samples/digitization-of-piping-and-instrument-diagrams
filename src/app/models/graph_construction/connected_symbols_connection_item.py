# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.enums.flow_direction import FlowDirection
from app.models.bounding_box import BoundingBox
from app.models.graph_construction.base_connected_symbols_item import BaseConnectedSymbolsItem


class ConnectedSymbolsConnectionItem(BaseConnectedSymbolsItem):
    '''This class represents a symbol that is connected to other symbols'''
    flow_direction: FlowDirection
    segments: list[BoundingBox]
