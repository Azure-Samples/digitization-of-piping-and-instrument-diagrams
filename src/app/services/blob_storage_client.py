from app.config import Config, config
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential
from typing import Union
from logger_config import get_logger


logger = get_logger(__name__)


class BlobStorageClient:
    _container_client: Optional[ContainerClient] = None

    def __init__(self, config: Config = config, credential=DefaultAzureCredential()):
        '''Initializes a new instance of the BlobStorageClient class.

        :param config: The configuration to use
        :type config: Config
        :param credential: The credential to use
        :type credential: DefaultAzureCredential
        '''
        self._config = config
        self._credential = credential

    def throw_if_not_initialized(self):
        '''Throws an exception if the blob storage client is not initialized.'''
        if self._container_client is None:
            raise Exception('Blob storage client is not initialized')

    def upload_bytes(self, blob_name: str, image_bytes: Union[bytes, str]):
        '''Uploads the given bytes to the blob storage account.

        :param blob_name: The name of the blob to upload to
        :type blob_name: str
        :param image_bytes: The bytes to upload
        :type image_bytes: Union[bytes, str]
        '''
        logger.info(f'Uploading {blob_name} to blob storage')

        self.throw_if_not_initialized()
        blob_client = self._container_client.get_blob_client(blob_name)
        return blob_client.upload_blob(image_bytes, overwrite=True)

    def download_bytes(self, blob_name: str) -> bytes:
        '''Downloads the given blob from the blob storage account.

        :param blob_name: The name of the blob to download
        :type blob_name: str
        :return: The bytes of the blob
        :rtype: bytes
        '''
        logger.info(f'Downloading {blob_name} from blob storage')

        self.throw_if_not_initialized()
        blob_client = self._container_client.get_blob_client(blob_name)
        blob = blob_client.download_blob()

        return blob.readall()

    def blob_exists(self, blob_name: str) -> bool:
        '''Checks if the given blob exists in the blob storage account.

        :param blob_name: The name of the blob to check
        :type blob_name: str
        :return: True if the blob exists, False otherwise
        :rtype: bool
        '''
        logger.info(f'Checking if {blob_name} exists in blob storage')

        self.throw_if_not_initialized()
        return self._container_client.get_blob_client(blob_name).exists()

    def init(self):
        '''Initializes the blob storage client.'''
        blob_service_client = BlobServiceClient(
            self._config.blob_storage_account_url,
            self._credential
        )
        self._container_client = blob_service_client.get_container_client(self._config.blob_storage_container_name)


blob_storage_client = BlobStorageClient(config, DefaultAzureCredential())
