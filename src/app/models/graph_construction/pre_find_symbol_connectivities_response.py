# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel


class PreFindSymbolConnectivitiesResponse(BaseModel):
    '''This class represents the response from the pre find symbol connectivities function.'''
    asset_symbol_ids: set[str]
    asset_valve_symbol_ids: set[str]
    flow_direction_asset_ids: set[str]
