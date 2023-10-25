import os
import unittest
from unittest.mock import MagicMock, patch, call
from parameterized import parameterized
from fastapi import HTTPException
import pytest
import sys
import datetime

from app.models.graph_construction.graph_construction_response import GraphConstructionInferenceResponse

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.routes.controllers.pid_digitization_controller import detect_symbols, detect_text, \
    detect_lines_and_construct_graph, process_line_detection_and_graph_construction_job,\
    process_line_detection, get_inference_results, get_job_status, get_output_inference_images,\
    persist_graph
from app.models.enums.inference_result import InferenceResult
from app.models.bounding_box import BoundingBox
from app.models.graph_construction.graph_construction_request import GraphConstructionInferenceRequest
from app.models.line_detection.line_detection_response import LineDetectionInferenceResponse
import app.queue_consumer as queue_consumer
from app.models.bounding_box import BoundingBox
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.bounding_box import BoundingBox
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.image_response import ImageResponse
import json


class TestDetectSymbols(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_returns_bounding_boxes(self):
        # arrange
        async def mock_image_read(*args):
            return b'123'

        async def mock_run_inferencing(*args):
            return {'label': []}

        pid_id = '123'
        image = MagicMock()
        image.read = MagicMock(wraps=mock_image_read)

        run_inferencing = MagicMock(wraps=mock_run_inferencing)

        output_image_path = '123/images/output_123_symbol-detection.png'
        build_output_image_path = MagicMock(return_value=output_image_path)

        bounding_box_inclusive = {'topX': 0.0, 'topY': 0.0, 'bottomX': 1.0, 'bottomY': 1.0}  # Represents mapping after deserialization from JSON input

        config = MagicMock()
        config.inference_score_threshold = 0.5

        # act
        with patch("app.routes.controllers.pid_digitization_controller.symbol_detection.run_inferencing", run_inferencing), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_output_image_path",
                  build_output_image_path), \
             patch("app.routes.controllers.pid_digitization_controller.config", config):
            result = await detect_symbols(pid_id, bounding_box_inclusive, image)

        # assert
        assert result == {'label': []}
        build_output_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection, InferenceResult.symbol_detection.value)
        run_inferencing.assert_called_once_with('123', bounding_box_inclusive, 0.5, b'123', output_image_path)

    async def test_invalid_bounding_box_inclusive_throws_http_exception(self):
        # arrange
        async def mock_image_read(*args):
            return b'123'

        async def mock_run_inferencing(*args):
            return {'label': []}

        pid_id = '123'
        image = MagicMock()
        image.read = MagicMock(wraps=mock_image_read)

        run_inferencing = MagicMock(wraps=mock_run_inferencing)

        debug_image_path = '123/images/debug_123.jpg'
        build_debug_image_path = MagicMock(return_value=debug_image_path)

        bounding_box_inclusive = {'topX': 0.0, 'topY': 0.0, 'bottomX': 2.0, 'bottomY': 2.0}

        config = MagicMock()
        config.inference_score_threshold = 0.5

        # act
        with patch("app.routes.controllers.pid_digitization_controller.symbol_detection.run_inferencing", run_inferencing), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_debug_image_path", build_debug_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.config", config):
            with pytest.raises(HTTPException) as e:
                await detect_symbols(pid_id, bounding_box_inclusive, image)

        # assert
        assert e.value.status_code == 400
        assert e.value.detail == f'The bounding_box_inclusive_str JSON string value provided for P&ID image {pid_id} is invalid. Make sure that all coordinates (topX, topY, bottomX, bottomY) are present and in the range [0, 1].'


