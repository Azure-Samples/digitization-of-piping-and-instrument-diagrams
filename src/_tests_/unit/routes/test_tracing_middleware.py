import sys
import os
import json
import pytest
from unittest.mock import Mock, AsyncMock, call
from fastapi import FastAPI, File, UploadFile
from starlette.testclient import TestClient
import unittest
from parameterized import parameterized

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.routes.tracing_middleware import TracingMiddleware
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse


# define all unit tests in TracingMiddleware
class TestTracingMiddleware(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.blob_storage_client_mock = Mock()
        self.blob_storage_client_mock.upload_bytes = Mock()
        self.app.add_middleware(TracingMiddleware, blob_storage_client=self.blob_storage_client_mock)

        @self.app.post("/api/pid-digitalization/symbol-detection/{id}")
        async def object_detection(id: str, file: UploadFile = File(...)):
            return { "predictions": [{ 'box': {'topX': 10, 'topY': 10, 'bottomX': 10, 'bottomY': 10}, 'label': '0', 'score': 0.5 }]}

        @self.app.post("/api/pid-digitalization/text-detection/{id}")
        async def text_detection(id: str, object_detection_result: SymbolDetectionInferenceResponse):
            return { "predictions": [{ 'box': {'topX': 10, 'topY': 10, 'bottomX': 10, 'bottomY': 10}, 'label': '0', 'score': 0.5 }]}

        self.client = TestClient(self.app)

    @parameterized.expand([('png'), ('jpg'), ('jpeg'), ('PNG'), ('JPG'), ('JPEG')])
    def test_dispatch_only_uploadfile(self, image_type):

        # act
        response = self.client.post("/api/pid-digitalization/symbol-detection/123", files={"file": (f"test.{image_type}", b"test")})

        # assert
        assert response.status_code == 200
        assert response.json() == { "predictions": [{ 'box': {'topX': 10, 'topY': 10, 'bottomX': 10, 'bottomY': 10}, 'label': '0', 'score': 0.5 }]}

        self.blob_storage_client_mock.upload_bytes.assert_has_calls([
            call("123/symbol-detection/123.png", b"test"),
            call('123/symbol-detection/response.json', '{"predictions":[{"box":{"topX":10,"topY":10,"bottomX":10,"bottomY":10},"label":"0","score":0.5}]}')
        ],
        any_order=True)


    def test_dispatch_only_uploadfile_invalid_image(self):

        # act
        response = self.client.post("/api/pid-digitalization/symbol-detection/123", files={"file": ("test.exe", b"test")})

        # assert
        assert response.status_code == 400

        self.blob_storage_client_mock.upload_bytes.assert_not_called()

    def test_dispatch_withno_uploadfile(self):
        # arrange
        json_payload = {
            "image_url": "123.png",
            "image_details": { "format": "png", "width": 100, "height": 100 },
            "label": [
                {'id': 1, 'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0, "label": "0", "score": 0.5}
            ]
        }

        # act
        response = self.client.post("/api/pid-digitalization/text-detection/123", json=json_payload)

        # assert
        assert response.status_code == 200
        assert response.json() == { "predictions": [{ 'box': {'topX': 10, 'topY': 10, 'bottomX': 10, 'bottomY': 10}, 'label': '0', 'score': 0.5 }]}

        expected_request = json.dumps(json_payload)
        expected_request = expected_request.encode('utf-8')
        self.blob_storage_client_mock.upload_bytes.assert_has_calls([
            call('123/text-detection/request.json',
                  expected_request),
            call('123/text-detection/response.json',
                 '{"predictions":[{"box":{"topX":10,"topY":10,"bottomX":10,"bottomY":10},"label":"0","score":0.5}]}')
            ],
            any_order=True)

    def test_dispatch_withno_id_matching_image_url(self):
        # arrange
        json_payload = {
            "image_url": "456.png",
            "image_details": { "format": "png", "width": 100, "height": 100 },
            "label": [
                {'id': 1, 'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0, "label": "0", "score": 0.5}
            ]
        }

        # act
        response = self.client.post("/api/pid-digitalization/text-detection/123", json=json_payload)

        # assert
        assert response.status_code == 400

        self.blob_storage_client_mock.upload_bytes.assert_not_called()
