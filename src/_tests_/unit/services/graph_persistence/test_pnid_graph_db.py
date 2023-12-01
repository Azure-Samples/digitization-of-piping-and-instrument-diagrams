# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import sys
import unittest
from unittest.mock import MagicMock, call, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.graph_persistence.pnid_graph_db import PnidGraphDb
from app.models.bounding_box import BoundingBox
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_persistence.nodes.asset_type import AssetType
from app.models.graph_persistence.edges.base_edge import BaseEdge
from app.models.graph_persistence.nodes.connector import Connector
from app.models.graph_persistence.nodes.sheet import Sheet
from app.models.graph_persistence.nodes.asset import Asset
from app.models.enums.flow_direction import FlowDirection
from app.models.graph_construction.connected_symbols_connection_item import ConnectedSymbolsConnectionItem
from app.models.graph_persistence.edges.connected import Connected
from app.models.graph_persistence.nodes.pnid import PnId


class TestPnidGraphDb(unittest.TestCase):
    def test_is_connector_returns_true_for_connector(self):
        # arrange
        instance = PnidGraphDb(MagicMock())
        config_mock = MagicMock()
        config_mock.symbol_label_for_connectors = "symbol_mock"

        # act
        with patch("app.services.graph_persistence.pnid_graph_db.config", config_mock):
            result = instance._is_connector('symbol_mock')

        # assert
        self.assertTrue(result)

    def test_is_connector_returns_false_for_non_connector(self):
        # arrange
        instance = PnidGraphDb(MagicMock())
        config_mock = MagicMock()
        config_mock.symbol_label_for_connectors = "symbol_mock"

        # act
        with patch("app.services.graph_persistence.pnid_graph_db.config", config_mock):
            result = instance._is_connector('NonConnector')

        # assert
        self.assertFalse(result)

    def test_create_asset_types_when_not_exists(self):
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        database_repository_mock = MagicMock()
        database_repository_mock.create_asset_type_node = MagicMock(return_value=None)

        # Test data with unique asset labels and no connection
        asset_connected = [
            ConnectedSymbolsItem(id=1,
                                 label='Piping/Endpoint/Connector b',
                                 text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[]),
        ]

        # Mock the return value of _is_connector method to False
        instance._is_connector = MagicMock(return_value=False)

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock):
            instance._create_all_asset_types(asset_connected)

        # Ensure that create_asset_type_node is called with the expected argument
        instance._is_connector.assert_called_once_with('Piping/Endpoint/Connector b')
        database_repository_mock.create_asset_type_node.assert_called_once()
        database_repository_mock.create_asset_type_node.assert_called_once_with(cursor_mock,
                                                                                AssetType(uniquestring='Piping/Endpoint/Connector b'))

    def test_create_asset_types_when_exists(self):
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        database_repository_mock = MagicMock()
        database_repository_mock.create_asset_type_node = MagicMock(return_value=None)

        asset_label = 'Piping/Endpoint/Pagination'
        # Test data with unique asset labels and no connection
        asset_connected = [
            ConnectedSymbolsItem(id=1,
                                 label=asset_label,
                                 text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[]),
        ]

        # Mock the return value of _is_connector method to True
        instance._is_connector = MagicMock(return_value=True)

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock):
            instance._create_all_asset_types(asset_connected)

        # Ensure that create_asset_type_node is called with the expected argument
        instance._is_connector.assert_called_once_with(asset_label)
        database_repository_mock.create_asset_type_node.assert_not_called()

    def test_create_all_assets_connectors_connector_node(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to True
        instance._is_connector = MagicMock(return_value=True)

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/assetid'
        node_id_generator_mock.get_connector_node_id = MagicMock(return_value=connector_id)

        database_repository_mock = MagicMock()
        database_repository_mock.create_connector_node = MagicMock(return_value=None)
        database_repository_mock.create_resides_edge = MagicMock(return_value=None)

        asset_label = "Piping/Endpoint/Same"
        # Test data with unique asset labels and no connection
        asset_connected = [
            ConnectedSymbolsItem(id=1,
                                 label=asset_label,
                                 text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[]),
        ]
        sheet_node = Sheet(id='sheetid', name='sheetname')

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_assets_connectors('pnidid', sheet_node, asset_connected)

        # assert
        instance._is_connector.assert_called_once_with(asset_label)
        node_id_generator_mock.get_connector_node_id.assert_called_once_with('pnidid', sheet_node, asset_connected[0])
        database_repository_mock.create_connector_node.assert_called_once_with(cursor_mock, Connector(id=connector_id,
                                                                                                      name=asset_label,
                                                                                                      text_associated='E-12346'))
        database_repository_mock.create_resides_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=connector_id,
                                                                                                   to_id='sheetid'))

    def test_create_all_assets_connectors_asset_node(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to False for asset
        instance._is_connector = MagicMock(return_value=False)

        node_id_generator_mock = MagicMock()
        asset_id = 'pnidid/sheetid/assetid'
        node_id_generator_mock.get_asset_node_id = MagicMock(return_value=asset_id)

        database_repository_mock = MagicMock()
        database_repository_mock.create_asset_node = MagicMock(return_value=None)
        database_repository_mock.create_is_part_of_edge = MagicMock(return_value=None)
        database_repository_mock.create_labeled_edge = MagicMock(return_value=None)

        asset_label = "Asset1"
        # Test data with unique asset labels and no connection
        asset_connected = [
            ConnectedSymbolsItem(id=1,
                                 label=asset_label,
                                 text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[]),
        ]
        sheet_node = Sheet(id='sheetid', name='sheetname')

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_assets_connectors('pnidid', sheet_node, asset_connected)

        # assert
        instance._is_connector.assert_called_once_with(asset_label)
        node_id_generator_mock.get_asset_node_id.assert_called_once_with('pnidid', sheet_node, asset_connected[0])
        database_repository_mock.create_asset_node.assert_called_once_with(cursor_mock, Asset(id=asset_id,
                                                                                              text_associated='E-12346',
                                                                                              attributes={}))
        database_repository_mock.create_is_part_of_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                      to_id=sheet_node.id))
        database_repository_mock.create_labeled_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                   to_id=asset_label))

    def test_create_all_assets_connectors_connection_connector(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to True for connector
        instance._is_connector = MagicMock(return_value=True)

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/connectionid'
        asset_id = 'pnidid/sheetid/assetid'
        node_id_generator_mock.get_connector_node_id = MagicMock(side_effect=[asset_id, connector_id])

        database_repository_mock = MagicMock()
        database_repository_mock.create_connector_node = MagicMock(return_value=None)
        database_repository_mock.create_resides_edge = MagicMock(return_value=None)

        asset_label = "Equipment/Compressor"
        connection_label = 'Instrument/Sensor'
        # Test data with unique asset labels and no connection
        connected_symbols = [
            ConnectedSymbolsItem(id=1, label=asset_label, text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label=connection_label,
                                                                   text_associated='DSF-321',
                                                                   bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                                                   flow_direction=FlowDirection.downstream,
                                                                   segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
                                                                ])
        ]

        sheet_node = Sheet(id='sheetid', name='sheetname')

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_assets_connectors('pnidid', sheet_node, connected_symbols)

        # assert that _is_connector is called for both asset and connection
        instance._is_connector.assert_has_calls([call(asset_label), call(connection_label)])
        # assert that get_connector_node_id is called for both asset and connection
        node_id_generator_mock.get_connector_node_id.assert_has_calls([call('pnidid', sheet_node, connected_symbols[0]),
                                                                       call('pnidid', sheet_node, connected_symbols[0].connections[0])])
        # assert that create_connector_node is called for both asset and connection
        database_repository_mock.create_connector_node.assert_has_calls([call(cursor_mock, Connector(id=asset_id,
                                                                                                     name=asset_label,
                                                                                                     text_associated='E-12346')),
                                                                         call(cursor_mock, Connector(id=connector_id,
                                                                                                     name=connection_label,
                                                                                                     text_associated='DSF-321'))])

        # assert that create_resides_edge is called for both asset and connection
        database_repository_mock.create_resides_edge.assert_has_calls([call(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                  to_id=sheet_node.id)),
                                                                       call(cursor_mock, BaseEdge(from_id=connector_id,
                                                                                                  to_id=sheet_node.id))])

    def test_create_all_assets_connectors_connection_asset(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to False for connector
        instance._is_connector = MagicMock(return_value=False)

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/connectionid'
        asset_id = 'pnidid/sheetid/assetid'
        node_id_generator_mock.get_connector_node_id = MagicMock(side_effect=[asset_id, connector_id])
        node_id_generator_mock.get_asset_node_id = MagicMock(side_effect=[asset_id, connector_id])

        database_repository_mock = MagicMock()
        database_repository_mock.create_asset_node = MagicMock(return_value=None)
        database_repository_mock.create_is_part_of_edge = MagicMock(return_value=None)

        asset_label = "Equipment/Compressor"
        connection_label = 'Instrument/Sensor'
        # Test data with unique asset labels and no connection
        connected_symbols = [
            ConnectedSymbolsItem(id=1, label=asset_label, text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label=connection_label,
                                                                   text_associated='DSF-321',
                                                                   bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                                                   flow_direction=FlowDirection.downstream,
                                                                   segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
                                                                ])
        ]

        sheet_node = Sheet(id='sheetid', name='sheetname')

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_assets_connectors('pnidid', sheet_node, connected_symbols)

        # assert that _is_connector is called for both asset and connection
        instance._is_connector.assert_has_calls([call(asset_label), call(connection_label)])
        # assert that get_asset_node_id is called for both asset and connection
        node_id_generator_mock.get_asset_node_id.assert_has_calls([call('pnidid', sheet_node, connected_symbols[0]),
                                                                   call('pnidid', sheet_node, connected_symbols[0].connections[0])])
        # assert that create_connector_node is called for both asset and connection
        database_repository_mock.create_asset_node.assert_has_calls([call(cursor_mock, Asset(id=asset_id,
                                                                                             text_associated='E-12346',
                                                                                             attributes={})),
                                                                    call(cursor_mock, Asset(id=connector_id,
                                                                                            text_associated='DSF-321',
                                                                                            attributes={}))])
        # assert that create_resides_edge is called for both asset and connection
        database_repository_mock.create_is_part_of_edge.assert_has_calls([call(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                     to_id=sheet_node.id)),
                                                                          call(cursor_mock, BaseEdge(from_id=connector_id,
                                                                                                     to_id=sheet_node.id))])

        # assert that create_labeled_edge is called for both asset and connection
        database_repository_mock.create_labeled_edge.assert_has_calls([call(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                  to_id=asset_label)),
                                                                       call(cursor_mock, BaseEdge(from_id=connector_id,
                                                                                                  to_id=connection_label))])

    def test_create_all_asset_connectors_edges_connector(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/connectionid'
        asset_id = 'pnidid/sheetid/assetid'
        node_id_generator_mock.get_connector_node_id = MagicMock(return_value=connector_id)
        node_id_generator_mock.get_asset_node_id = MagicMock(return_value=asset_id)

        database_repository_mock = MagicMock()
        database_repository_mock.create_outputs_edge = MagicMock(return_value=None)

        connection_label = "Equipment/Compressor"
        asset_label = 'Piping/Endpoint/Pagination'
        # Test data with unique asset labels and no connection
        connected_symbols = [
            ConnectedSymbolsItem(id=1, label=asset_label, text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label=connection_label,
                                                                   text_associated='DSF-321',
                                                                   bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                                                   flow_direction=FlowDirection.downstream,
                                                                   segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
                                                                ])
        ]

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_asset_connectors_edges('pnidid', 'sheetid', connected_symbols)

        # assert that get_asset_node_id is called once
        node_id_generator_mock.get_asset_node_id.assert_called_once_with('pnidid', 'sheetid', connected_symbols[0].connections[0])

        # assert that get_connector_node_id is called once
        node_id_generator_mock.get_connector_node_id.assert_called_once_with('pnidid', 'sheetid', connected_symbols[0])

        # assert that create_outputs_edge is called once
        database_repository_mock.create_outputs_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=connector_id,
                                                                                                   to_id=asset_id))

    def test_create_all_asset_connectors_edges_input(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to False for connector and True for asset
        instance._is_connector = MagicMock(side_effect=[False, True])

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/connectionid'
        asset_id = 'pnidid/sheetid/assetid'

        node_id_generator_mock.get_connector_node_id = MagicMock(return_value=connector_id)
        node_id_generator_mock.get_asset_node_id = MagicMock(return_value=asset_id)

        database_repository_mock = MagicMock()
        database_repository_mock.create_inputs_edge = MagicMock(return_value=None)

        asset_label = "Equipment/Compressor"
        connection_label = 'Instrument/Sensor'
        # Test data with unique asset labels and no connection
        connected_symbols = [
            ConnectedSymbolsItem(id=1, label=asset_label, text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label=connection_label,
                                                                   text_associated='DSF-321',
                                                                   bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                                                   flow_direction=FlowDirection.downstream,
                                                                   segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
                                                                ])
        ]

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_asset_connectors_edges('pnidid', 'sheetid', connected_symbols)

        # assert that _is_connector is called twice
        instance._is_connector.assert_has_calls([call(asset_label), call(connection_label)])

        # assert that get_asset_node_id is called once
        node_id_generator_mock.get_asset_node_id.assert_called_once_with('pnidid', 'sheetid', connected_symbols[0])

        # assert that get_connector_node_id is called once
        node_id_generator_mock.get_connector_node_id.assert_called_once_with('pnidid', 'sheetid', connected_symbols[0].connections[0])

        # assert that create_inputs_edge is called once
        database_repository_mock.create_inputs_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=asset_id,
                                                                                                  to_id=connector_id))

    def test_create_all_asset_connectors_edges_connected(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        # Mock the return value of _is_connector method to False for connector and False for asset
        instance._is_connector = MagicMock(side_effect=[False, False])

        node_id_generator_mock = MagicMock()
        connector_id = 'pnidid/sheetid/connectionid'
        asset_id = 'pnidid/sheetid/assetid'

        node_id_generator_mock.get_asset_node_id = MagicMock(side_effect=[asset_id, connector_id])

        database_repository_mock = MagicMock()
        database_repository_mock.create_connected_edge = MagicMock(return_value=None)

        asset_label = "Equipment/Compressor"
        connection_label = 'Instrument/Sensor'
        # Test data with unique asset labels and no connection
        connected_symbols = [
            ConnectedSymbolsItem(id=1, label=asset_label, text_associated='E-12346',
                                 bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label=connection_label,
                                                                   text_associated='DSF-321',
                                                                   bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1),
                                                                   flow_direction=FlowDirection.downstream,
                                                                   segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
                                                                ])
        ]

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock),\
                patch("app.services.graph_persistence.pnid_graph_db.node_id_generator", node_id_generator_mock):
            instance._create_all_asset_connectors_edges('pnidid', 'sheetid', connected_symbols)

        # assert that _is_connector is called twice
        instance._is_connector.assert_has_calls([call(asset_label), call(connection_label)])

        # assert that get_asset_node_id is called twice
        node_id_generator_mock.get_asset_node_id.assert_has_calls([call('pnidid', 'sheetid', connected_symbols[0]),
                                                                   call('pnidid', 'sheetid', connected_symbols[0].connections[0])])

        # assert that create_connected_edge is called once
        database_repository_mock.create_connected_edge.assert_called_once_with(cursor_mock, Connected(from_id=asset_id,
                                                                                                      to_id=connector_id,
                                                                                                      segments=[BoundingBox(topX=0.0,
                                                                                                                            topY=0.0,
                                                                                                                            bottomX=0.1,
                                                                                                                            bottomY=0.1)]))

    def test_delete_existing_graph(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        database_repository_mock = MagicMock()
        database_repository_mock.delete_pnid = MagicMock(return_value=None)

        # act
        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock):
            instance.delete_existing_graph('pnidid')

        # assert
        database_repository_mock.delete_pnid.assert_called_once_with(cursor_mock, 'pnidid')

    def test_create_graph_with_no_connections(self):
        # arrange
        cursor_mock = MagicMock()
        instance = PnidGraphDb(cursor_mock)

        database_repository_mock = MagicMock()
        database_repository_mock.create_pnid_node = MagicMock(return_value=None)
        database_repository_mock.create_sheet_node = MagicMock(return_value=None)
        database_repository_mock.create_belongs_edge = MagicMock(return_value=None)

        # Test data with no connection
        pnid_node = PnId(id="pid_id", name="pid_id", attributes={})
        connected_symbols = []

        with patch("app.services.graph_persistence.pnid_graph_db.database_repository", database_repository_mock):
            instance.create_graph(pnid_node.id, connected_symbols)

        database_repository_mock.create_pnid_node.assert_called_once_with(cursor_mock, pnid_node)
        database_repository_mock.create_sheet_node.assert_called_once_with(cursor_mock, Sheet(id=pnid_node.id, name=pnid_node.id,
                                                                                              attributes={}))
        database_repository_mock.create_belongs_edge.assert_called_once_with(cursor_mock, BaseEdge(from_id=pnid_node.id,
                                                                                                   to_id=pnid_node.id))