class TestDetectText(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_returns_text(self):
        # arrange
        def mock_run_inferencing(*args):
            return {'all_text_list': [], 'text_and_symbols_associated_list': []}

        def mock_blob_exists(*args):
            return True

        def mock_download_bytes(*args):
            return b'123'

        pid_id = '123'
        corrected_symbol_detection_results = SymbolDetectionInferenceResponse(**{
            'label': [],
            'image_url': '123/images/123.jpg',
            'image_details': {
                'width': 100,
                'height': 100}})

        run_inferencing = MagicMock(wraps=mock_run_inferencing)

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        debug_image_path = '123/images/debug_123_1.jpg'
        build_debug_image_path = MagicMock(return_value=debug_image_path)

        output_image_path = '123/images/output_123_2.jpg'
        build_output_image_path = MagicMock(return_value=output_image_path)

        config = MagicMock()
        config.inference_score_threshold = 0.5
        config.symbol_label_prefixes_with_text = '1,2'
        config.text_detection_area_intersection_ratio_threshold = 0.7
        config.text_detection_distance_threshold = 0.02

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(wraps=mock_blob_exists)
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.text_detection.run_inferencing", run_inferencing), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_debug_image_path", build_debug_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_output_image_path", build_output_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
             patch("app.routes.controllers.pid_digitization_controller.config", config):
            result = await detect_text(pid_id, corrected_symbol_detection_results)

        # assert
        assert result == {'all_text_list': [], 'text_and_symbols_associated_list': []}
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_debug_image_path.assert_called_once_with(pid_id, InferenceResult.text_detection, 'text')
        build_output_image_path.assert_called_once_with(pid_id, InferenceResult.text_detection, InferenceResult.text_detection.value)

        run_inferencing.assert_called_once_with('123', corrected_symbol_detection_results, b'123', 0.7, 0.02, '1,2',
                                                '123/images/debug_123_1.jpg', '123/images/output_123_2.jpg')

    async def test_file_not_exists_throws_http_exception(self):
        # arrange
        def mock_blob_exists(*args):
            return False

        pid_id = '123'
        corrected_symbol_detection_results = {'label': []}

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        blob_exists = MagicMock(wraps=mock_blob_exists)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.blob_storage_client.blob_exists", blob_exists), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path):
            with pytest.raises(HTTPException) as e:
                await detect_text(pid_id, corrected_symbol_detection_results)

        # assert
        assert e.value.status_code == 422
        assert e.value.detail == 'Pid image 123 does not exist. Run symbol detection first.'

    async def test_invalid_bounding_box_inclusive_throws_http_exception(self):
        # arrange
        def mock_blob_exists(*args):
            return True

        pid_id = '123'
        corrected_symbol_detection_results = SymbolDetectionInferenceResponse(**{
            'label': [],
            'bounding_box_inclusive': {
                'topX': 0.0,
                'topY': 0.0,
                'bottomX': 2.0,
                'bottomY': 2.0},
            'image_url': '123/images/123.jpg',
            'image_details': {
                'width': 100,
                'height': 100}})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        blob_exists = MagicMock(wraps=mock_blob_exists)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.blob_storage_client.blob_exists", blob_exists), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path):
            with pytest.raises(HTTPException) as e:
                await detect_text(pid_id, corrected_symbol_detection_results)

        # assert
        assert e.value.status_code == 400
        assert e.value.detail == f'The bounding_box_inclusive value provided for P&ID image {pid_id} is invalid. Make sure that coordinates are normalized and in the range [0, 1].'


class TestGraphConstruction(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_submits_job(self):

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'thinning_enabled': True, 'hough_threshold': 10, 'hough_max_line_gap': 5, 'hough_min_line_length': 20, 'bounding_box_inclusive': None, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, False, False])

        config = MagicMock()
        config.line_detection_job_timeout_seconds = 300

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 0, 0))

        queue = MagicMock()

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
             patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
             patch("app.routes.controllers.pid_digitization_controller.config", config), \
             patch("app.routes.controllers.pid_digitization_controller.datetime", dt), \
             patch("app.queue_consumer._queue", queue):
            result = await detect_lines_and_construct_graph(pid_id, corrected_text_detection_results)

        # assert
        assert result == {'message': 'Graph construction job submitted successfully.'}
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)

        blob_storage_client.upload_bytes.assert_called_once_with(job_status_path, '{"status": "submitted", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:00"}')
        queue.put.assert_called_once_with((process_line_detection_and_graph_construction_job,
                                           ('123', corrected_text_detection_results,)))

    async def test_invalid_bounding_box_inclusive_throws_http_exception(self):
        # arrange
        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{
            'all_text_list': [],
            'text_and_symbols_associated_list': [],
            'thinning_enabled': True,
            'hough_threshold': 10,
            'hough_max_line_gap': 5,
            'hough_min_line_length': 20,
            'bounding_box_inclusive': {
                'topX': 0.0,
                'topY': 0.0,
                'bottomX': 2.0,
                'bottomY': 2.0},
            'image_details': {'height': 100, 'width': 100},
            'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])

        config = MagicMock()
        config.line_detection_job_timeout_seconds = 300

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 0, 0))

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
            patch("app.routes.controllers.pid_digitization_controller.config", config), \
            patch("app.routes.controllers.pid_digitization_controller.datetime", dt):
            with pytest.raises(HTTPException) as e:
                await detect_lines_and_construct_graph(pid_id, corrected_text_detection_results)

        # assert
        assert e.value.status_code == 400
        assert e.value.detail == f'The bounding_box_inclusive value provided for P&ID image {pid_id} is invalid. Make sure that coordinates are normalized and in the range [0, 1].'

    async def test_submits_job_job_file_exists_conflict(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"status": "submitted", "step": "line_detection", "updated_at": "2020-06-25 00:05:00"}'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'thinning_enabled': True, 'hough_threshold': 10, 'hough_max_line_gap': 5, 'hough_min_line_length': 20, 'bounding_box_inclusive': None, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        config = MagicMock()
        config.line_detection_job_timeout_seconds = 300

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 0, 0))

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
            patch("app.routes.controllers.pid_digitization_controller.config", config), \
            patch("app.routes.controllers.pid_digitization_controller.datetime", dt):
            with pytest.raises(HTTPException) as e:
                await detect_lines_and_construct_graph(pid_id, corrected_text_detection_results)

        # assert
        assert e.value.status_code == 409
        assert e.value.detail == 'Graph construction job already exists for pid id 123.'


    async def test_submits_job_job_file_exists_conflict_with_timeout(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"status": "submitted", "step": "line_detection", "updated_at": "2020-06-25 00:05:00"}'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'thinning_enabled': True, 'hough_threshold': 10, 'hough_max_line_gap': 5, 'hough_min_line_length': 20, 'bounding_box_inclusive': None, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        config = MagicMock()
        config.line_detection_job_timeout_seconds = 300

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 1, 0))

        queue = MagicMock()

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
             patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
             patch("app.routes.controllers.pid_digitization_controller.config", config), \
             patch("app.routes.controllers.pid_digitization_controller.datetime", dt), \
             patch("app.queue_consumer._queue", queue):
            result = await detect_lines_and_construct_graph(pid_id, corrected_text_detection_results)

        # assert
        assert result == {'message': 'Graph construction job submitted successfully.'}
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)

        blob_storage_client.upload_bytes.assert_called_once_with(job_status_path, '{"status": "submitted", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}')

        queue.put.assert_called_once_with((process_line_detection_and_graph_construction_job, ('123', corrected_text_detection_results,)))

    async def test_submits_job_job_file_exists_no_conflict(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"status": "failure", "step": "line_detection", "updated_at": "2020-06-25 00:05:00"}'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'thinning_enabled': True, 'hough_threshold': 10, 'hough_max_line_gap': 5, 'hough_min_line_length': 20, 'bounding_box_inclusive': None, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        config = MagicMock()
        config.line_detection_job_timeout_seconds = 300

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 1, 0))

        queue = MagicMock()

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
             patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
             patch("app.routes.controllers.pid_digitization_controller.config", config), \
             patch("app.routes.controllers.pid_digitization_controller.datetime", dt), \
             patch("app.queue_consumer._queue", queue):
            result = await detect_lines_and_construct_graph(pid_id, corrected_text_detection_results)

        # assert
        assert result == {'message': 'Graph construction job submitted successfully.'}
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)

        blob_storage_client.upload_bytes.assert_called_once_with(job_status_path, '{"status": "submitted", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}')
        queue.put.assert_called_once_with((process_line_detection_and_graph_construction_job, ('123', corrected_text_detection_results,)))

    async def test_happy_path_process_line_detection_default_parameters(self):
        # arrange
        def mock_detect_lines(*args):
            return LineDetectionInferenceResponse(**{'line_segments': [], 'line_segments_count': 0, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        def mock_download_bytes(*args):
            return b'123'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        response_path = '123/graph_construction/response.json'
        build_response_path = MagicMock(return_value=response_path)

        debug_image_path = ['123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg',
                            '123/images/debug_123_line_segments.jpg']
        build_debug_image_path = MagicMock(side_effect=debug_image_path)

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        detect_lines = MagicMock(wraps=mock_detect_lines)

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 1, 0))

        config = MagicMock()
        config.enable_thinning_preprocessing_line_detection = True
        config.line_detection_hough_threshold = 5
        config.detect_dotted_lines = False
        config.line_detection_hough_max_line_gap = None
        config.line_detection_hough_min_line_length = 5
        config.line_detection_hough_rho = 0.1
        config.line_detection_hough_theta = 1080
        config.line_detection_job_timeout_seconds = 300


        # act
        with patch("app.routes.controllers.pid_digitization_controller.line_detection.detect_lines", detect_lines), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_debug_image_path", build_debug_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_response_path", build_response_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
            patch("app.routes.controllers.pid_digitization_controller.config", config), \
            patch("app.routes.controllers.pid_digitization_controller.datetime", dt):
            process_line_detection(pid_id, corrected_text_detection_results)

        # assert
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)
        build_response_path.assert_called_with(pid_id, InferenceResult.graph_construction, InferenceResult.line_detection.value)
        blob_storage_client.download_bytes.assert_called_once_with(image_path)
        blob_storage_client.upload_bytes.assert_has_calls([
            call(job_status_path, '{"status": "in_progress", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}'),
            call(response_path, '{"image_url": "123.png", "image_details": {"format": "png", "width": 100, "height": 100}, "line_segments_count": 0, "line_segments": []}'),
            call(job_status_path, '{"status": "done", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}'),
        ])

        detect_lines.assert_called_once_with(pid_id, b'123', corrected_text_detection_results, True, 5, None, 5, 0.1, 1080, None, 100, 100, '123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg', '123/graph-construction/output_123_line-detection.png')


    async def test_happy_path_process_line_detection_non_default_parameters(self):
        # arrange
        def mock_detect_lines(*args):
            return LineDetectionInferenceResponse(**{'line_segments': [], 'line_segments_count': 0, 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        def mock_download_bytes(*args):
            return b'123'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'thinning_enabled': False, 'hough_threshold': 10, 'hough_max_line_gap': 5, 'hough_min_line_length': 10, 'hough_rho': 0.2, 'hough_theta': 360, 'bounding_box_inclusive': {'topX': 0.2, 'topY': 0.2, 'bottomX': 0.8, 'bottomY': 0.8}, 'image_details': {'height': 100, 'width': 100}, 'image_url': '1.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        response_path = '123/graph_construction/response.json'
        build_response_path = MagicMock(return_value=response_path)

        debug_image_path = ['123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg', '123/images/debug_123_line_segments.jpg']
        build_debug_image_path = MagicMock(side_effect=debug_image_path)

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        detect_lines = MagicMock(wraps=mock_detect_lines)

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 1, 0))

        config = MagicMock()
        config.enable_thinning_preprocessing_line_detection = True
        config.detect_dotted_lines = False
        config.line_detection_hough_threshold = 5
        config.line_detection_hough_max_line_gap = None
        config.line_detection_hough_min_line_length = 15
        config.line_detection_hough_rho = 0.1
        config.line_detection_hough_theta = 1080
        config.line_detection_job_timeout_seconds = 300


        # act
        with patch("app.routes.controllers.pid_digitization_controller.line_detection.detect_lines", detect_lines), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_debug_image_path", build_debug_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_response_path", build_response_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
            patch("app.routes.controllers.pid_digitization_controller.config", config), \
            patch("app.routes.controllers.pid_digitization_controller.datetime", dt):
            process_line_detection(pid_id, corrected_text_detection_results)

        # assert
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)
        build_response_path.assert_called_with(pid_id, InferenceResult.graph_construction, InferenceResult.line_detection.value)
        blob_storage_client.download_bytes.assert_called_once_with(image_path)
        blob_storage_client.upload_bytes.assert_has_calls([
            call(job_status_path, '{"status": "in_progress", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}'),
            call(response_path, '{"image_url": "123.png", "image_details": {"format": "png", "width": 100, "height": 100}, "line_segments_count": 0, "line_segments": []}'),
            call(job_status_path, '{"status": "done", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}'),
        ])

        detect_lines.assert_called_once_with(pid_id, b'123', corrected_text_detection_results, False, 10, None, 15, 0.2, 360, BoundingBox(topX=0.2, topY=0.2, bottomX=0.8, bottomY=0.8), 100, 100, '123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg', '123/graph-construction/output_123_line-detection.png')


    async def test_process_line_detection_failure_status(self):
        # arrange
        def mock_download_bytes(*args):
            return b'123'

        pid_id = '123'
        corrected_text_detection_results = GraphConstructionInferenceRequest(**{'all_text_list': [], 'text_and_symbols_associated_list': [], 'image_details': {'height': 100, 'width': 100}, 'image_url': '123.png'})

        image_path = '123/images/123.jpg'
        build_image_path = MagicMock(return_value=image_path)

        job_status_path = '123/graph_construction/job_status.json'
        build_job_status_path = MagicMock(return_value=job_status_path)

        response_path = '123/graph_construction/response.json'
        build_response_path = MagicMock(return_value=response_path)

        debug_image_path = ['123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg', '123/images/debug_123_line_segments.jpg']
        build_debug_image_path = MagicMock(side_effect=debug_image_path)

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)

        detect_lines = MagicMock(side_effect=Exception('Error during line detection'))

        dt = MagicMock()
        dt.utcnow = MagicMock(return_value=datetime.datetime(2020, 6, 25, 0, 10, 1, 0))

        config = MagicMock()
        config.enable_thinning_preprocessing_line_detection = True
        config.detect_dotted_lines = False
        config.line_detection_hough_threshold = 5
        config.line_detection_hough_max_line_gap = None
        config.line_detection_hough_min_line_length = 5
        config.line_detection_hough_rho = 0.1
        config.line_detection_hough_theta = 1080
        config.line_detection_job_timeout_seconds = 300

        # act
        with patch("app.routes.controllers.pid_digitization_controller.line_detection.detect_lines", detect_lines), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_image_path", build_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_debug_image_path", build_debug_image_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_job_status_path", build_job_status_path), \
            patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder.build_inference_response_path", build_response_path), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client), \
            patch("app.routes.controllers.pid_digitization_controller.config", config), \
            patch("app.routes.controllers.pid_digitization_controller.datetime", dt):
            process_line_detection(pid_id, corrected_text_detection_results)

        # assert
        build_image_path.assert_called_once_with(pid_id, InferenceResult.symbol_detection)
        build_job_status_path.assert_called_with(pid_id, InferenceResult.graph_construction)
        build_response_path.assert_not_called()
        blob_storage_client.download_bytes.assert_called_once_with(image_path)
        blob_storage_client.upload_bytes.assert_has_calls([
            call(job_status_path, '{"status": "in_progress", "step": "line_detection", "message": null, "updated_at": "2020-06-25 00:10:01"}'),
            call(job_status_path, '{"status": "failure", "step": "line_detection", "message": "Error during line detection", "updated_at": "2020-06-25 00:10:01"}'),
        ])

        detect_lines.assert_called_once_with(pid_id, b'123', corrected_text_detection_results, True, 5, None, 5, 0.1, 1080, None, 100, 100, '123/images/debug_123_preprocessed.jpg', '123/images/debug_123_preprocessed_before_thinning.jpg', '123/graph-construction/output_123_line-detection.png')


