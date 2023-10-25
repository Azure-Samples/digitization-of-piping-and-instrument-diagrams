import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest
from requests import HTTPError
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from app.services.symbol_detection.symbol_detection_service  import run_inferencing
from app.models.bounding_box import BoundingBox


class TestRunInferencing(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_returns_bounding_boxes(self):
        # arrange
        async def mock_upload_bytes_coroutine(*args):
            return {}

        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5

        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(topX=0.1, topY=0.1, bottomX=1, bottomY=1)

        boxes = [
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.0 },
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.5 },
            { 'box': {'topX': 0.1, 'topY': 0.1, 'bottomX': 0.1, 'bottomY': 0.1}, 'label': '0', 'score': 0.5 },
            { 'box': {'topX': 0.2, 'topY': 0.2, 'bottomX': 0.2, 'bottomY': 0.2}, 'label': '0', 'score': 0.6 }
        ]

        symbol_detection_endpoint_client = MagicMock()
        symbol_detection_endpoint_client.send_request = MagicMock(return_value={'boxes': boxes})

        blob_storage_client = MagicMock()
        blob_storage_client.upload_bytes = MagicMock(wraps=mock_upload_bytes_coroutine)

        get_image_dimensions = MagicMock(return_value=(100, 100))

        cv2_imwrite = MagicMock()

        # act
        with patch("app.services.symbol_detection.symbol_detection_service.symbol_detection_endpoint_client", symbol_detection_endpoint_client), \
            patch("app.services.symbol_detection.symbol_detection_service.image_utils.get_image_dimensions", get_image_dimensions), \
             patch("cv2.imwrite", cv2_imwrite):
            result = await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert result == {
            'image_url': f'{pid_id}.png',
            'image_details': {
                'width': 100,
                'height': 100,
                'format': 'png'
            },
            'bounding_box_inclusive': {'topX': 0.1, 'topY': 0.1, 'bottomX': 1.0, 'bottomY': 1.0},
            'label': [
                {'id': 0, 'topX': 0.1, 'topY': 0.1, 'bottomX': 0.1, 'bottomY': 0.1, 'label': '0', 'score': 0.5},
                {'id': 1, 'topX': 0.2, 'topY': 0.2, 'bottomX': 0.2, 'bottomY': 0.2, 'label': '0', 'score': 0.6}
            ]
        }
        cv2_imwrite.assert_called_once_with(image_path, None)

    async def test_happy_path_with_draw_bounding_boxes_returns_bounding_boxes(self):
        # arrange
        async def mock_upload_bytes_coroutine(*args):
            return {}

        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5
        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(topX=0.1, topY=0.1, bottomX=1, bottomY=1)

        boxes = [
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.0 },
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.5 },
            { 'box': {'topX': 0.1, 'topY': 0.1, 'bottomX': 0.1, 'bottomY': 0.1}, 'label': '0', 'score': 0.5 },
            { 'box': {'topX': 0.2, 'topY': 0.2, 'bottomX': 0.2, 'bottomY': 0.2}, 'label': '0', 'score': 0.6 }
        ]

        symbol_detection_endpoint_client = MagicMock()
        symbol_detection_endpoint_client.send_request = MagicMock(return_value={'boxes': boxes})

        blob_storage_client = MagicMock()
        blob_storage_client.upload_bytes = MagicMock(wraps=mock_upload_bytes_coroutine)

        draw_bounding_boxes = MagicMock()
        draw_bounding_boxes.return_value = b'123'

        get_image_dimensions = MagicMock(return_value=(100, 100))

        cv2_imwrite = MagicMock()

        # act
        with patch("app.services.symbol_detection.symbol_detection_service.symbol_detection_endpoint_client", symbol_detection_endpoint_client), \
            patch("app.services.symbol_detection.symbol_detection_service.image_utils.get_image_dimensions", get_image_dimensions), \
            patch("app.services.symbol_detection.symbol_detection_service.draw_bounding_boxes", draw_bounding_boxes), \
             patch("cv2.imwrite", cv2_imwrite):
            result = await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert result == {
            'image_url': f'{pid_id}.png',
            'image_details': {
                'width': 100,
                'height': 100,
                'format': 'png'
            },
            'bounding_box_inclusive': {'topX': 0.1, 'topY': 0.1, 'bottomX': 1.0, 'bottomY': 1.0},
            'label': [
                {'id': 0, 'topX': 0.1, 'topY': 0.1, 'bottomX': 0.1, 'bottomY': 0.1, 'label': '0', 'score': 0.5},
                {'id': 1, 'topX': 0.2, 'topY': 0.2, 'bottomX': 0.2, 'bottomY': 0.2, 'label': '0', 'score': 0.6}
            ]
        }
        cv2_imwrite.assert_called_once_with(image_path, b'123')


    async def test_happy_path_with_draw_bounding_boxes_throws_exception_returns_bounding_boxes(self):
        # arrange
        async def mock_upload_bytes_coroutine(*args):
            return {}

        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5
        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.0, bottomX=1.0, bottomY=1.0)

        boxes = [
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.0 },
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.5 },
            { 'box': {'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0}, 'label': '0', 'score': 0.6 }
        ]

        symbol_detection_endpoint_client = MagicMock()
        symbol_detection_endpoint_client.send_request = MagicMock(return_value={'boxes': boxes})

        blob_storage_client = MagicMock()
        blob_storage_client.upload_bytes = MagicMock(wraps=mock_upload_bytes_coroutine)

        draw_bounding_boxes = MagicMock()
        draw_bounding_boxes.return_value = b'123'

        get_image_dimensions = MagicMock(return_value=(100, 100))

        cv2_imwrite = MagicMock(side_effect=Exception('error'))

        # act
        with patch("app.services.symbol_detection.symbol_detection_service.symbol_detection_endpoint_client", symbol_detection_endpoint_client), \
            patch("app.services.symbol_detection.symbol_detection_service.image_utils.get_image_dimensions", get_image_dimensions), \
            patch("app.services.symbol_detection.symbol_detection_service.draw_bounding_boxes", draw_bounding_boxes), \
             patch("cv2.imwrite", cv2_imwrite):
            result = await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert result == {
            'image_url': f'{pid_id}.png',
            'image_details': {
                'width': 100,
                'height': 100,
                'format': 'png'
            },
            'bounding_box_inclusive': {'topX': 0.0, 'topY': 0.0, 'bottomX': 1.0, 'bottomY': 1.0},
            'label': [
                {'id': 0, 'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0, 'label': '0', 'score': 0.5},
                {'id': 1, 'topX': 0, 'topY': 0, 'bottomX': 0, 'bottomY': 0, 'label': '0', 'score': 0.6}
            ]
        }
        cv2_imwrite.assert_called_once_with(image_path, b'123')


    async def test_symbol_detection_client_throws_exception_raises_http_exception(self):
        # arrange
        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5
        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(bottomX=0.0, bottomY=0.0, topX=1.0, topY=1.0)

        symbol_detection_endpoint_client = MagicMock()
        symbol_detection_endpoint_client.send_request = MagicMock(side_effect=Exception('error'))

        # act
        with patch("app.services.symbol_detection.symbol_detection_endpoint_client", symbol_detection_endpoint_client):
            with pytest.raises(HTTPException) as e:
                await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert e.value.status_code == 500
        assert e.value.detail == 'Internal server error while fetching the symbol detection results.'

    async def test_symbol_detection_client_throws_http_error_400_raises_http_exception(self):
        # arrange
        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5
        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(bottomX=0.0, bottomY=0.0, topX=1.0, topY=1.0)

        symbol_detection_endpoint_client = MagicMock()
        http_error = HTTPError(response=MagicMock(status_code=400, text='error'))
        symbol_detection_endpoint_client.send_request = MagicMock(side_effect=http_error)

        # act
        with patch("app.services.symbol_detection.symbol_detection_service.symbol_detection_endpoint_client", symbol_detection_endpoint_client):
            with pytest.raises(HTTPException) as e:
                await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert e.value.status_code == 400
        assert e.value.detail == 'error'

    async def test_symbol_detection_client_throws_http_error_500_raises_http_exception(self):
        # arrange
        pid_id = '123'
        image = b'image'
        inference_score_threhshold = 0.5
        image_path = '123/images/123.jpg'

        bounding_box_inclusive = BoundingBox(bottomX=0.0, bottomY=0.0, topX=1.0, topY=1.0)

        symbol_detection_endpoint_client = MagicMock()
        http_error = HTTPError(response=MagicMock(status_code=500, text='error'))
        symbol_detection_endpoint_client.send_request = MagicMock(side_effect=http_error)

        # act
        with patch("app.services.symbol_detection.symbol_detection_service.symbol_detection_endpoint_client", symbol_detection_endpoint_client):
            with pytest.raises(HTTPException) as e:
                await run_inferencing(pid_id, bounding_box_inclusive, inference_score_threhshold, image, image_path)

        # assert
        assert e.value.status_code == 500
        assert e.value.detail == 'There was an error while fetching the symbol detection results.'
