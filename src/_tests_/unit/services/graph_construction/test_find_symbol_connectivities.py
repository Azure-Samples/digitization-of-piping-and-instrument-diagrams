import os
import unittest
from unittest.mock import MagicMock
import networkx as nx
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.models.enums.graph_node_type import GraphNodeType
from app.services.graph_construction.graph_service import GraphService
from app.services.graph_construction.find_symbol_connectivities import find_symbol_connectivities
from app.models.graph_construction.pre_find_symbol_connectivities_response import PreFindSymbolConnectivitiesResponse
from app.models.graph_construction.traversal_connection import TraversalConnection
from app.models.graph_construction.traversal_connection import TraversalConnection
from app.models.enums.flow_direction import FlowDirection
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig


class TestFindSymbolConnectivitiesUnit(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        def get_connected_nodes_mock(
            starting_node: str,
            asset_symbol_ids: set[str],
            exhaust_paths: bool = False,
            propagation_pass: bool = False,
            junction_arrow_ids = None,
            arrow_symbol_label = None
        ):
            if propagation_pass:
                if starting_node == 'a-1':
                    return [
                        TraversalConnection(
                            node_id='a-1',
                            flow_direction=FlowDirection.downstream,
                            visited_ids=['vs-1'],
                        )
                    ]
                else:
                    return []

            if starting_node == 'as-1':
                return [
                    TraversalConnection(
                        node_id='as-2',
                        flow_direction=FlowDirection.downstream,
                        visited_ids=['l-1', 'a-1', 'l-2'],
                    ),
                    TraversalConnection(
                        node_id='vs-1',
                        flow_direction=FlowDirection.downstream,
                        visited_ids=['l-1', 'a-1', 'l-3'],
                    )
                ]
            elif starting_node == 'as-2':
                return [
                    TraversalConnection(
                        node_id='vs-1',
                        flow_direction=FlowDirection.unknown,
                        visited_ids=['l-1', 'a-1', 'l-3'],
                    )
                ]
            elif starting_node == 'vs-1':
                return [
                    TraversalConnection(
                        node_id='as-2',
                        flow_direction=FlowDirection.unknown,
                        visited_ids=['l-3', 'a-1', 'l-1'],
                    )
                ]

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'as-1', 'as-2', 'vs-1'},
            asset_valve_symbol_ids={'vs-1', 'vs-2'},
            flow_direction_asset_ids={'as-1', 'as-2'},
        )

        graph_service_mock = MagicMock()
        graph_service_mock.get_arrow_symbols_at_T_junction.return_value = ['a-1']
        graph_service_mock.get_connected_nodes.side_effect = get_connected_nodes_mock

        # act
        result = find_symbol_connectivities(
            pre_find_symbol_connectivities=pre_find_symbol_connectivities,
            graph_service=graph_service_mock
        )

        for k, v in result.items():
            v.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'as-1': [
                TraversalConnection(
                    node_id='as-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['l-1', 'a-1', 'l-2'],
                ),
                TraversalConnection(
                    node_id='vs-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['l-1', 'a-1', 'l-3'],
                )
            ],
            'as-2': [
                TraversalConnection(
                    node_id='vs-1',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['l-1', 'a-1', 'l-3'],
                )
            ],
            'vs-1': [
                TraversalConnection(
                    node_id='as-2',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['l-3', 'a-1', 'l-1'],
                )
            ]
        }


