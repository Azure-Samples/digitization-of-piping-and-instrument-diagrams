import os
import sys
import unittest
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from app.models.bounding_box import BoundingBox
from app.models.enums.flow_direction import FlowDirection
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_construction.connected_symbols_connection_item import ConnectedSymbolsConnectionItem
from app.services.graph_persistence.graph_persistence_service import persist


class TestGraphPersistenceService(unittest.TestCase):
    def test_happy_path_invokes_commit(self):
        # arrange
        cursor_mock = MagicMock()

        connection_mock = MagicMock()
        connection_mock.cursor = MagicMock(return_value=cursor_mock)

        db_mock = MagicMock()
        db_mock.connect = MagicMock(return_value=connection_mock)

        instance = MagicMock()
        pnid_graph_db_mock = MagicMock(return_value=instance)
        instance.delete_existing_graph = MagicMock()
        instance.create_graph = MagicMock()

        connected_symbols = [
            ConnectedSymbolsItem(id=1, label='Equipment/Compressor', text_associated='E-12346', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), connections=[
                ConnectedSymbolsConnectionItem(id=2, label='Instrument/Sensor', text_associated='DSF-321', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), flow_direction=FlowDirection.downstream, segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
            ])
        ]

        # act  app.repository.connect
        with patch("app.services.graph_persistence.graph_persistence_service.db", db_mock), \
             patch("app.services.graph_persistence.graph_persistence_service.PnidGraphDb", pnid_graph_db_mock):
            persist('1', connected_symbols)

        # assert
        db_mock.connect.assert_called_once()
        connection_mock.cursor.assert_called_once()
        connection_mock.commit.assert_called_once()
        connection_mock.close.assert_called_once()
        cursor_mock.close.assert_called_once()
        instance.delete_existing_graph.assert_called_once_with('1')
        instance.create_graph.assert_called_once_with('1', connected_symbols)

    def test_failure_path_invokes_commit_with_rollback_path(self):
        # arrange
        cursor_mock = MagicMock()

        connection_mock = MagicMock()
        connection_mock.cursor = MagicMock(return_value=cursor_mock)
        connection_mock.commit = MagicMock(side_effect=Exception('Error in database execution query'))

        db_mock = MagicMock()
        db_mock.connect = MagicMock(return_value=connection_mock)

        instance = MagicMock()
        pnid_graph_db_mock = MagicMock(return_value=instance)
        instance.delete_existing_graph = MagicMock()
        instance.create_graph = MagicMock()

        connected_symbols = [
            ConnectedSymbolsItem(id=1, label='Equipment/Compressor/Pressure', text_associated='E-12346', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), 
                                 connections=[
                                    ConnectedSymbolsConnectionItem(id=2, label='Instrument/Sensor/Pressure', text_associated='DSF-321', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), flow_direction=FlowDirection.downstream, segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
            ])
        ]

        # act  app.repository.connect
        with patch("app.services.graph_persistence.graph_persistence_service.db", db_mock), \
             patch("app.services.graph_persistence.graph_persistence_service.PnidGraphDb", pnid_graph_db_mock):
             with pytest.raises(Exception):
                persist('1', connected_symbols)

        # assert
        db_mock.connect.assert_called_once()
        connection_mock.cursor.assert_called_once()
        connection_mock.commit.assert_called_once()
        connection_mock.rollback.assert_called_once()
        connection_mock.close.assert_called_once()
        cursor_mock.close.assert_called_once()
        instance.delete_existing_graph.assert_called_once_with('1')
        instance.create_graph.assert_called_once_with('1', connected_symbols)

    def test_persist_graph_with_no_connector(self):
        # arrange
        cursor_mock = MagicMock()

        connection_mock = MagicMock()
        connection_mock.cursor = MagicMock(return_value=cursor_mock)
        connection_mock.commit = MagicMock()

        db_mock = MagicMock()
        db_mock.connect = MagicMock(return_value=connection_mock)

        connected_symbols = [
            ConnectedSymbolsItem(id=1, label='Equipment/Compressor/Pressure', text_associated='E-12346', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), connections=[
                ConnectedSymbolsConnectionItem(id=2, label='Instrument/Sensor/Pressure', text_associated='DSF-321', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), flow_direction=FlowDirection.downstream, segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
            ])
        ]

        # act  app.repository.connect
        with patch("app.services.graph_persistence.graph_persistence_service.db", db_mock):
            persist('1', connected_symbols)

        # assert
        params = [
            ('DELETE [pnide].[asset] FROM [pnide].[Asset] as asset, [pnide].[ispartof] as ispartof, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (asset-(ispartof)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[connector] FROM [pnide].[Connector] as connector, [pnide].[Resides] as resides, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (connector-(resides)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[sheet] FROM [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE FROM [pnide].[PNID] WHERE Id = ?', '1'),
            ('INSERT INTO [pnide].[PNID] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Sheet] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Belongs] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?), (SELECT $node_id FROM [pnide].[PNID] WHERE Id = ?));', '1', '1'),
            ('IF NOT EXISTS (SELECT * FROM [pnide].[AssetType] WHERE [uniquestring] = ?) INSERT INTO [pnide].[AssetType] (category, subcategory, displayname) VALUES (?,?,?);', 'Equipment/Compressor/Pressure', 'Equipment', 'Compressor', 'Pressure'),
            ('IF NOT EXISTS (SELECT * FROM [pnide].[AssetType] WHERE [uniquestring] = ?) INSERT INTO [pnide].[AssetType] (category, subcategory, displayname) VALUES (?,?,?);', 'Instrument/Sensor/Pressure', 'Instrument', 'Sensor', 'Pressure'),
            ('INSERT INTO [pnide].[Asset] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/1', 'E-12346', '{}'),
            ('INSERT INTO [pnide].[IsPartOf] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));','1/1/1', '1'),
            ('INSERT INTO [pnide].[Labeled] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[AssetType] WHERE uniquestring = ?));', '1/1/1', 'Equipment/Compressor/Pressure'),
            ('INSERT INTO [pnide].[Asset] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/2', 'DSF-321', '{}'),
            ('INSERT INTO [pnide].[IsPartOf] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));',  '1/1/2', '1'),
            ('INSERT INTO [pnide].[Labeled] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[AssetType] WHERE uniquestring = ?));', '1/1/2', 'Instrument/Sensor/Pressure'),
            ('INSERT INTO [pnide].[Connected] ($from_id, $to_id, segments) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), ?);', '1/1/1', '1/1/2', '[{"topX": 0.0, "topY": 0.0, "bottomX": 0.1, "bottomY": 0.1}]')
        ]

        for i, param in enumerate(params):
            for j, value in enumerate(param):
                assert value == ' '.join(cursor_mock.execute.mock_calls[i].args[j].split())


    def test_persist_graph_with_connector(self):
        # arrange
        cursor_mock = MagicMock()

        connection_mock = MagicMock()
        connection_mock.cursor = MagicMock(return_value=cursor_mock)
        connection_mock.commit = MagicMock()

        db_mock = MagicMock()
        db_mock.connect = MagicMock(return_value=connection_mock)

        connected_symbols = [
            ConnectedSymbolsItem(id=1, label='Piping/Endpoint/Pagination', text_associated='E-12346', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), connections=[
                ConnectedSymbolsConnectionItem(id=2, label='Instrument/Sensor/Pressure', text_associated='DSF-321', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), flow_direction=FlowDirection.downstream, segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
            ])
        ]

        # act  app.repository.connect
        with patch("app.services.graph_persistence.graph_persistence_service.db", db_mock):
            persist('1', connected_symbols)

        # assert
        params = [
            ('DELETE [pnide].[asset] FROM [pnide].[Asset] as asset, [pnide].[ispartof] as ispartof, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (asset-(ispartof)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[connector] FROM [pnide].[Connector] as connector, [pnide].[Resides] as resides, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (connector-(resides)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[sheet] FROM [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE FROM [pnide].[PNID] WHERE Id = ?', '1'),
            ('INSERT INTO [pnide].[PNID] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Sheet] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Belongs] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?), (SELECT $node_id FROM [pnide].[PNID] WHERE Id = ?));', '1', '1'),
            ('IF NOT EXISTS (SELECT * FROM [pnide].[AssetType] WHERE [uniquestring] = ?) INSERT INTO [pnide].[AssetType] (category, subcategory, displayname) VALUES (?,?,?);', 'Instrument/Sensor/Pressure', 'Instrument', 'Sensor', 'Pressure'),
            ('INSERT INTO [pnide].[Connector] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/1', 'E-12346', 'null'),
            ('INSERT INTO [pnide].[Resides] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));', '1/1/1', '1'),
            ('INSERT INTO [pnide].[Asset] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/2', 'DSF-321', '{}'),
            ('INSERT INTO [pnide].[IsPartOf] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));',  '1/1/2', '1'),
            ('INSERT INTO [pnide].[Labeled] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), (SELECT $node_id FROM [pnide].[AssetType] WHERE uniquestring = ?));', '1/1/2', 'Instrument/Sensor/Pressure'),
            ('INSERT INTO [pnide].[Outputs] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?));', '1/1/1', '1/1/2')
        ]

        for i, param in enumerate(params):
            for j, value in enumerate(param):
                assert value == ' '.join(cursor_mock.execute.mock_calls[i].args[j].split())


    def test_persist_graph_with_connector_to_connector(self):
        # arrange
        cursor_mock = MagicMock()

        connection_mock = MagicMock()
        connection_mock.cursor = MagicMock(return_value=cursor_mock)
        connection_mock.commit = MagicMock()

        db_mock = MagicMock()
        db_mock.connect = MagicMock(return_value=connection_mock)

        connected_symbols = [
            ConnectedSymbolsItem(id=1, label='Piping/Endpoint/Pagination', text_associated='E-12346', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), connections=[
                ConnectedSymbolsConnectionItem(id=2, label='Piping/Endpoint/Pagination', text_associated='DSF-321', bounding_box=BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1), flow_direction=FlowDirection.downstream, segments=[BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)])
            ])
        ]

        # act  app.repository.connect
        with patch("app.services.graph_persistence.graph_persistence_service.db", db_mock):
            persist('1', connected_symbols)

        # assert
        params = [
            ('DELETE [pnide].[asset] FROM [pnide].[Asset] as asset, [pnide].[ispartof] as ispartof, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (asset-(ispartof)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[connector] FROM [pnide].[Connector] as connector, [pnide].[Resides] as resides, [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (connector-(resides)->sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE [pnide].[sheet] FROM [pnide].[sheet] as sheet, [pnide].[belongs] as belongs, [pnide].[pnid] as pnid WHERE MATCH (sheet-(belongs)->pnid) AND pnid.Id = ?', '1'),
            ('DELETE FROM [pnide].[PNID] WHERE Id = ?', '1'),
            ('INSERT INTO [pnide].[PNID] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Sheet] (Id, name, attributes) VALUES (?,?,?);', '1', '1', '{}'),
            ('INSERT INTO [pnide].[Belongs] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?), (SELECT $node_id FROM [pnide].[PNID] WHERE Id = ?));', '1', '1'),
            ('INSERT INTO [pnide].[Connector] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/1', 'E-12346', 'null'),
            ('INSERT INTO [pnide].[Resides] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));', '1/1/1', '1'),
            ('INSERT INTO [pnide].[Connector] (Id, text_associated, attributes) VALUES (?,?,?);', '1/1/2', 'DSF-321', 'null'),
            ('INSERT INTO [pnide].[Resides] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));', '1/1/2', '1'),
            ('INSERT INTO [pnide].[Refers] ($from_id, $to_id) VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?));', '1/1/1', '1/1/2')]

        for i, param in enumerate(params):
            for j, value in enumerate(param):
                assert value == ' '.join(cursor_mock.execute.mock_calls[i].args[j].split())

