import os
from pydantic import ValidationError
import unittest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from app.config import Config


class TestConfig(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        blob_storage_account_url = 'blob_storage_account_url'
        blob_storage_container_name = 'blob_storage_container_name'
        form_recognizer_endpoint = 'form_recognizer_endpoint'
        debug = True
        detect_dotted_lines = False
        inference_score_threshold = 1.5
        inference_service_retry_count = 5
        inference_service_retry_backoff_factor = 1.0
        port = 3000
        symbol_detection_api = 'symbol_detection_api'
        symbol_detection_api_bearer_token = 'symbol_detection_api_bearer_token'
        symbol_label_prefixes_with_text = '1,2,3,4'
        text_detection_area_intersection_ratio_threshold = 0.9
        text_detection_distance_threshold = 0.04

        # act
        config = Config(
            blob_storage_account_url=blob_storage_account_url,
            blob_storage_container_name=blob_storage_container_name,
            form_recognizer_endpoint=form_recognizer_endpoint,
            debug=debug,
            detect_dotted_lines=detect_dotted_lines,
            inference_score_threshold=inference_score_threshold,
            inference_service_retry_count=inference_service_retry_count,
            inference_service_retry_backoff_factor=inference_service_retry_backoff_factor,
            port=port,
            symbol_detection_api=symbol_detection_api,
            symbol_detection_api_bearer_token=symbol_detection_api_bearer_token,
            symbol_label_prefixes_with_text=symbol_label_prefixes_with_text,
            text_detection_area_intersection_ratio_threshold=text_detection_area_intersection_ratio_threshold,
            text_detection_distance_threshold=text_detection_distance_threshold
        )

        # assert
        assert config.blob_storage_account_url == blob_storage_account_url
        assert config.blob_storage_container_name == blob_storage_container_name
        assert config.form_recognizer_endpoint == form_recognizer_endpoint
        assert config.debug == debug
        assert config.detect_dotted_lines == detect_dotted_lines
        assert config.line_detection_hough_min_line_length == 10
        assert config.line_detection_hough_max_line_gap is None
        assert config.inference_score_threshold == inference_score_threshold
        assert config.inference_service_retry_count == inference_service_retry_count
        assert config.inference_service_retry_backoff_factor == inference_service_retry_backoff_factor
        assert config.port == port
        assert config.symbol_detection_api == symbol_detection_api
        assert config.symbol_detection_api_bearer_token == symbol_detection_api_bearer_token
        assert config.symbol_label_prefixes_with_text == set(['1', '2', '3', '4'])
        assert config.text_detection_area_intersection_ratio_threshold == text_detection_area_intersection_ratio_threshold
        assert config.text_detection_distance_threshold == text_detection_distance_threshold

    def test_happy_path_dotted_lines_true(self):
        # arrange
        blob_storage_account_url = 'blob_storage_account_url'
        blob_storage_container_name = 'blob_storage_container_name'
        form_recognizer_endpoint = 'form_recognizer_endpoint'
        debug = True
        detect_dotted_lines = True
        inference_score_threshold = 1.5
        inference_service_retry_count = 5
        inference_service_retry_backoff_factor = 1.0
        port = 3000
        symbol_detection_api = 'symbol_detection_api'
        symbol_detection_api_bearer_token = 'symbol_detection_api_bearer_token'
        symbol_label_prefixes_with_text = '1,2,3,4'
        text_detection_area_intersection_ratio_threshold = 0.9
        text_detection_distance_threshold = 0.04

        # act
        config = Config(
            blob_storage_account_url=blob_storage_account_url,
            blob_storage_container_name=blob_storage_container_name,
            form_recognizer_endpoint=form_recognizer_endpoint,
            debug=debug,
            detect_dotted_lines=detect_dotted_lines,
            inference_score_threshold=inference_score_threshold,
            inference_service_retry_count=inference_service_retry_count,
            inference_service_retry_backoff_factor=inference_service_retry_backoff_factor,
            port=port,
            symbol_detection_api=symbol_detection_api,
            symbol_detection_api_bearer_token=symbol_detection_api_bearer_token,
            symbol_label_prefixes_with_text=symbol_label_prefixes_with_text,
            text_detection_area_intersection_ratio_threshold=text_detection_area_intersection_ratio_threshold,
            text_detection_distance_threshold=text_detection_distance_threshold
        )

        # assert
        assert config.blob_storage_account_url == blob_storage_account_url
        assert config.blob_storage_container_name == blob_storage_container_name
        assert config.form_recognizer_endpoint == form_recognizer_endpoint
        assert config.debug == debug
        assert config.detect_dotted_lines == detect_dotted_lines
        assert config.line_detection_hough_min_line_length is None
        assert config.line_detection_hough_max_line_gap == 10
        assert config.inference_score_threshold == inference_score_threshold
        assert config.inference_service_retry_count == inference_service_retry_count
        assert config.inference_service_retry_backoff_factor == inference_service_retry_backoff_factor
        assert config.port == port
        assert config.symbol_detection_api == symbol_detection_api
        assert config.symbol_detection_api_bearer_token == symbol_detection_api_bearer_token
        assert config.symbol_label_prefixes_with_text == set(['1', '2', '3', '4'])
        assert config.text_detection_area_intersection_ratio_threshold == text_detection_area_intersection_ratio_threshold
        assert config.text_detection_distance_threshold == text_detection_distance_threshold

    def test_empty_mandatory_config_values_then_throws_validation_error(self):
        # arrange

        # act
        with self.assertRaises(ValidationError) as exception:
            _ = Config(
                blob_storage_account_url=str(),
                blob_storage_container_name=str(),
                form_recognizer_endpoint=str(),
                symbol_detection_api=str(),
                symbol_detection_api_bearer_token=str()
            )

        # assert
        exception_json = exception.exception.json()
        self.assertIn("blob_storage_account_url", exception_json)
        self.assertIn("blob_storage_container_name", exception_json)
        self.assertIn("form_recognizer_endpoint", exception_json)
        self.assertIn("symbol_detection_api", exception_json)
        self.assertIn("symbol_detection_api_bearer_token", exception_json)
