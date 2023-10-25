import argparse
import time
import app.repository.connect as db
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
import logger_config
from app.models.graph_construction.graph_construction_response import GraphConstructionInferenceResponse
from .pnid_graph_db import PnidGraphDb
import traceback

logger = logger_config.get_logger(__name__)


def persist(pid_id: str, asset_connected: list[ConnectedSymbolsItem]):
    '''
    Persists the graph to the database. This method is called after the graph is constructed.
    :param pid_id: id of the pid
    :param asset_connected: list of connected assets
    '''
    logger.info(f'Persisting graph of pnid {pid_id} to database')
    performance_counter = time.perf_counter()
    cnxn = db.connect()
    cursor = cnxn.cursor()

    try:
        graphdb = PnidGraphDb(cursor)
        # step 1: delete existing graph
        logger.info(f'Deleting existing graph of pnid {pid_id} from database')
        graphdb.delete_existing_graph(pid_id)
        logger.info(f'Finished deleting existing graph of pnid {pid_id} from database')

        # step 2: create nodes and edges
        logger.info(f'Creating graph of pnid {pid_id} in database')
        graphdb.create_graph(pid_id, asset_connected)
        logger.info(f'Finished creating graph of pnid {pid_id} in database')

        cnxn.commit()
        logger.info(f'Finished persisting graph of pnid {pid_id} to database in {time.perf_counter() - performance_counter} seconds')

    except Exception as ex:
        logger.error(f'Error persisting graph of pnid {pid_id} to database: {ex}: stacktrace: {traceback.format_exc()}')
        cnxn.rollback()
        raise ex
    finally:
        cursor.close()
        cnxn.close()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pid-id',
        dest='pid_id',
        type=str,
        default='pid_sub1',
        help='PID ID'
    )
    parser.add_argument(
        '--graph-construction-path',
        dest='graph_construction_path',
        type=str,
        help='graph construction results path'
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()

    with open(args.graph_construction_path, 'r') as fline:
        results = fline.read()
        graph_construction_results = GraphConstructionInferenceResponse.parse_raw(results)

    persist(
        pid_id=args.pid_id,
        asset_connected=graph_construction_results.connected_symbols
    )
