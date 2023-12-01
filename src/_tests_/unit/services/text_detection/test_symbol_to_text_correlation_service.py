# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import json
import os
import unittest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.services.text_detection.symbol_to_text_correlation_service import correlate_symbols_with_text
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.text_detection.text_recognized import TextRecognized


input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')
expect_data_path = os.path.join(os.path.dirname(__file__), 'data', 'expect')


class TestCorrelateSymbolsWithText(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        symbol_detection_data_path = os.path.join(input_data_path, 'symbol_detection_data.json')
        text_detection_data_path = os.path.join(input_data_path, 'text_detection_data.json')
        expected_output_path = os.path.join(expect_data_path, 'expected_symbol_text_detection_result.json')

        with open(symbol_detection_data_path, 'rb') as f:
            symbol_detection_data = SymbolDetectionInferenceResponse.parse_raw(f.read())

        with open(text_detection_data_path, 'r') as f:
            text_detection_data = json.load(f)
            text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        with open(expected_output_path, 'r') as f:
            expected_output = json.load(f)

        area_threshold = 0.8
        distance_threshold = 0.01
        symbol_labels_with_text = ('lmi', 'tag', 'valve', 'plate')

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            symbol_labels_with_text)

        # assert
        result = [elem.dict() for elem in result]
        assert result == expected_output

    def test_when_closest_text_not_alphanumeric_case1_returns_text_associated_without_alphanumeric_text(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "testi",
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.5,
                "bottomY": 0.5,
            },
            {
                "text": "testj",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            },
            {
                "text": "test 123",
                "topX": 0.502,
                "topY": 0.502,
                "bottomX": 1.002,
                "bottomY": 1.002,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "testi"

    def test_when_closest_text_not_alphanumeric_case2_returns_text_associated_with_alphanumeric_text(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "test",
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.5,
                "bottomY": 0.5,
            },
            {
                "text": "test",
                "topX": 0.502,
                "topY": 0.502,
                "bottomX": 1.002,
                "bottomY": 1.002,
            },
            {
                "text": "test 123",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "test 123"

    def test_when_closest_text_not_alphanumeric_returns_none_with_no_text_close_with_alphanumic_text(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "testi",
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.5,
                "bottomY": 0.5,
            },
            {
                "text": "testj",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            },
            {
                "text": "test 123",
                "topX": 0.52,
                "topY": 0.52,
                "bottomX": 1.02,
                "bottomY": 1.02,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "testi"

    def test_when_closest_text_alphanumeric_and_text_outside_alphanumeric_returns_closest_text(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "test 123",
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.5,
                "bottomY": 0.5,
            },
            {
                "text": "456 test",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "test 123"

    def test_when_closest_text_alphanumeric_and_text_outside_not_alphanumeric_returns_closest_text(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "test 123",
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.5,
                "bottomY": 0.5,
            },
            {
                "text": "test",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "test 123"

    def test_when_multiple_text_outside_returns_correct_text_with_number(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "test1",
                "topX": 0.502,
                "topY": 0.502,
                "bottomX": 1.002,
                "bottomY": 1.002,
            },
            {
                "text": "test2",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "test2"

    def test_when_multiple_text_outside_returns_correct_text_without_number(self):
        # arrange
        symbol_detection_data = {
            "image_url": "pid.png",
            "image_details": {
                "height": 100,
                "width": 100
            },
            "label": [
                {
                    "label": "label1",
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.5,
                    "bottomY": 0.5,
                    "id": 1
                }
            ]
        }
        symbol_detection_data = SymbolDetectionInferenceResponse(**symbol_detection_data)

        text_detection_data = [
            {
                "text": "testi",
                "topX": 0.502,
                "topY": 0.502,
                "bottomX": 1.002,
                "bottomY": 1.002,
            },
            {
                "text": "testj",
                "topX": 0.501,
                "topY": 0.501,
                "bottomX": 1.001,
                "bottomY": 1.001,
            }
        ]
        text_detection_data = [TextRecognized(**result) for result in text_detection_data]

        area_threshold = 0.8
        distance_threshold = 0.01
        label_prefixes_with_text: tuple[str] = ('label',)

        # act
        result = correlate_symbols_with_text(
            text_detection_data,
            symbol_detection_data,
            area_threshold,
            distance_threshold,
            label_prefixes_with_text)

        # assert
        assert result[0].text_associated == "testj"
