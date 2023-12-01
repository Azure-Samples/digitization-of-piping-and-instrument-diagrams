# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import parameterized
import unittest
from unittest.mock import patch, call, ANY
import sys
from fastapi import HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.text_detection import run_inferencing
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.symbol_detection.label import Label
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.text_detection.text_recognized import TextRecognized
from app.models.text_detection.text_detection_inference_response import TextDetectionInferenceResponse
from app.models.bounding_box import BoundingBox
from app.models.image_details import ImageDetails


class TestRunInferencing(unittest.TestCase):
    pid_id = 'pid-id'
    image = b'123'
    area_threshold = 0.8
    distance_threshold = 0.01
    symbol_label_prefixes_with_text = set(['lmi', 'tag'])

    symbol_detection_result = SymbolDetectionInferenceResponse(
        image_url=f'{pid_id}.png',
        image_details=ImageDetails(height=100, width=100),
        bounding_box_inclusive=BoundingBox(bottomX=1.0, bottomY=1.0, topX=0.0, topY=0.0),
        label=[
            Label(
                label='lmi',
                score=0.9,
                topX=0.1,
                topY=0.1,
                bottomX=0.2,
                bottomY=0.2,
                id=1
            ),
            Label(
                label='tag',
                score=0.9,
                topX=0.4,
                topY=0.4,
                bottomX=0.5,
                bottomY=0.5,
                id=2
            ),
            Label(
                label='arrow',
                score=0.9,
                topX=0.6,
                topY=0.6,
                bottomX=0.7,
                bottomY=0.7,
                id=3
            ),
        ]
    )

    read_text_result = [
        ('lmi', [[10, 10], [20, 10], [20, 20], [10, 20]]),
        ('tag', [[40, 40], [50, 40], [50, 50], [40, 50]]),
        ('arrow', [[60, 60], [70, 60], [70, 70], [60, 70]]),
    ]

    all_text_list = [
        TextRecognized(
            text='lmi',
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.2,
        ),
        TextRecognized(
            text='tag',
            topX=0.4,
            topY=0.4,
            bottomX=0.5,
            bottomY=0.5,
        ),
        TextRecognized(
            text='arrow',
            topX=0.6,
            topY=0.6,
            bottomX=0.7,
            bottomY=0.7,
        )
    ]

    correlate_symbols_with_text = [
        SymbolAndTextAssociated(
            id=1,
            label='lmi',
            score=None,
            topX=0.1,
            topY=0.1,
            bottomX=0.2,
            bottomY=0.2,
            text_associated='lmi',
        ),
        SymbolAndTextAssociated(
            id=2,
            label='tag',
            score=None,
            topX=0.4,
            topY=0.4,
            bottomX=0.5,
            bottomY=0.5,
            text_associated='tag',
        ),
        SymbolAndTextAssociated(
            id=3,
            label='arrow',
            score=None,
            topX=0.6,
            topY=0.6,
            bottomX=0.7,
            bottomY=0.7,
            text_associated=None,
        )
    ]

    @parameterized.parameterized.expand([('test.png', 'test2.png'), ('test.png', None), (None, 'test.png')])
    def test_happy_path_without_saving_bounding_boxes(self, debug_image_text_path, debug_image_symbol_and_text_path):
        # arrange

        # act
        with patch('app.services.text_detection.text_detection_service.ocr_client.read_text') as mock_read_text, \
             patch('app.services.text_detection.text_detection_service.correlate_symbols_with_text') as mock_correlate_symbols_with_text, \
             patch('app.services.text_detection.text_detection_service.TextDetectionImagePreprocessor.preprocess') as mock_preprocess:
            mock_preprocess.return_value = self.image
            mock_read_text.return_value = self.read_text_result
            mock_correlate_symbols_with_text.return_value = self.correlate_symbols_with_text
            result = run_inferencing(
                pid_id=self.pid_id,
                symbol_detection_inference_results=self.symbol_detection_result,
                image=self.image,
                area_threshold=self.area_threshold,
                distance_threshold=self.distance_threshold,
                symbol_label_prefixes_with_text=self.symbol_label_prefixes_with_text,
                debug_image_text_path=debug_image_text_path,
                output_image_symbol_and_text_path=debug_image_symbol_and_text_path
            )

        # assert
        expected_result = TextDetectionInferenceResponse(
            image_url=f'{self.pid_id}.png',
            image_details=ImageDetails(height=100, width=100),
            bounding_box_inclusive=BoundingBox(bottomX=1.0, bottomY=1.0, topX=0.0, topY=0.0),
            all_text_list=self.all_text_list,
            text_and_symbols_associated_list=self.correlate_symbols_with_text,
        )
        self.assertEqual(result, expected_result)

        mock_preprocess.assert_called_once_with(self.image)
        mock_read_text.assert_called_once()
        mock_correlate_symbols_with_text.assert_called_once_with(
            self.all_text_list,
            self.symbol_detection_result,
            self.area_threshold,
            self.distance_threshold,
            ('lmi', 'tag')
        )

    def test_happy_path_with_saving_bounding_boxes(self):
        # arrange
        debug_image_text_path='debug_text.png'
        debug_image_symbol_and_text_path='debug_symbol_and_text.png'

        # act
        with patch('app.services.text_detection.text_detection_service.ocr_client.read_text') as mock_read_text, \
            patch('app.services.text_detection.text_detection_service.correlate_symbols_with_text') as mock_correlate_symbols_with_text, \
            patch('app.services.text_detection.text_detection_service.TextDetectionImagePreprocessor.preprocess') as mock_preprocess, \
            patch('app.services.text_detection.text_detection_service.draw_bounding_boxes') as mock_draw_bounding_boxes, \
            patch('app.services.text_detection.text_detection_service.config') as mock_config, \
            patch('app.services.text_detection.text_detection_service.does_string_contain_at_least_one_number_and_one_letter') as mock_does_string_contain_at_least_one_number_and_one_letter, \
            patch('cv2.imwrite') as mock_imwrite:
            mock_draw_bounding_boxes.return_value = self.image
            mock_preprocess.return_value = self.image
            mock_read_text.return_value = self.read_text_result
            mock_config.debug = True
            mock_correlate_symbols_with_text.return_value = self.correlate_symbols_with_text
            mock_does_string_contain_at_least_one_number_and_one_letter.return_value = True
            result = run_inferencing(
                pid_id=self.pid_id,
                symbol_detection_inference_results=self.symbol_detection_result,
                image=self.image,
                area_threshold=self.area_threshold,
                distance_threshold=self.distance_threshold,
                symbol_label_prefixes_with_text=self.symbol_label_prefixes_with_text,
                debug_image_text_path=debug_image_text_path,
                output_image_symbol_and_text_path=debug_image_symbol_and_text_path
            )

        # assert
        expected_result = TextDetectionInferenceResponse(
            image_url=f'{self.pid_id}.png',
            image_details=ImageDetails(height=100, width=100),
            bounding_box_inclusive=BoundingBox(bottomX=1.0, bottomY=1.0, topX=0.0, topY=0.0),
            all_text_list=self.all_text_list,
            text_and_symbols_associated_list=self.correlate_symbols_with_text,
        )
        self.assertEqual(result, expected_result)

        mock_preprocess.assert_called_once_with(self.image)
        mock_read_text.assert_called_once()
        mock_correlate_symbols_with_text.assert_called_once_with(
            self.all_text_list,
            self.symbol_detection_result,
            self.area_threshold,
            self.distance_threshold,
            ('lmi', 'tag')
        )

        expected_ids_call1 = [result.id for result in self.correlate_symbols_with_text if result.label != 'arrow']
        expected_bounding_boxes_call1 = [BoundingBox(**result.dict()) for result in self.correlate_symbols_with_text if result.label != 'arrow']
        expected_labels_call1 = [result.text_associated for result in self.correlate_symbols_with_text if result.label != 'arrow']
        expected_ids_call2 = None
        expected_bounding_boxes_call2 = [BoundingBox(**result.dict()) for result in self.all_text_list]
        expected_labels_call2 = [result.text for result in self.all_text_list]
        valid_bit_array1 = [
            1 for result in self.correlate_symbols_with_text if result.label != 'arrow'
        ]
        mock_draw_bounding_boxes.assert_has_calls(
            calls=[
                call(
                    self.image,
                    self.symbol_detection_result.image_details,
                    expected_ids_call1,
                    expected_bounding_boxes_call1,
                    expected_labels_call1,
                    valid_bit_array1
                ),
                call(
                    self.image,
                    self.symbol_detection_result.image_details,
                    expected_ids_call2,
                    expected_bounding_boxes_call2,
                    expected_labels_call2,
                )
            ],
            any_order=True
        )
        mock_imwrite.assert_has_calls(
            calls=[
                call(debug_image_text_path, self.image),
                call(debug_image_symbol_and_text_path, self.image)
            ],
            any_order=True
        )

    def test_when_ocr_client_throws_exception_then_raises_http_exception(self):
        # arrange

        # act
        with patch('app.services.text_detection.text_detection_service.TextDetectionImagePreprocessor.preprocess') as mock_preprocess, \
             patch('app.services.text_detection.text_detection_service.ocr_client.read_text') as mock_read_text:
            mock_preprocess.return_value = self.image
            mock_read_text.side_effect = Exception('Error')
            with self.assertRaises(HTTPException) as exception:
                run_inferencing(
                    pid_id=self.pid_id,
                    symbol_detection_inference_results=self.symbol_detection_result,
                    image=self.image,
                    area_threshold=self.area_threshold,
                    distance_threshold=self.distance_threshold,
                    symbol_label_prefixes_with_text=self.symbol_label_prefixes_with_text,
                    debug_image_text_path=None,
                    output_image_symbol_and_text_path=None
                )

        # assert
        self.assertEqual(exception.exception.status_code, 500)
        self.assertEqual(exception.exception.detail, 'There was an internal issue performing OCR on the image.')