# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pyodbc import Cursor
import app.repository.database_repository as database_repository
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_persistence.nodes.asset_type import AssetType
from app.models.graph_persistence.nodes.pnid import PnId
from app.models.graph_persistence.nodes.sheet import Sheet
from app.models.graph_persistence.edges.base_edge import BaseEdge
from app.config import config
from app.models.graph_persistence.nodes.connector import Connector
import app.services.graph_persistence.node_id_generator as node_id_generator
from app.models.enums.flow_direction import FlowDirection
from app.models.graph_persistence.nodes.asset import Asset
from app.models.graph_persistence.edges.connected import Connected
import logger_config


logger = logger_config.get_logger(__name__)


class PnidGraphDb:
    """
    Main responsiblity of this class is to create the pnid graph in the database
    """
    def __init__(self, cursor: Cursor):
        self.cursor = cursor

    def _is_connector(self, label: str):
        '''
        Checks if the label is a connector
        :param label: label of the symbol'''
        return label in config.symbol_label_for_connectors

    def delete_existing_graph(self, pnd_id):
        database_repository.delete_pnid(self.cursor, pnd_id)

    def create_graph(self, pid_id: str, asset_connected: list[ConnectedSymbolsItem]):
        pnid_node = PnId(id=pid_id, name=pid_id, attributes={})
        # Since we are not collecting the sheet information, we will create a sheet node for each pnid with the same id.
        sheet_node = Sheet(id=pid_id, name=pid_id, attributes={})

        # step 1: Create pnid and sheet nodes and their edges
        logger.debug(f'Creating pnid node {pnid_node}')
        database_repository.create_pnid_node(self.cursor, pnid_node)
        logger.debug(f'Creating sheet node {sheet_node}')
        database_repository.create_sheet_node(self.cursor, sheet_node)
        logger.debug(f'Creating belongs edge between pnid {pnid_node} and sheet {sheet_node}')
        database_repository.create_belongs_edge(self.cursor, BaseEdge(from_id=sheet_node.id, to_id=pnid_node.id))

        # step 2: create asset types if they don't exist
        logger.debug('Creating asset types')
        self._create_all_asset_types(asset_connected)
        logger.debug('Finished creating asset types')

        # step 3: create all the assets and connector nodes
        logger.debug('Creating assets and connectors')
        self._create_all_assets_connectors(pnid_node, sheet_node, asset_connected)
        logger.debug('Finished creating assets and connectors')

        # Create all edges between assets and connectors
        logger.debug('Creating edges between assets and connectors')
        self._create_all_asset_connectors_edges(pnid_node, sheet_node, asset_connected)
        logger.debug('Finished creating edges between assets and connectors')

    def _create_all_asset_types(self, asset_connected: list[ConnectedSymbolsItem]):
        created_asset_type_nodes = set()

        # create asset types if they don't exist
        for asset in asset_connected:
            if asset.label not in created_asset_type_nodes and not self._is_connector(asset.label):
                database_repository.create_asset_type_node(self.cursor, AssetType(uniquestring=asset.label))
                created_asset_type_nodes.add(asset.label)

            for connection in asset.connections:
                if connection.label not in created_asset_type_nodes and not self._is_connector(connection.label):
                    logger.debug(f'Creating asset type {connection.label}')
                    database_repository.create_asset_type_node(self.cursor, AssetType(uniquestring=connection.label))
                    created_asset_type_nodes.add(connection.label)

    def _create_all_assets_connectors(self, pnid_node: PnId, sheet_node: Sheet, asset_connected: list[ConnectedSymbolsItem]):
        created_nodes = set()  # assets and connector ids

        # Create all the assets and connector nodes
        for asset in asset_connected:
            if self._is_connector(asset.label):
                connector_node_id = node_id_generator.get_connector_node_id(pnid_node, sheet_node, asset)
                if connector_node_id not in created_nodes:
                    database_repository.create_connector_node(
                        self.cursor,
                        Connector(
                            id=connector_node_id,
                            name=asset.label,
                            text_associated=asset.text_associated))
                    database_repository.create_resides_edge(self.cursor, BaseEdge(from_id=connector_node_id, to_id=sheet_node.id))
                    created_nodes.add(connector_node_id)
            else:
                asset_node_id = node_id_generator.get_asset_node_id(pnid_node, sheet_node, asset)
                if asset_node_id not in created_nodes:
                    asset_node = Asset(id=asset_node_id, text_associated=asset.text_associated, attributes={})
                    database_repository.create_asset_node(self.cursor, asset_node)
                    database_repository.create_is_part_of_edge(self.cursor, BaseEdge(from_id=asset_node_id, to_id=sheet_node.id))
                    database_repository.create_labeled_edge(self.cursor, BaseEdge(from_id=asset_node_id, to_id=asset.label))
                    created_nodes.add(asset_node_id)

            for connection in asset.connections:
                if self._is_connector(connection.label):
                    connection_connector_node_id = node_id_generator.get_connector_node_id(pnid_node, sheet_node, connection)
                    if connection_connector_node_id not in created_nodes:
                        database_repository.create_connector_node(
                            self.cursor,
                            Connector(
                                id=connection_connector_node_id,
                                name=connection.label,
                                text_associated=connection.text_associated))
                        reside_edge = BaseEdge(from_id=connection_connector_node_id, to_id=sheet_node.id)
                        database_repository.create_resides_edge(self.cursor, reside_edge)
                        created_nodes.add(connection_connector_node_id)
                else:
                    connection_asset_node_id = node_id_generator.get_asset_node_id(pnid_node, sheet_node, connection)
                    if connection_asset_node_id not in created_nodes:
                        connection_asset_node = Asset(
                            id=connection_asset_node_id,
                            text_associated=connection.text_associated,
                            attributes={})
                        database_repository.create_asset_node(self.cursor, connection_asset_node)
                        is_part_of_edge = BaseEdge(from_id=connection_asset_node_id, to_id=sheet_node.id)
                        database_repository.create_is_part_of_edge(self.cursor, is_part_of_edge)
                        is_labeled_edge = BaseEdge(from_id=connection_asset_node_id, to_id=connection.label)
                        database_repository.create_labeled_edge(self.cursor, is_labeled_edge)
                        created_nodes.add(connection_asset_node_id)

    def _create_all_asset_connectors_edges(self, pnid_node: PnId, sheet_node: Sheet, asset_connected: list[ConnectedSymbolsItem]):
        """
        Creates all the edges between assets and connectors.
        """
        for asset in asset_connected:
            if self._is_connector(asset.label):
                # Connector is source. Hence, connector -> asset
                connector_node_id = node_id_generator.get_connector_node_id(pnid_node, sheet_node, asset)
                for connection in asset.connections:
                    if connection.flow_direction is FlowDirection.downstream or connection.flow_direction is FlowDirection.unknown:
                        if self._is_connector(connection.label):
                            connection_connector_node_id = node_id_generator.get_connector_node_id(pnid_node, sheet_node, connection)
                            database_repository.create_refers_edge(self.cursor,
                                                                   BaseEdge(from_id=connector_node_id,
                                                                            to_id=connection_connector_node_id))
                        else:
                            asset_node_id = node_id_generator.get_asset_node_id(pnid_node, sheet_node, connection)
                            database_repository.create_outputs_edge(self.cursor, BaseEdge(from_id=connector_node_id, to_id=asset_node_id))
            else:
                # Asset is source. Hence, asset -> asset or asset -> connector
                asset_node_id = node_id_generator.get_asset_node_id(pnid_node, sheet_node, asset)
                for connection in asset.connections:
                    if self._is_connector(connection.label):
                        if connection.flow_direction is FlowDirection.downstream or connection.flow_direction is FlowDirection.unknown:
                            connector_node_id = node_id_generator.get_connector_node_id(pnid_node, sheet_node, connection)
                            database_repository.create_inputs_edge(self.cursor, BaseEdge(from_id=asset_node_id, to_id=connector_node_id))
                    else:
                        if connection.flow_direction is FlowDirection.downstream or connection.flow_direction is FlowDirection.unknown:
                            connection_asset_node_id = node_id_generator.get_asset_node_id(pnid_node, sheet_node, connection)
                            database_repository.create_connected_edge(
                                self.cursor,
                                Connected(from_id=asset_node_id, to_id=connection_asset_node_id, segments=connection.segments))
