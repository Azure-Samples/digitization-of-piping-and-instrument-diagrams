import os
import parameterized
import unittest
from unittest.mock import MagicMock, patch
import networkx as nx
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.graph_construction.graph_service import GraphService
from app.models.enums.graph_node_type import GraphNodeType
from app.models.enums.flow_direction import FlowDirection
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.models.graph_construction.traversal_connection import TraversalConnection


class TestAddNode(unittest.TestCase):
    @parameterized.parameterized.expand([
        (GraphNodeType.line, { 'test': 'test' }),
        (GraphNodeType.symbol, { 'test': 'test', 'label': 'label' })
    ])
    def test_happy_path_type_not_in_kwargs(self, node_type, kwargs):
        # arrange
        G = MagicMock()
        G.add_node.return_value = None
        graph_service = GraphService(G)

        # act
        graph_service.add_node('node-id', node_type, **kwargs)

        # assert
        G.add_node.assert_called_once_with('node-id', type=node_type, **kwargs, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})


    def test_happy_path_type_in_kwargs(self):
        # arrange
        G = MagicMock()
        G.add_node.return_value = None
        graph_service = GraphService(G)

        # act
        kwargs = { 'type': 'test' }
        graph_service.add_node('node-id', GraphNodeType.line, **kwargs)

        # assert
        G.add_node.assert_called_once_with('node-id', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

    def test_happy_path_when_symbol_without_label_raises_exception(self):
        # arrange
        G = MagicMock()
        G.add_node.return_value = None
        graph_service = GraphService(G)

        # act
        kwargs = { 'test': 'test' }
        with self.assertRaises(Exception) as e:
            graph_service.add_node('node-id', GraphNodeType.symbol, **kwargs)

        # assert
        G.add_node.assert_not_called()
        self.assertEqual(str(e.exception), 'Symbol nodes must have a label')


class TestAddEdge(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        G = MagicMock()
        G.add_edge.return_value = None
        graph_service = GraphService(G)

        # act
        kwargs = { 'test': 'test' }
        graph_service.add_edge('node-1', 'node-2', **kwargs)

        # assert
        G.add_edge.assert_called_once_with('node-1', 'node-2', test='test')


class TestGetNode(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        G = nx.Graph()
        G.add_node('node-1', type=GraphNodeType.line, test='test')
        graph_service = GraphService(G)

        # act
        node = graph_service.get_node('node-1')

        # assert
        assert node == { 'type': GraphNodeType.line, 'test': 'test' }


class TestGetDegree(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol)
        G.add_node('symbol-2', type=GraphNodeType.symbol)
        G.add_node('symbol-3', type=GraphNodeType.symbol)
        G.add_node('symbol-4', type=GraphNodeType.symbol)
        G.add_node('symbol-5', type=GraphNodeType.symbol)

        G.add_edge('symbol-2', 'symbol-3')
        G.add_edge('symbol-2', 'symbol-4')
        G.add_edge('symbol-2', 'symbol-5')

        G.add_edge('symbol-3', 'symbol-4')

        graph_service = GraphService(G)

        # act

        # assert
        assert graph_service.get_degree('symbol-1') == 0
        assert graph_service.get_degree('symbol-2') == 3
        assert graph_service.get_degree('symbol-3') == 2
        assert graph_service.get_degree('symbol-4') == 2
        assert graph_service.get_degree('symbol-5') == 1


class TestGetConnectedNodes(unittest.TestCase):
    def test_happy_path_no_cycles_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-3', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'line-2')
        G.add_edge('line-1', 'line-3')
        G.add_edge('line-2', 'symbol-2')
        G.add_edge('line-3', 'symbol-3')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes(
            'symbol-1',
            {'symbol-1', 'symbol-2', 'symbol-3'}
        )

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-1', 'line-2']),
            TraversalConnection(node_id='symbol-3', flow_direction=FlowDirection.unknown, visited_ids=['line-1', 'line-3']),
        ]

    def test_happy_path_with_cycles_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-3', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'line-2')
        G.add_edge('line-1', 'line-3')
        G.add_edge('line-2', 'symbol-2')
        G.add_edge('line-3', 'symbol-3')
        G.add_edge('symbol-3', 'symbol-1')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-1', {'symbol-1', 'symbol-2', 'symbol-3'})

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='symbol-3', flow_direction=FlowDirection.unknown, visited_ids=[]),
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-1', 'line-2']),
        ]

    def test_happy_path_with_non_terminal_symbol_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='non-terminal-1')
        G.add_node('symbol-3', type=GraphNodeType.symbol, label='non-terminal-2')
        G.add_node('symbol-4', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-5', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-1')
        G.add_edge('line-1', 'symbol-2')
        G.add_edge('symbol-2', 'line-2')
        G.add_edge('line-2', 'symbol-3')
        G.add_edge('symbol-3', 'line-3')
        G.add_edge('line-3', 'symbol-4')
        G.add_edge('symbol-4', 'symbol-5')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-1', {'symbol-1', 'symbol-4', 'symbol-5'})

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='symbol-4', flow_direction=FlowDirection.unknown, visited_ids=['line-1', 'symbol-2', 'line-2', 'symbol-3', 'line-3']),
        ]

    def test_happy_path_when_arrow_symbol_has_downstream_path_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-1', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.downstream, visited_ids=['line-0', 'line-1', 'arrow-1', 'line-2', 'line-3']),
        ]

    def test_happy_path_when_arrow_symbol_has_upstream_path_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'line-1')
        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-2', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == []

    def test_happy_path_when_arrow_symbol_has_conflicting_path_case1_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('arrow-2', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'arrow-1')
        G.add_edge('arrow-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-2', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == []

    def test_happy_path_when_arrow_symbol_has_conflicting_path_case2_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-0'}, label='arrow')
        G.add_node('arrow-2', type=GraphNodeType.symbol, sources={'line-2'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'arrow-1')
        G.add_edge('arrow-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-2', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == []

    def test_happy_path_when_downstream_double_arrow_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-0'}, label='arrow')
        G.add_node('arrow-2', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'arrow-1')
        G.add_edge('arrow-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-1', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.downstream, visited_ids=['line-0', 'arrow-1', 'line-1', 'arrow-2', 'line-2', 'line-3']),
        ]

    def test_happy_path_when_upstream_double_arrow_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-0'}, label='arrow')
        G.add_node('arrow-2', type=GraphNodeType.symbol, sources={'line-1'}, label='arrow')
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'arrow-1')
        G.add_edge('arrow-1', 'line-1')
        G.add_edge('line-1', 'arrow-2')
        G.add_edge('arrow-2', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'symbol-2')

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes('symbol-2', {'symbol-1', 'symbol-2'})

        # assert
        assert connected_objects == []

    def test_happy_path_when_T_intersection_and_propagation_pass_returns_valid_connected_nodes(self):
        # arrange
        G = nx.Graph()

        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-3', type=GraphNodeType.symbol, label='symbol')
        G.add_node('arrow-1', type=GraphNodeType.symbol, sources={'line-2'}, label='arrow')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'arrow-1')
        G.add_edge('arrow-1', 'line-1')
        G.add_edge('line-1', 'symbol-2')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('line-2', 'symbol-3')

        starting_node = 'symbol-3'
        asset_symbol_ids = {'symbol-1', 'symbol-2', 'symbol-3'}
        exhaust_paths = True
        propagation_pass = True
        junction_arrow_ids = {'arrow-1'}

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes(
            starting_node,
            asset_symbol_ids,
            exhaust_paths,
            propagation_pass,
            junction_arrow_ids,
            'arrow')

        # assert
        assert connected_objects == [
            TraversalConnection(node_id='arrow-1', flow_direction=FlowDirection.downstream, visited_ids=['line-2']),
        ]

    def test_happy_path_when_exhaust_paths_returns_duplicate_paths_in_different_traversals(self):
        # arrange
        G = nx.Graph()

        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'line-1')
        G.add_edge('symbol-1', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'line-1')
        G.add_edge('line-1', 'symbol-2')

        starting_node = 'symbol-1'
        asset_symbol_ids = {'symbol-1', 'symbol-2'}
        exhaust_paths = True
        propagation_pass = False
        junction_arrow_ids = set()

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes(
            starting_node,
            asset_symbol_ids,
            exhaust_paths,
            propagation_pass,
            junction_arrow_ids,
            'arrow')

        sorted_connected_objects = sorted(connected_objects, key=lambda x: len(x.visited_ids))

        # assert
        assert sorted_connected_objects == [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-0', 'line-1']),
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-2', 'line-3', 'line-1']),
        ]

    def test_happy_path_when_not_exhaust_paths_returns_single_path(self):
        # arrange
        G = nx.Graph()

        G.add_node('line-0', type=GraphNodeType.line)
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol')
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol')

        G.add_edge('symbol-1', 'line-0')
        G.add_edge('line-0', 'line-1')
        G.add_edge('symbol-1', 'line-2')
        G.add_edge('line-2', 'line-3')
        G.add_edge('line-3', 'line-1')
        G.add_edge('line-1', 'symbol-2')

        starting_node = 'symbol-1'
        asset_symbol_ids = {'symbol-1', 'symbol-2'}
        exhaust_paths = False
        propagation_pass = False
        junction_arrow_ids = set()

        graph_service = GraphService(G)

        # act
        connected_objects = graph_service.get_connected_nodes(
            starting_node,
            asset_symbol_ids,
            exhaust_paths,
            propagation_pass,
            junction_arrow_ids,
            'arrow')

        sorted_connected_objects = sorted(connected_objects, key=lambda x: len(x.visited_ids))

        # assert
        assert sorted_connected_objects == [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-0', 'line-1']),
        ]