class TestFindSymbolConnectivitiesComponent(unittest.TestCase):
    # region Ttests that have the same response between the exhaustive and non-exhaustive search.
    def test_when_multiple_T_intersection_with_directed_line_and_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-5'}})
        G.add_node('arrow-3', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-3'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'arrow-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'arrow-3')
        G.add_edge('arrow-3', 'symbol-2')
        G.add_edge('arrow-1', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('arrow-2', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            True,
            arrow_symbol_label)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-2', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ]
        }

    def test_when_multiple_T_intersection_with_directed_line_and_no_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-5'}})
        G.add_node('arrow-3', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-3'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'arrow-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'arrow-3')
        G.add_edge('arrow-3', 'symbol-2')
        G.add_edge('arrow-1', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('arrow-2', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            False,
            arrow_symbol_label)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-2', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-3', 'arrow-3'],
                )
            ]
        }

    def test_when_multiple_T_intersection_with_undirected_line_and_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-5'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'arrow-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')
        G.add_edge('arrow-1', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('arrow-2', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            True,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'arrow-2', 'line-3'],
                )
            ],
            'symbol-2': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-3', 'arrow-2', 'line-2', 'arrow-1', 'line-1'],
                )
            ],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-2', 'arrow-2', 'line-3'],
                ),
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-2', 'arrow-1', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-3'],
                ),
            ]
        }

    def test_when_multiple_T_intersection_with_undirected_line_and_no_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-5'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'arrow-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')
        G.add_edge('arrow-1', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('arrow-2', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            False,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'arrow-2', 'line-3'],
                )
            ],
            'symbol-2': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-3', 'arrow-2', 'line-2', 'arrow-1', 'line-1'],
                )
            ],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-1', 'line-2', 'arrow-2', 'line-3'],
                ),
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-2', 'arrow-1', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'arrow-2', 'line-3'],
                ),
            ]
        }

    def test_when_downstream_sensor_non_asset_and_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-1'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'symbol-2')
        G.add_edge('line-1', 'line-2')
        G.add_edge('line-2', 'symbol-3')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            True,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1'],
                ),
                TraversalConnection(
                    node_id='symbol-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'line-2'],
                )
            ],
            'symbol-2': [
            ],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-2', 'line-1', 'arrow-1'],
                )
            ]
        }

    def test_when_downstream_sensor_non_asset_and_no_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-1'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'symbol-2')
        G.add_edge('line-1', 'line-2')
        G.add_edge('line-2', 'symbol-3')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            False,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1'],
                ),
                TraversalConnection(
                    node_id='symbol-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'line-2'],
                )
            ],
            'symbol-2': [
            ],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-2', 'line-1', 'arrow-1'],
                )
            ]
        }

    def test_when_unknown_T_intersection_arrow_with_known_direction_and_exhaustive_search_returns_correct_connected_symbols(self):
        # This is a known bug when the arrow is pointing in the wrong direction and there is a branch.
        # The symbol from the branch can traverse upstream.

        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-2'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('arrow-3', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})  # will end up without any sources since it will be marked as untraceable
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'arrow-1')
        G.add_edge('arrow-1', 'symbol-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'arrow-3')
        G.add_edge('arrow-3', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('line-1', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            True,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-2', 'line-2', 'arrow-1'],
                ),
                TraversalConnection(
                    node_id='symbol-4',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-1', 'line-5'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-3', 'line-3', 'arrow-2', 'line-2', 'arrow-1'],
                )
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-5', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'line-1', 'arrow-2', 'line-2', 'arrow-1'],
                )
            ]
        }

    def test_when_unknown_T_intersection_arrow_with_known_direction_and_no_exhaustive_search_returns_correct_connected_symbols(self):
        # This is a known bug when the arrow is pointing in the wrong direction and there is a branch.
        # The symbol from the branch can traverse upstream.

        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-2'}})
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('arrow-3', type=GraphNodeType.symbol, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-4'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})  # will end up without any sources since it will be marked as untraceable
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'arrow-1')
        G.add_edge('arrow-1', 'symbol-2')
        G.add_edge('arrow-2', 'line-3')
        G.add_edge('line-3', 'arrow-3')
        G.add_edge('arrow-3', 'line-4')
        G.add_edge('line-4', 'symbol-3')
        G.add_edge('line-1', 'line-5')
        G.add_edge('line-5', 'symbol-4')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'symbol-4'},
            asset_valve_symbol_ids=set(),
            flow_direction_asset_ids={'symbol-1', 'symbol-2', 'symbol-3'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            False,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-2', 'line-2', 'arrow-1'],
                ),
                TraversalConnection(
                    node_id='symbol-4',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-1', 'line-5'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-4', 'arrow-3', 'line-3', 'arrow-2', 'line-2', 'arrow-1'],
                )
            ],
            'symbol-4': [
                TraversalConnection(
                    node_id='symbol-1',
                    flow_direction=FlowDirection.unknown,
                    visited_ids=['line-5', 'line-1'],
                ),
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-5', 'line-1', 'arrow-2', 'line-2', 'arrow-1'],
                )
            ]
        }

    # endregion

    # region The two tests below have different results with exhaustive search and no exhaustive search.
    # This is due to the cycle in the graph.
    def test_when_cycle_and_exhaustive_search_returns_correct_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('valve-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.line, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-1'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-6', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-7', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'valve-1')
        G.add_edge('valve-1', 'line-3')
        G.add_edge('line-3', 'symbol-2')
        G.add_edge('line-2', 'line-4')
        G.add_edge('line-4', 'line-5')
        G.add_edge('line-5', 'line-6')
        G.add_edge('line-6', 'line-3')
        G.add_edge('line-5', 'line-7')
        G.add_edge('line-7', 'symbol-3')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'valve-1'},
            asset_valve_symbol_ids={'valve-1'},
            flow_direction_asset_ids={'symbol-1', 'symbol-2'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            True,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'line-4', 'line-5', 'line-6', 'line-3'],
                ),
                TraversalConnection(
                    node_id='symbol-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'line-4', 'line-5', 'line-7'],
                ),
                TraversalConnection(
                    node_id='valve-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-7', 'line-5', 'line-6', 'line-3'],
                )
            ],
            'valve-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-3'],
                )
            ]
        }

    def test_when_cycle_and_no_exhaustive_search_returns_incorrect_connected_symbols(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('valve-1', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_node('arrow-1', type=GraphNodeType.line, label=arrow_symbol_label, **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-1'}})

        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-4', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-5', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-6', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-7', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'valve-1')
        G.add_edge('valve-1', 'line-3')
        G.add_edge('line-3', 'symbol-2')
        G.add_edge('line-2', 'line-4')
        G.add_edge('line-4', 'line-5')
        G.add_edge('line-5', 'line-6')
        G.add_edge('line-6', 'line-3')
        G.add_edge('line-5', 'line-7')
        G.add_edge('line-7', 'symbol-3')

        graph_service = GraphService(G)

        pre_find_symbol_connectivities = PreFindSymbolConnectivitiesResponse(
            asset_symbol_ids={'symbol-1', 'symbol-2', 'symbol-3', 'valve-1'},
            asset_valve_symbol_ids={'valve-1'},
            flow_direction_asset_ids={'symbol-1', 'symbol-2'},
        )

        # act
        result = find_symbol_connectivities(
            graph_service,
            pre_find_symbol_connectivities,
            False,
            arrow_symbol_label)

        # sort the result
        for _, value in result.items():
            value.sort(key=lambda x: x.node_id)

        # assert
        assert result == {
            'symbol-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'line-4', 'line-5', 'line-6', 'line-3'],
                ),
                TraversalConnection(
                    node_id='symbol-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2', 'line-4', 'line-5', 'line-7'],
                ),
                TraversalConnection(
                    node_id='valve-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-1', 'arrow-1', 'line-2'],
                )
            ],
            'symbol-2': [],
            'symbol-3': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-7', 'line-5', 'line-6', 'line-3'],
                ),
                TraversalConnection(  # incorrect result
                    node_id='valve-1',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-7', 'line-5', 'line-4', 'line-2'],
                )
            ],
            'valve-1': [
                TraversalConnection(
                    node_id='symbol-2',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-3'],
                ),
                TraversalConnection(  # incorrect result
                    node_id='symbol-3',
                    flow_direction=FlowDirection.downstream,
                    visited_ids=['line-3', 'line-6', 'line-5', 'line-7'],
                )
            ]
        }

    # endregion
