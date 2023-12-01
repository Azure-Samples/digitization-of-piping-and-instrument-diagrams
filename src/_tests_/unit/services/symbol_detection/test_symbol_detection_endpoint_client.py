# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
from unittest.mock import MagicMock
import pytest
from requests import HTTPError
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.symbol_detection.symbol_detection_endpoint_client import SymbolDetectionEndpointClient


class TestSendRequest(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        bearer_token = 'bearer-token'

        config = MagicMock()
        config.symbol_detection_api = 'http://inference-endpoint'
        config.symbol_detection_api_bearer_token = bearer_token
        session = MagicMock()
        session.post.return_value = MagicMock()
        session.post.return_value.json.return_value = { 'predictions': [] }
        session.post.return_value.raise_for_status.return_value = None
        symbol_detection_endpoint_client = SymbolDetectionEndpointClient(config, session)

        # act
        response = symbol_detection_endpoint_client.send_request(b'image-bytes')

        # assert
        session.post.assert_called_once_with(
            'http://inference-endpoint/score',
            files={ 'image': b'image-bytes' },
            headers={ 'Authorization': f'Bearer {bearer_token}' })
        self.assertEqual(response, { 'predictions': [] })

    def test_raises_http_error_when_response_status_code_is_400(self):
        # arrange
        bearer_token = 'bearer-token'
        error = HTTPError('error')

        config = MagicMock()
        config.symbol_detection_api = 'http://inference-endpoint'
        config.symbol_detection_api_bearer_token = bearer_token
        session = MagicMock()
        session.post.return_value = MagicMock()
        session.post.return_value.raise_for_status.side_effect = error
        symbol_detection_endpoint_client = SymbolDetectionEndpointClient(config, session)

        # act
        with pytest.raises(HTTPError) as e:
            symbol_detection_endpoint_client.send_request(b'image-bytes')

        # assert
        session.post.assert_called_once_with(
            'http://inference-endpoint/score',
            files={ 'image': b'image-bytes' },
            headers={ 'Authorization': f'Bearer {bearer_token}' })
        self.assertEqual(e.value, error)


class TestCheckHealth(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        bearer_token = 'bearer-token'

        config = MagicMock()
        config.symbol_detection_api = 'http://inference-endpoint'
        config.symbol_detection_api_bearer_token = bearer_token
        session = MagicMock()
        session.get.return_value.raise_for_status.return_value = None
        symbol_detection_endpoint_client = SymbolDetectionEndpointClient(config, session)

        # act
        response = symbol_detection_endpoint_client.check_health()

        # assert
        session.get.assert_called_once_with(
            'http://inference-endpoint',
            headers={ 'Authorization': f'Bearer {bearer_token}' })
        self.assertTrue(response)

    def test_returns_false_when_health_check_raises_http_error(self):
        # arrange
        bearer_token = 'bearer-token'

        config = MagicMock()
        config.symbol_detection_api = 'http://inference-endpoint'
        config.symbol_detection_api_bearer_token = bearer_token
        session = MagicMock()
        session.get.return_value.raise_for_status.side_effect = HTTPError('error')
        symbol_detection_endpoint_client = SymbolDetectionEndpointClient(config, session)

        # act
        response = symbol_detection_endpoint_client.check_health()

        # assert
        session.get.assert_called_once_with(
            'http://inference-endpoint',
            headers={ 'Authorization': f'Bearer {bearer_token}' })
        self.assertFalse(response)
