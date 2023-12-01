# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import json
from app.models.graph_persistence.nodes.pnid import PnId
from app.models.graph_persistence.nodes.sheet import Sheet
from app.models.graph_persistence.nodes.connector import Connector
from app.models.graph_persistence.nodes.asset import Asset
from app.models.graph_persistence.nodes.asset_type import AssetType
from app.models.graph_persistence.edges.connected import Connected
import pyodbc
from app.models.graph_persistence.edges.base_edge import BaseEdge
import logger_config

logger = logger_config.get_logger(__name__)


def create_pnid_node(cursor: pyodbc.Cursor, pnid_entity: PnId):
    '''
    Create PNID node
    '''
    logger.debug(f'Creating pnid node {pnid_entity}')
    tsql = "INSERT INTO [pnide].[PNID] (Id, name, attributes) VALUES (?,?,?);"
    cursor.execute(tsql, pnid_entity.id, pnid_entity.name, json.dumps(pnid_entity.attributes))


def create_sheet_node(cursor: pyodbc.Cursor, sheet_entity: Sheet):
    '''
    Create Sheet node
    '''
    logger.debug(f'Creating sheet node {sheet_entity}')
    tsql = "INSERT INTO [pnide].[Sheet] (Id, name, attributes) VALUES (?,?,?);"
    cursor.execute(tsql, sheet_entity.id, sheet_entity.name, json.dumps(sheet_entity.attributes))


def create_asset_node(cursor: pyodbc.Cursor, asset_entity: Asset):
    '''
    Create Asset node
    '''
    logger.debug(f'Creating asset node {asset_entity}')
    tsql = "INSERT INTO [pnide].[Asset] (Id, text_associated, attributes) VALUES (?,?,?);"
    cursor.execute(tsql, asset_entity.id, asset_entity.text_associated, json.dumps(asset_entity.attributes))


def create_asset_type_node(cursor: pyodbc.Cursor, asset_type_entity: AssetType):
    '''
    Create Asset type node
    '''
    logger.debug(f'Creating asset type node {asset_type_entity}')
    tsql = """IF NOT EXISTS (SELECT * FROM [pnide].[AssetType] WHERE [uniquestring] = ?)
        INSERT INTO [pnide].[AssetType] (category, subcategory, displayname) VALUES (?,?,?);"""
    cursor.execute(tsql,
                   asset_type_entity.uniquestring,
                   asset_type_entity.category,
                   asset_type_entity.subcategory,
                   asset_type_entity.displayname)


def create_connector_node(cursor: pyodbc.Cursor, connector_entity: Connector):
    '''
    Create Connector node
    '''
    logger.debug(f'Creating connector node {connector_entity}')
    tsql = "INSERT INTO [pnide].[Connector] (Id, text_associated, attributes) VALUES (?,?,?);"
    cursor.execute(tsql, connector_entity.id, connector_entity.text_associated, json.dumps(connector_entity.attributes))


def create_belongs_edge(cursor: pyodbc.Cursor, belongs_entity: BaseEdge):
    '''
    Belongs edge creation => Sheet to PNID
    '''
    logger.debug(f'Creating belongs edge {belongs_entity}')
    tsql = """INSERT INTO [pnide].[Belongs] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?),
                        (SELECT $node_id FROM [pnide].[PNID] WHERE Id = ?));"""

    cursor.execute(tsql, belongs_entity.from_id, belongs_entity.to_id)


def create_connected_edge(cursor: pyodbc.Cursor, connected_entity: Connected):
    '''
    Connected edge creation => Asset to Asset
    '''
    logger.debug(f'Creating connected edge {connected_entity}')
    tsql = """INSERT INTO [pnide].[Connected] ($from_id, $to_id, segments)
                VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?),
                        (SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?), ?);"""

    cursor.execute(tsql,
                   connected_entity.from_id,
                   connected_entity.to_id,
                   json.dumps([segment.__dict__ for segment in connected_entity.segments]))


def create_labeled_edge(cursor: pyodbc.Cursor, labeled_entity: BaseEdge):
    '''
    Labeled edge creation => Asset to AssetType
    '''
    logger.debug(f'Creating labeled edge {labeled_entity}')
    tsql = """INSERT INTO [pnide].[Labeled] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?),
                        (SELECT $node_id FROM [pnide].[AssetType] WHERE uniquestring = ?));"""

    cursor.execute(tsql, labeled_entity.from_id, labeled_entity.to_id)


