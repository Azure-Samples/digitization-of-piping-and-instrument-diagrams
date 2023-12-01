# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import parameterized
import unittest
from unittest.mock import patch, call, ANY
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.line_detection.line_detection_service import detect_lines
from app.models.line_detection.line_detection_response import LineDetectionInferenceResponse
from app.models.line_detection.line_segment import LineSegment
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.text_detection.text_recognized import TextRecognized
from app.models.text_detection.text_detection_inference_response import TextDetectionInferenceResponse
from app.models.bounding_box import BoundingBox
from app.models.image_details import ImageDetails


class TestDetectLines(unittest.TestCase):
    pid_id = 'pid-id'
    image = b'123'

    threshold = 8
    min_line_length = 10
    max_line_gap = 8
    rho = 0.2
    theta_param = 1080
    bounding_box_inclusive_normalized = BoundingBox(
        topX=0.1,
        topY=0.1,
        bottomX=0.2,
        bottomY=0.2
    )
    bounding_box_inclusive_denormalized = BoundingBox(
        topX=10,
        topY=10,
        bottomX=20,
        bottomY=20
    )
    image_height = 100
    image_width = 100
    thinning_enabled = True

    line_segments_service_results = [
        LineSegment(
            startX=0.1,
            startY=0.1,
            endX=0.2,
            endY=0.2
        ),
        LineSegment(
            startX=0.4,
            startY=0.4,
            endX=0.5,
            endY=0.5
        ),
    ]

    text_detection_results = TextDetectionInferenceResponse(
        image_url=f'{pid_id}.png',
        image_details=ImageDetails(height=image_height, width=image_width),
        all_text_list=[
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
        ],
        text_and_symbols_associated_list=[
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
    )

    denormalized_symbol_detected_coords = [
        BoundingBox(topX=10.0, topY=10.0, bottomX=20.0, bottomY=20.0),
        BoundingBox(topX=40.0, topY=40.0, bottomX=50.0, bottomY=50.0),
        BoundingBox(topX=60.0, topY=60.0, bottomX=70.0, bottomY=70.0)
    ]

    denormalized_text_detected_coords = [
        BoundingBox(topX=10.0, topY=10.0, bottomX=20.0, bottomY=20.0),
        BoundingBox(topX=40.0, topY=40.0, bottomX=50.0, bottomY=50.0),
        BoundingBox(topX=60.0, topY=60.0, bottomX=70.0, bottomY=70.0)
    ]

    @parameterized.parameterized.expand([('test.png', 'test2.png', 'test3.png'), ('test.png', None, None), (None, 'test.png', None),  (None, None, 'test.png')])
    def test_happy_path(self, debug_image_preprocessed_path, debug_image_preprocessed_before_thinning_path, output_image_line_segments_path):
        # arrange

        # act
        with patch('app.services.line_detection.line_detection_service.detect_line_segments') as mock_detect_line_segments, \
            patch('app.services.line_detection.line_detection_service.LineDetectionImagePreprocessor.preprocess') as mock_preprocess, \
            patch('app.services.line_detection.line_detection_service.LineDetectionImagePreprocessor.apply_thinning') as mock_apply_thinning:
            mock_preprocess.return_value = self.image
            mock_apply_thinning.return_value = self.image
            mock_detect_line_segments.return_value = self.line_segments_service_results

            result = detect_lines(
                pid_id=self.pid_id,
                image_bytes=self.image,
                text_detection_results=self.text_detection_results,
                enable_thinning=self.thinning_enabled,
                threshold=self.threshold,
                max_line_gap=self.max_line_gap,
                min_line_length=self.min_line_length,
                rho=self.rho,
                theta_param=self.theta_param,
                bounding_box_inclusive=self.bounding_box_inclusive_normalized,
                image_height=self.image_height,
                image_width=self.image_width,
                debug_image_preprocessed_path=debug_image_preprocessed_path,
                debug_image_preprocessed_before_thinning_path=debug_image_preprocessed_before_thinning_path,
                output_image_line_segments_path=output_image_line_segments_path
            )

        # assert
        expected_result = LineDetectionInferenceResponse(
            line_segments=self.line_segments_service_results,
            image_url=f'{self.pid_id}.png',
            line_segments_count=2,
            image_details=ImageDetails(height=self.image_height, width=self.image_width)
        )
        self.assertEqual(result, expected_result)

        mock_preprocess.assert_called_once_with(self.image, self.denormalized_symbol_detected_coords, self.denormalized_text_detected_coords)
        mock_apply_thinning.assert_called_once_with(self.image)

        mock_detect_line_segments.assert_called_once_with(
            self.pid_id,
            self.image,
            self.image_height,
            self.image_width,
            self.threshold,
            self.max_line_gap,
            self.min_line_length,
            self.rho,
            self.theta_param,
            self.bounding_box_inclusive_denormalized,
        )

    def test_happy_path_no_thinning(self):
        # arrange
        debug_image_preprocessed_path = 'preprocessed.png'
        debug_image_preprocessed_before_thinning_path = 'preprocessed_before_thinning.png'
        output_image_line_segments_path = 'line_segments.png'

        # act
        with patch('app.services.line_detection.line_detection_service.detect_line_segments') as mock_detect_line_segments, \
            patch('app.services.line_detection.line_detection_service.LineDetectionImagePreprocessor.preprocess') as mock_preprocess, \
            patch('app.services.line_detection.line_detection_service.LineDetectionImagePreprocessor.apply_thinning') as mock_apply_thinning:
            mock_preprocess.return_value = self.image
            mock_apply_thinning.return_value = self.image
            mock_detect_line_segments.return_value = self.line_segments_service_results

            result = detect_lines(
                pid_id=self.pid_id,
                image_bytes=self.image,
                text_detection_results=self.text_detection_results,
                enable_thinning=False,
                threshold=self.threshold,
                max_line_gap=self.max_line_gap,
                min_line_length=self.min_line_length,
                rho=self.rho,
                theta_param=self.theta_param,
                bounding_box_inclusive=self.bounding_box_inclusive_normalized,
                image_height=self.image_height,
                image_width=self.image_width,
                debug_image_preprocessed_path=debug_image_preprocessed_path,
                debug_image_preprocessed_before_thinning_path=debug_image_preprocessed_before_thinning_path,
                output_image_line_segments_path=output_image_line_segments_path
            )

        # assert
        expected_result = LineDetectionInferenceResponse(
            line_segments=self.line_segments_service_results,
            image_url=f'{self.pid_id}.png',
            line_segments_count=2,
            image_details=ImageDetails(height=self.image_height, width=self.image_width)
        )
        self.assertEqual(result, expected_result)

        mock_preprocess.assert_called_once_with(self.image, self.denormalized_symbol_detected_coords, self.denormalized_text_detected_coords)
        mock_apply_thinning.assert_not_called()

        mock_detect_line_segments.assert_called_once_with(
            self.pid_id,
            self.image,
            self.image_height,
            self.image_width,
            self.threshold,
            self.max_line_gap,
            self.min_line_length,
            self.rho,
            self.theta_param,
            self.bounding_box_inclusive_denormalized,
        )