class TestGetInference(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_symbol_detection_returns_inference_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"box": {}, "label": "1", "score": 0.9}'

        pid_id = '123'
        inference_result_type = InferenceResult.symbol_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_request_path = MagicMock(return_value='123/inference_results/123.json')
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[False, True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {'box': {}, 'label': '1', 'score': 0.9}
        assert blob_storage_client.blob_exists.call_count == 2
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_request_path.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 1


    async def test_happy_path_symbol_detection_returns_corrected_inference_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"box": {}, "label": "1", "score": 0.9}'

        pid_id = '123'
        inference_result_type = InferenceResult.symbol_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_request_path = MagicMock(return_value='123/inference_results/123.json')
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {'box': {}, 'label': '1', 'score': 0.9}
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_request_path.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 0

    async def test_happy_path_text_detection_returns_inference_results(self):

        # arrange
        def mock_download_bytes(*args):
            return b'{"all_text_list": [{"topX": 0.08, "topY": 0.05, "bottomX": 0.88, "bottomY": 0.06, "text": "NOTES"}], "text_and_symbols_associated_list": [{"topX": 0.53, "topY": 0.54, "bottomX": 0.54, "bottomY": 0.55, "id": 21, "label": "9", "text_associated": "QR-66651"} ]}'

        pid_id = '123'
        inference_result_type = InferenceResult.text_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_request_path = MagicMock(return_value='123/inference_results/123.json')
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[False, True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {"all_text_list": [{"topX": 0.08, "topY": 0.05, "bottomX": 0.88, "bottomY": 0.06, "text": "NOTES"}], "text_and_symbols_associated_list": [{"topX": 0.53, "topY": 0.54, "bottomX": 0.54, "bottomY": 0.55, "id": 21, "label": "9", "text_associated": "QR-66651"} ]}
        assert blob_storage_client.blob_exists.call_count == 2
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_request_path.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 1

    async def test_happy_path_text_detection_returns_corrected_inference_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"all_text_list": [{"topX": 0.08, "topY": 0.05, "bottomX": 0.88, "bottomY": 0.06, "text": "NOTES"}], "text_and_symbols_associated_list": [{"topX": 0.53, "topY": 0.54, "bottomX": 0.54, "bottomY": 0.55, "id": 21, "label": "9", "text_associated": "QR-66651"} ]}'

        pid_id = '123'
        inference_result_type = InferenceResult.text_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_request_path = MagicMock(return_value='123/inference_results/123.json')
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {"all_text_list": [{"topX": 0.08, "topY": 0.05, "bottomX": 0.88, "bottomY": 0.06, "text": "NOTES"}], "text_and_symbols_associated_list": [{"topX": 0.53, "topY": 0.54, "bottomX": 0.54, "bottomY": 0.55, "id": 21, "label": "9", "text_associated": "QR-66651"} ]}
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_request_path.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 0

    async def test_happy_path_line_detection_returns_inference_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"line_segments": [{"startX": 0.10, "startY": 0.91, "endX": 0.1018363939899833, "endY": 0.99}]}'

        pid_id = '123'
        inference_result_type = InferenceResult.line_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {"line_segments": [{"startX": 0.10, "startY": 0.91, "endX": 0.1018363939899833, "endY": 0.99}]}
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 1

    async def test_happy_path_graph_construction_returns_inference_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"connected_symbols": [{"id": 9, "label": "test", "text_associated": "test L",\
                          "bounding_box": {"topX": 0.1, "topY": 0.02, "bottomX": 0.2, "bottomY": 0.3},\
                          "connections": [{"id": 5, "label": "conn L", "text_associated": "conn t",\
                                           "bounding_box": {"topX": 0.2, "topY": 0.02, "bottomX": 0.3, "bottomY": 0.1},\
                                           "flow_direction": "l", "line_metadata": {"line_type": "u"}}]}]}'

        pid_id = '123'
        inference_result_type = InferenceResult.graph_construction

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_response_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
                patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
                    result = await get_inference_results(inference_result_type, pid_id)

        result = [x async for x in result.body_iterator]
        result = b"".join(result)
        result = json.loads(result)

        # assert
        assert result == {"connected_symbols": [{"id": 9, "label": "test", "text_associated": "test L",
                          "bounding_box": {"topX": 0.1, "topY": 0.02, "bottomX": 0.2, "bottomY": 0.3},
                          "connections": [{"id": 5, "label": "conn L", "text_associated": "conn t",
                                           "bounding_box": {"topX": 0.2, "topY": 0.02, "bottomX": 0.3, "bottomY": 0.1},
                                           "flow_direction": "l", "line_metadata": {"line_type": "u"}}]}]}
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_response_path.call_count == 1

    async def test_file_not_exists_throws_http_exception(self):
        # arrange
        def mock_blob_exists(*args):
            return False

        pid_id = '123'
        inference_result_type = InferenceResult.symbol_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_symbol_inference_result_storage_path = MagicMock(return_value='123/inference_results/123.json')

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(wraps=mock_blob_exists)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            with pytest.raises(HTTPException) as e:
                await get_inference_results(inference_result_type, pid_id)

        # assert
        assert e.value.status_code == 404
        assert e.value.detail == 'Inference results not found for pid 123.'