class TestPropagateFlowDirection(unittest.TestCase):
    def test_happy_path_downstream(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('arrow-1', type=GraphNodeType.symbol, label='arrow', **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-0'}})
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol', **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol', **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        symbol_node_id = 'symbol-1'
        traversal_connections = [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.downstream, visited_ids=['line-0', 'arrow-1', 'line-1', 'line-2', 'line-3']),
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.downstream, visited_ids=['arrow-1']),
        ]

        graph_service = GraphService(G)
        key = 'temp_key'

        # act
        graph_service.propagate_flow_direction(symbol_node_id, traversal_connections, key)

        # assert
        assert G.nodes['line-0'][key] == {'symbol-1'}
        assert sorted(G.nodes['arrow-1'][key]) == ['line-0', 'symbol-1']
        assert G.nodes['line-1'][key] == {'arrow-1'}
        assert G.nodes['line-2'][key] == {'line-1'}
        assert G.nodes['line-3'][key] == {'line-2'}
        assert sorted(G.nodes['symbol-2'][key]) == ['arrow-1', 'line-3']

    def test_happy_path_unknown(self):
        # arrange
        G = nx.Graph()
        G.add_node('line-0', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-1', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-2', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('line-3', type=GraphNodeType.line, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('arrow-1', type=GraphNodeType.symbol, label='arrow', **{SymbolNodeKeysConfig.SOURCES_KEY: {'line-0'}})
        G.add_node('symbol-1', type=GraphNodeType.symbol, label='symbol', **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, label='symbol', **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        symbol_node_id = 'symbol-1'
        traversal_connections = [
            TraversalConnection(node_id='symbol-2', flow_direction=FlowDirection.unknown, visited_ids=['line-0', 'arrow-1', 'line-1', 'line-2', 'line-3']),
        ]

        graph_service = GraphService(G)
        key = 'temp_key'

        # act
        graph_service.propagate_flow_direction(symbol_node_id, traversal_connections, key)

        # assert
        assert G.nodes['line-0'][key] == set()
        assert G.nodes['arrow-1'][key] == {'line-0'}
        assert G.nodes['line-1'][key] == set()
        assert G.nodes['line-2'][key] == set()
        assert G.nodes['line-3'][key] == set()
        assert G.nodes['symbol-2'][key] == set()


class TestGetSymbolNodes(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        G = nx.Graph()

        asset_symbol_1 = {
            'type': GraphNodeType.symbol,
            'label': 'asset-1'
        }
        asset_symbol_2 = {
            'type': GraphNodeType.symbol,
            'label': 'asset-2'
        }
        asset_symbol_3 = {
            'type': GraphNodeType.symbol,
            'label': 'asset-3'
        }

        non_asset_symbol_1 = {
            'type': GraphNodeType.symbol,
            'label': 'non-asset-1'
        }
        non_asset_symbol_2 = {
            'type': GraphNodeType.symbol,
            'label': 'non-asset-2'
        }

        G.add_node('symbol-1', **asset_symbol_1)
        G.add_node('symbol-2', **non_asset_symbol_1)
        G.add_node('symbol-3', **asset_symbol_2)
        G.add_node('symbol-4', **non_asset_symbol_2)
        G.add_node('symbol-5', **asset_symbol_3)
        G.add_node('line-1', type=GraphNodeType.line, label='asset-1')

        expected = [
            ('symbol-1', asset_symbol_1),
            ('symbol-2', non_asset_symbol_1),
            ('symbol-3', asset_symbol_2),
            ('symbol-4', non_asset_symbol_2),
            ('symbol-5', asset_symbol_3),
        ]

        graph_service = GraphService(G)

        # act
        symbol_nodes = graph_service.get_symbol_nodes()

        # assert
        assert sorted(symbol_nodes, key=lambda x: x[0]) == sorted(expected, key=lambda x: x[0])

    def test_happy_path_no_symbols(self):
        # arrange
        G = nx.Graph()

        G.add_node('line-1', type=GraphNodeType.line)

        expected = []
        graph_service = GraphService(G)

        # act
        symbol_nodes = graph_service.get_symbol_nodes()

        # assert
        assert symbol_nodes == expected


class TestGetArrowSymbolsAtTJunction(unittest.TestCase):
    def test_when_no_T_junction_returns_empty_list(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label)

        G.add_edge('line-1', 'line-2')
        G.add_edge('line-2', 'arrow-1')
        G.add_edge('arrow-1', 'line-3')

        graph_service = GraphService(G)

        # act
        arrow_symbols = graph_service.get_arrow_symbols_at_T_junction(arrow_symbol_label)

        # assert
        assert arrow_symbols == []

    def test_when_1_T_junction_returns_id_of_node(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label)

        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('arrow-1', 'line-3')

        graph_service = GraphService(G)

        # act
        arrow_symbols = graph_service.get_arrow_symbols_at_T_junction(arrow_symbol_label)

        # assert
        assert arrow_symbols == ['arrow-1']

    def test_when_multiple_T_junctions_returns_multiple_node_ids(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('line-4', type=GraphNodeType.line)
        G.add_node('line-5', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label)
        G.add_node('arrow-2', type=GraphNodeType.symbol, label=arrow_symbol_label)

        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('arrow-1', 'line-3')
        G.add_edge('line-3', 'arrow-2')
        G.add_edge('arrow-2', 'line-4')
        G.add_edge('arrow-2', 'line-5')

        graph_service = GraphService(G)

        # act
        arrow_symbols = graph_service.get_arrow_symbols_at_T_junction(arrow_symbol_label)

        # assert
        assert sorted(arrow_symbols) == sorted(['arrow-1', 'arrow-2'])

    def test_when_arrow_intersection_with_more_than_3_degree_returns_arrow_node_id(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('line-3', type=GraphNodeType.line)
        G.add_node('line-4', type=GraphNodeType.line)
        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label)

        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('arrow-1', 'line-3')
        G.add_edge('arrow-1', 'line-4')

        graph_service = GraphService(G)

        # act
        arrow_symbols = graph_service.get_arrow_symbols_at_T_junction(arrow_symbol_label)

        # assert
        assert arrow_symbols == ['arrow-1']

    def test_when_arrow_intersection_with_degree_more_than_2_but_less_than_3_line_connections_returns_empty_list(self):
        # arrange
        arrow_symbol_label = 'arrow'

        G = nx.Graph()
        G.add_node('line-1', type=GraphNodeType.line)
        G.add_node('line-2', type=GraphNodeType.line)
        G.add_node('symbol-1', type=GraphNodeType.symbol)
        G.add_node('arrow-1', type=GraphNodeType.symbol, label=arrow_symbol_label)

        G.add_edge('line-1', 'arrow-1')
        G.add_edge('arrow-1', 'line-2')
        G.add_edge('arrow-1', 'symbol-1')

        graph_service = GraphService(G)

        # act
        arrow_symbols = graph_service.get_arrow_symbols_at_T_junction(arrow_symbol_label)

        # assert
        assert arrow_symbols == []


class TestPublishSources(unittest.TestCase):
    def test_when_no_untraveable_node_ids_then_does_not_update_nodes(self):
        # arrange
        temp_sources_key = 'temp_sources'
        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, temp_sources=set(), **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, temp_sources={'symbol-1'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, temp_sources=set(), **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'symbol-2')
        G.add_edge('symbol-2', 'symbol-3')

        graph_service = GraphService(G)

        # act
        graph_service.publish_sources(temp_sources_key)

        # assert
        assert G.nodes['symbol-1'][SymbolNodeKeysConfig.SOURCES_KEY] == set()
        assert G.nodes['symbol-2'][SymbolNodeKeysConfig.SOURCES_KEY] == {'symbol-1'}
        assert G.nodes['symbol-3'][SymbolNodeKeysConfig.SOURCES_KEY] == set()


    def test_when_degree_0_then_updates_source_accordingly(self):
        # arrange
        temp_sources_key = 'temp_sources'
        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, temp_sources=set(), **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, temp_sources={'symbol-1'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, temp_sources=set(), **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        graph_service = GraphService(G)

        # act
        graph_service.publish_sources(temp_sources_key)

        # assert
        assert G.nodes['symbol-1'][SymbolNodeKeysConfig.SOURCES_KEY] == set()
        assert G.nodes['symbol-2'][SymbolNodeKeysConfig.SOURCES_KEY] == {'symbol-1'}
        assert G.nodes['symbol-3'][SymbolNodeKeysConfig.SOURCES_KEY] == set()

    def test_when_untraceable_node_with_same_number_of_sources_as_degree_then_makes_necessary_updates(self):
        # arrange
        temp_sources_key = 'temp_sources'
        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, temp_sources={'symbol-2'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, temp_sources={'symbol-3', 'symbol-1'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, temp_sources={'symbol-2'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'symbol-2')
        G.add_edge('symbol-2', 'symbol-3')

        graph_service = GraphService(G)

        # act
        graph_service.publish_sources(temp_sources_key)

        # assert
        symbol_1_sources = G.nodes['symbol-1'][SymbolNodeKeysConfig.SOURCES_KEY]
        symbol_2_sources = G.nodes['symbol-2'][SymbolNodeKeysConfig.SOURCES_KEY]
        symbol_3_sources = G.nodes['symbol-3'][SymbolNodeKeysConfig.SOURCES_KEY]
        assert symbol_1_sources == set()
        assert symbol_2_sources == set()
        assert symbol_3_sources == set()

    def test_when_untraceable_node_with_different_number_of_sources_as_degree_then_makes_necessary_updates(self):
        # arrange
        temp_sources_key = 'temp_sources'
        G = nx.Graph()
        G.add_node('symbol-1', type=GraphNodeType.symbol, temp_sources={'symbol-2'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-2', type=GraphNodeType.symbol, temp_sources={'symbol-3', 'symbol-1'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-3', type=GraphNodeType.symbol, temp_sources={'symbol-2'}, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})
        G.add_node('symbol-4', type=GraphNodeType.symbol, **{SymbolNodeKeysConfig.SOURCES_KEY: set()})

        G.add_edge('symbol-1', 'symbol-2')
        G.add_edge('symbol-2', 'symbol-3')
        G.add_edge('symbol-2', 'symbol-4')

        graph_service = GraphService(G)

        # act
        graph_service.publish_sources(temp_sources_key)

        # assert
        symbol_1_sources = G.nodes['symbol-1'][SymbolNodeKeysConfig.SOURCES_KEY]
        symbol_2_sources = G.nodes['symbol-2'][SymbolNodeKeysConfig.SOURCES_KEY]
        symbol_3_sources = G.nodes['symbol-3'][SymbolNodeKeysConfig.SOURCES_KEY]
        symbol_4_sources = G.nodes['symbol-4'][SymbolNodeKeysConfig.SOURCES_KEY]
        assert symbol_1_sources == set()
        assert symbol_2_sources == set()
        assert symbol_3_sources == set()
        assert symbol_4_sources == set()
