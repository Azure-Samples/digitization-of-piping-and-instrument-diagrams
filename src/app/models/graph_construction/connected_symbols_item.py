# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.graph_construction.base_connected_symbols_item import BaseConnectedSymbolsItem
from app.models.graph_construction.connected_symbols_connection_item import ConnectedSymbolsConnectionItem


class ConnectedSymbolsItem(BaseConnectedSymbolsItem):
    '''This class represents a symbol that is connected to other symbols'''
    connections: list[ConnectedSymbolsConnectionItem]
