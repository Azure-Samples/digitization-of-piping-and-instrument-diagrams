from app.config import config
from app.services.graph_construction.graph_service import GraphService
from app.models.graph_construction.pre_find_symbol_connectivities_response import PreFindSymbolConnectivitiesResponse
from app.models.graph_construction.traversal_connection import TraversalConnection
import logger_config
import time

logger = logger_config.get_logger(__name__)


def find_symbol_connectivities(
    graph_service: GraphService,
    pre_find_symbol_connectivities: PreFindSymbolConnectivitiesResponse,
    propagation_should_use_exhaustive_search: bool = False,
    arrow_symbol_label: str = config.arrow_symbol_label,
):
    '''This function finds all symbols that are connected to each other, and returns a graph
    that represents the connections between symbols.

    :param graph_service: The graph service to use to find connected symbols
    :type graph_service: GraphService
    :param pre_find_symbol_connectivities: The pre find symbol connectivities response
    :type pre_find_symbol_connectivities: PreFindSymbolConnectivitiesResponse
    :param propagation_should_use_exhaustive_search: Whether or not the propagation should use exhaustive search
    :type propagation_should_use_exhaustive_search: bool
    :param arrow_symbol_label: The arrow symbol label
    :type arrow_symbol_label: str
    :return: The connected symbols
    :rtype: dict[str, list[TraversalConnection]]]'''

    logger.debug('Beginning propagation...')
    tic = time.perf_counter()

    # case 1:
    # Find the 3 way intersection arrows that have atleast 3 lines connected to it
    # if the arrows have a degree greater than 2, ensure that the count of the lines the arrow
    # is connected to is greater than 2
    logger.debug('Finding the junction arrows...')
    arrow_ids_with_degree_greater_than_two = set(graph_service.get_arrow_symbols_at_T_junction(
        arrow_symbol_label
    ))

    # traverse then propagate
    # Stop at equipments, pagination (flow direction assets) or sensors (which indicates you are not on process flow anymore)
    non_valve_assets = pre_find_symbol_connectivities.asset_symbol_ids.difference(
        pre_find_symbol_connectivities.asset_valve_symbol_ids)

    # now we propogate for all the connections between the equipments/connectors
    logger.debug('Getting connections for each equipment/connectors...')
    traversal_connections_map: dict[str, list[TraversalConnection]] = {}
    for symbol_node_id in pre_find_symbol_connectivities.flow_direction_asset_ids:
        traversal_connections = graph_service.get_connected_nodes(
            symbol_node_id,
            non_valve_assets,
            propagation_should_use_exhaustive_search,
            True,
            arrow_ids_with_degree_greater_than_two,
            arrow_symbol_label)
        traversal_connections_map[symbol_node_id] = [elem for elem in traversal_connections if (
            elem.node_id in pre_find_symbol_connectivities.flow_direction_asset_ids or
            elem.node_id in arrow_ids_with_degree_greater_than_two
        )]

    temp_sources_key = 'temp_sources'
    logger.debug('Propagating the flow direction...')
    for key, value in traversal_connections_map.items():
        graph_service.propagate_flow_direction(key, value, temp_sources_key)

    graph_service.publish_sources(temp_sources_key)

    toc = time.perf_counter()
    logger.debug(f'Propagation finished {toc - tic:0.4f} seconds. Finding symbol connections...')

    tic = time.perf_counter()
    symbol_connections: dict[str, list[TraversalConnection]] = {}
    for asset_symbol_id in pre_find_symbol_connectivities.asset_symbol_ids:
        connected_nodes = graph_service.get_connected_nodes(
            starting_node=asset_symbol_id,
            asset_symbol_ids=pre_find_symbol_connectivities.asset_symbol_ids,
            arrow_symbol_label=arrow_symbol_label)
        symbol_connections[asset_symbol_id] = connected_nodes
    toc = time.perf_counter()
    logger.debug(f'Found symbol connections in {toc - tic:0.4f} seconds. Building output...')

    return symbol_connections