def create_inputs_edge(cursor: pyodbc.Cursor, inputs_entity: BaseEdge):
    '''
    Inputs edge creation => Asset to Connector
    '''
    logger.debug(f'Creating inputs edge {inputs_entity}')
    tsql = """INSERT INTO [pnide].[Inputs] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?),
                        (SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?));"""

    cursor.execute(tsql, inputs_entity.from_id, inputs_entity.to_id)


def create_outputs_edge(cursor: pyodbc.Cursor, outputs_entity: BaseEdge):
    '''
    Outputs edge creation => Connector to Asset
    '''
    logger.debug(f'Creating outputs edge {outputs_entity}')
    tsql = """INSERT INTO [pnide].[Outputs] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?));"""

    cursor.execute(tsql, outputs_entity.from_id, outputs_entity.to_id)


def create_refers_edge(cursor: pyodbc.Cursor, refers_entity: BaseEdge):
    '''
    Refers edge creation => Connector to Connector
    '''
    logger.debug(f'Creating refers edge {refers_entity}')
    tsql = """INSERT INTO [pnide].[Refers] ($from_id, $to_id)
            VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?));"""

    cursor.execute(tsql, refers_entity.from_id, refers_entity.to_id)


def create_resides_edge(cursor: pyodbc.Cursor, resides_entity: BaseEdge):
    '''
    Resides edge creation => Connector to Sheet
    '''
    logger.debug(f'Creating resides edge {resides_entity}')
    tsql = """INSERT INTO [pnide].[Resides] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Connector] WHERE Id = ?), (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));"""

    cursor.execute(tsql, resides_entity.from_id, resides_entity.to_id)


def create_is_part_of_edge(cursor: pyodbc.Cursor, is_part_of_entity: BaseEdge):
    '''
    IsPartOf edge creation => Asset to Sheet
    '''
    logger.debug(f'Creating is part of edge {is_part_of_entity}')
    tsql = """INSERT INTO [pnide].[IsPartOf] ($from_id, $to_id)
                VALUES ((SELECT $node_id FROM [pnide].[Asset] WHERE Id = ?),
                        (SELECT $node_id FROM [pnide].[Sheet] WHERE Id = ?));"""

    cursor.execute(tsql, is_part_of_entity.from_id, is_part_of_entity.to_id)


def delete_asset_ids_for_pid(cursor: pyodbc, pnId: str):
    '''
    Delete asset node and its associate edges
    '''
    logger.debug(f'Deleting asset node and its associate edges for {pnId}')
    tsql = """
        DELETE [pnide].[asset]
            FROM [pnide].[Asset] as asset,
                 [pnide].[ispartof] as ispartof,
                 [pnide].[sheet] as sheet,
                 [pnide].[belongs] as belongs,
                 [pnide].[pnid] as pnid
            WHERE MATCH (asset-(ispartof)->sheet-(belongs)->pnid)
                  AND pnid.Id = ?
        """
    cursor.execute(tsql, pnId)


def delete_connector_ids_for_pid(cursor: pyodbc, pnId: str):
    '''
    Delete connector node and its associate edges
    '''
    logger.debug(f'Deleting connector node and its associate edges for {pnId}')
    tsql = """
       DELETE [pnide].[connector]
            FROM [pnide].[Connector] as connector,
                 [pnide].[Resides] as resides,
                 [pnide].[sheet] as sheet,
                 [pnide].[belongs] as belongs,
                 [pnide].[pnid] as pnid
            WHERE MATCH (connector-(resides)->sheet-(belongs)->pnid)
                  AND pnid.Id = ?
        """
    cursor.execute(tsql, pnId)


def delete_sheet_ids_for_pid(cursor: pyodbc, pnId: str):
    '''
    Delete sheet node and its associate edges
    '''
    logger.debug(f'Deleting sheet node and its associate edges for {pnId}')
    tsql = """
        DELETE [pnide].[sheet]
            FROM [pnide].[sheet] as sheet,
                 [pnide].[belongs] as belongs,
                 [pnide].[pnid] as pnid
        WHERE MATCH (sheet-(belongs)->pnid)
              AND pnid.Id = ?
        """
    cursor.execute(tsql, pnId)


def delete_pnid(cursor: pyodbc, pnId: str):
    '''
    Delete PNID and its associated nodes and edges
    '''

    delete_asset_ids_for_pid(cursor, pnId)
    delete_connector_ids_for_pid(cursor, pnId)
    delete_sheet_ids_for_pid(cursor, pnId)

    # Finally, delete the PNID
    tsql = "DELETE FROM [pnide].[PNID] WHERE Id = ?"
    cursor.execute(tsql, pnId)
