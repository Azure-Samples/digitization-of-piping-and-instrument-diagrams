from app.config import config
from app.models.graph_construction.pre_find_symbol_connectivities_response import PreFindSymbolConnectivitiesResponse
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.services.graph_construction.graph_service import GraphService
from app.utils.regex_utils import (
     does_string_contain_at_least_one_number_and_one_letter,
     is_symbol_text_invalid)


def pre_find_symbol_connectivities(
    graph_service: GraphService,
    arrow_symbol_label: str = config.arrow_symbol_label,
    flow_direction_asset_prefixes: set[str] = config.flow_direction_asset_prefixes,
    valve_symbol_prefix: str = config.valve_symbol_prefix,
    symbol_label_prefixes_with_text: set[str] = config.symbol_label_prefixes_with_text
):
    '''This function generates the necessary data for the find symbol connectivities function.

    :param symbol_nodes: The symbol nodes
    :type symbol_nodes: list
    :param flow_direction_asset_prefixes_lowered_tuple: The flow direction asset prefixes
    :type flow_direction_asset_prefixes_lowered_tuple: tuple
    :param valve_symbol_prefix: The valve symbol prefix
    :type valve_symbol_prefix: str
    :param symbol_label_prefixes_with_text: The symbol label prefixes with text
    :type symbol_label_prefixes_with_text: set
    :return: The pre find symbol connectivities response
    :rtype: PreFindSymbolConnectivitiesResponse
    '''
    symbol_label_prefixes_with_text_lowered_tuple = \
        tuple([prefix.lower() for prefix in symbol_label_prefixes_with_text])

    flow_direction_asset_prefixes_lowered_tuple = \
        tuple([prefix.lower() for prefix in flow_direction_asset_prefixes])
    symbol_nodes = graph_service.get_symbol_nodes()

    asset_symbol_ids: set[str] = set()
    asset_valve_symbol_ids: set[str] = set()  # needed to take the difference between the asset symbols and valve symbols
    flow_direction_asset_ids: set[str] = set()
    for symbol_node_id, symbol_node in symbol_nodes:
        symbol_label: str = symbol_node[SymbolNodeKeysConfig.LABEL_KEY]
        if symbol_label == arrow_symbol_label or \
            SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY not in symbol_node or \
                symbol_node[SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY] is None:
            continue

        # get all the flow direction asset symbols
        if symbol_label.lower().startswith(flow_direction_asset_prefixes_lowered_tuple):
            flow_direction_asset_ids.add(symbol_node_id)

        # get all the asset symbols - valid alpha-numeric sensors, valves, equipments and pagination
        symbol_text = symbol_node[SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY]
        if does_string_contain_at_least_one_number_and_one_letter(symbol_text) and \
                is_symbol_text_invalid(symbol_text) is False and \
                symbol_label.lower().startswith(symbol_label_prefixes_with_text_lowered_tuple):
            asset_symbol_ids.add(symbol_node_id)

            # get all the valve symbols
            if symbol_label.lower().startswith(valve_symbol_prefix.lower()):
                asset_valve_symbol_ids.add(symbol_node_id)

    response = PreFindSymbolConnectivitiesResponse(
        asset_symbol_ids=asset_symbol_ids,
        asset_valve_symbol_ids=asset_valve_symbol_ids,
        flow_direction_asset_ids=flow_direction_asset_ids
    )
    return response