class TestGetJobStatus(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_symbol_returns_job_status_results(self):
        # arrange
        def mock_download_bytes(*args):
            return b'{"status": "done", "step": "line_detection", "message": null, "updated_at": "2023-06-08 14:57:25.521724"}'

        pid_id = '123'

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_job_status_path = MagicMock(return_value='123/graph-construction/job_status.json')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(side_effect=[True, True])

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_job_status(pid_id)

        # assert
        assert result == {'status': 'done', 'step': 'line_detection', 'message': None, 'updated_at': '2023-06-08 14:57:25.521724'}
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_inference_job_status_path.call_count == 1

    async def test_status_file_not_exists_throws_http_exception(self):
        # arrange
        def mock_blob_exists(*args):
            return False

        pid_id = '123'

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_inference_job_status_path = MagicMock(return_value='123/graph-construction/job_status.json')

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(wraps=mock_blob_exists)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
            patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            with pytest.raises(HTTPException) as e:
                await get_job_status(pid_id)

        # assert
        assert e.value.status_code == 404
        assert e.value.detail == 'Inference results not found for pid 123.'


class TestGetInferenceImages(unittest.IsolatedAsyncioTestCase):
    @parameterized.expand([(InferenceResult.symbol_detection, '123_symbol-detection.png'),
                           (InferenceResult.text_detection, '123_text-detection.png'),
                           (InferenceResult.line_detection, '123_line-detection.png'),
                           (InferenceResult.graph_construction, '123_graph-construction.png')])
    async def test_happy_path_get_output_inference_images(self, result_type, filename):
        # arrange
        def mock_download_bytes(*args):
            return b'123'

        pid_id = '123'

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_output_image_path = MagicMock(return_value='123/inference_results/123.jpg')

        blob_storage_client = MagicMock()
        blob_storage_client.download_bytes = MagicMock(wraps=mock_download_bytes)
        blob_storage_client.blob_exists = MagicMock(return_value=True)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            result = await get_output_inference_images(pid_id, result_type)

        # assert
        assert result == ImageResponse(image=b'123', filename=filename)
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 1
        assert storage_path_template_builder.build_output_image_path.call_count == 1

    async def test_file_not_exists_throws_http_exception(self):
        # arrange
        def mock_blob_exists(*args):
            return False

        pid_id = '123'
        result_type = InferenceResult.symbol_detection

        storage_path_template_builder = MagicMock()
        storage_path_template_builder.build_output_image_path = MagicMock(return_value='123/inference_results/123.jpg')

        blob_storage_client = MagicMock()
        blob_storage_client.blob_exists = MagicMock(wraps=mock_blob_exists)

        # act
        with patch("app.routes.controllers.pid_digitization_controller.storage_path_template_builder", storage_path_template_builder), \
             patch("app.routes.controllers.pid_digitization_controller.blob_storage_client", blob_storage_client):
            with pytest.raises(HTTPException) as e:
                await get_output_inference_images(pid_id, result_type)

        # assert
        assert e.value.status_code == 404
        assert e.value.detail == f'Inference image not found for pid id 123 and inference result type {result_type}'
        assert blob_storage_client.blob_exists.call_count == 1
        assert blob_storage_client.download_bytes.call_count == 0


class TestGraphPersistence(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_returns_success(self):
        # arrange
        pid_id = '123'
        corrected_graph_construction_results = GraphConstructionInferenceResponse(**{
            'label': [],
            'image_url': '123/images/123.jpg',
            'image_details': {
                'width': 100,
                'height': 100},
            'connected_symbols': []})

        graph_persistence_persist = MagicMock()

        # act
        with patch("app.routes.controllers.pid_digitization_controller.graph_persistence.persist", graph_persistence_persist):
            await persist_graph(pid_id, corrected_graph_construction_results)

        # assert
        graph_persistence_persist.assert_called_once_with(pid_id, corrected_graph_construction_results.connected_symbols)

    async def test_file_not_exists_throws_http_exception(self):
        # arrange
        pid_id = '123'
        corrected_graph_construction_results = GraphConstructionInferenceResponse(**{
            'label': [],
            'image_url': '123/images/123.jpg',
            'image_details': {
                'width': 100,
                'height': 100},
            'connected_symbols': []})

        graph_persistence_persist = MagicMock(side_effect=Exception('Error persisting graph'))

        # act
        with patch("app.routes.controllers.pid_digitization_controller.graph_persistence.persist", graph_persistence_persist):
            with pytest.raises(HTTPException) as e:
                await persist_graph(pid_id, corrected_graph_construction_results)

        # assert
        graph_persistence_persist.assert_called_once_with(pid_id, corrected_graph_construction_results.connected_symbols)
