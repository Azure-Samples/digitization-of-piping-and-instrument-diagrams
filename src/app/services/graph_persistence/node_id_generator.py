# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.graph_persistence.nodes.pnid import PnId
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_persistence.nodes.sheet import Sheet


def get_asset_node_id(pnid: PnId, sheet: Sheet, asset: ConnectedSymbolsItem):
    return f'{pnid.id}/{sheet.id}/{asset.id}'


def get_connector_node_id(pnid: PnId, sheet: Sheet, asset: ConnectedSymbolsItem):
    return get_asset_node_id(pnid, sheet, asset)
