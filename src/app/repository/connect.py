import pyodbc
import azure.identity as identity
import struct
from app.config import config
import logger_config


logger = logger_config.get_logger(__name__)


def connect():
    logger.info(f'Connecting to database using Azure AD authentication as {config.graph_db_authenticate_with_azure_ad}...')

    if config.graph_db_authenticate_with_azure_ad:
        credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
        token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
        cnxn = pyodbc.connect(config.graph_db_connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    else:
        cnxn = pyodbc.connect(config.graph_db_connection_string)

    logger.info('Connected')

    return cnxn
