import json
import cv2
import os
import sys
import numpy as np
import unittest

from app.models.bounding_box import BoundingBox

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from app.services.line_detection.utils.line_detection_image_preprocessor import LineDetectionImagePreprocessor

input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')


class TestLineDetectionImagePreprocessor(unittest.TestCase):
    def test_preprocess_valid_image(self):
        # Create a test image
        input_image_path = os.path.join(input_data_path, 'image.png')
        image = cv2.imread(input_image_path, cv2.IMREAD_COLOR)

        input_symbols_path = os.path.join(input_data_path, 'symbols.json')
        input_text_path = os.path.join(input_data_path, 'text.json')

        symbol_bounding_boxes = self._get_bounding_boxes_from_file(input_symbols_path)
        text_bounding_boxes = self._get_bounding_boxes_from_file(input_text_path)

        # Convert the image to bytes
        image_bytes = cv2.imencode('.png', image)[1].tobytes()

        # Preprocess the image
        processed_image = LineDetectionImagePreprocessor.preprocess(image_bytes, symbol_bounding_boxes, text_bounding_boxes)

        # Assert that the processed image has only one color channel (i.e. is grayscale)
        self.assertEqual(len(processed_image.shape), 2)

        # Assert that the processed image is binary (only black or white pixels)
        self.assertTrue(np.all(np.logical_or(processed_image == 0, processed_image == 255)))

        # Assert that the bounding boxes have been cleared
        for bb in symbol_bounding_boxes:
            self.assertTrue(np.all(processed_image[int(bb.bottomY):int(bb.topY), int(bb.bottomX):int(bb.topX)] == processed_image[int(bb.bottomY)][int(bb.bottomX)]))
        for bb in text_bounding_boxes:
            self.assertTrue(np.all(processed_image[int(bb.bottomY):int(bb.topY), int(bb.bottomX):int(bb.topX)] == processed_image[int(bb.bottomY)][int(bb.bottomX)]))

    def test_clear_bounding_boxes(self):
        # Create a test image
        input_image_path = os.path.join(input_data_path, 'image.png')
        image = cv2.imread(input_image_path, cv2.IMREAD_COLOR)

        input_symbols_path = os.path.join(input_data_path, 'symbols.json')

        bounding_boxes = self._get_bounding_boxes_from_file(input_symbols_path)

        # Call the clear_bounding_boxes method
        output_image = LineDetectionImagePreprocessor.clear_bounding_boxes(image, bounding_boxes)

        # Assert that the bounding boxes have been cleared
        for bb in bounding_boxes:
            self.assertTrue(np.all(output_image[int(bb.bottomY):int(bb.topY), int(bb.bottomX):int(bb.topX)] == output_image[int(bb.bottomY)][int(bb.bottomX)]))

    def _get_bounding_boxes_from_file(self, file_path):
        file = open(file_path)
        file_data = json.load(file)

        bounding_boxes = []

        for elem in file_data:
            bb = BoundingBox(bottomX=(elem['bottomX']),
                             topX=(elem['topX']),
                             bottomY=(elem['bottomY']),
                             topY=(elem['topY']))

            bounding_boxes.append(bb)

        return bounding_boxes
