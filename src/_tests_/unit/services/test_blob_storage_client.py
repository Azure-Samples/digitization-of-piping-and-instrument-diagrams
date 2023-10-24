import os
import unittest
from unittest.mock import MagicMock
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.services.blob_storage_client import BlobStorageClient


class TestUploadBytes(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path(self):
        # arrange
        async def mock_upload_blob(*args, **kwargs):
            return {'uploaded': True}

        blob_name = 'blob-name'
        bytes = b'bytes'

        blob_client = MagicMock()
        blob_client.upload_blob = MagicMock(wraps=mock_upload_blob)

        container_client = MagicMock()
        container_client.get_blob_client.return_value = blob_client
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())
        blob_storage_client._container_client = container_client

        # act
        await blob_storage_client.upload_bytes(blob_name, bytes)

        # assert
        container_client.get_blob_client.assert_called_once_with(blob_name)
        blob_client.upload_blob.assert_called_once_with(bytes, overwrite=True)

    async def test_blob_client_not_exists_throws_exception(self):
        # arrange
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())

        # act
        with self.assertRaises(Exception) as e:
            await blob_storage_client.upload_bytes('blob-name', b'bytes')

        # assert
        self.assertEqual(str(e.exception), 'Blob storage client is not initialized')


class TestDownloadBytes(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path(self):
        # arrange
        async def mock_readall(*args, **kwargs):
            return b'bytes'

        def mock_download_blob(*args, **kwargs):
            blob = MagicMock()
            blob.readall = MagicMock(wraps=mock_readall)
            return blob

        blob_name = 'blob-name'

        blob_client = MagicMock()
        blob_client.download_blob = MagicMock(wraps=mock_download_blob)

        container_client = MagicMock()
        container_client.get_blob_client.return_value = blob_client
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())
        blob_storage_client._container_client = container_client

        # act
        result = await blob_storage_client.download_bytes(blob_name)

        # assert
        container_client.get_blob_client.assert_called_once_with(blob_name)
        blob_client.download_blob.assert_called_once_with()
        self.assertEqual(result, b'bytes')

    async def test_blob_client_not_exists_throws_exception(self):
        # arrange
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())

        # act
        with self.assertRaises(Exception) as e:
            await blob_storage_client.download_bytes('blob-name')

        # assert
        self.assertEqual(str(e.exception), 'Blob storage client is not initialized')


class TestBlobExists(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path(self):
        # arrange
        async def mock_exists(*args, **kwargs):
            return True

        blob_name = 'blob-name'

        blob_client = MagicMock()
        blob_client.exists = MagicMock(wraps=mock_exists)

        container_client = MagicMock()
        container_client.get_blob_client.return_value = blob_client
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())
        blob_storage_client._container_client = container_client

        # act
        result = await blob_storage_client.blob_exists(blob_name)

        # assert
        container_client.get_blob_client.assert_called_once_with(blob_name)
        blob_client.exists.assert_called_once_with()
        self.assertEqual(result, True)

    
    async def test_blob_client_not_exists_throws_exception(self):
        # arrange
        blob_storage_client = BlobStorageClient(MagicMock(), MagicMock())

        # act
        with self.assertRaises(Exception) as e:
            await blob_storage_client.blob_exists('blob-name')

        # assert
        self.assertEqual(str(e.exception), 'Blob storage client is not initialized')
