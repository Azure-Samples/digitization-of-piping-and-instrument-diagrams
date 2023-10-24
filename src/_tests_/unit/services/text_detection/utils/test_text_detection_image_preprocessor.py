import cv2
import os
import sys
import numpy as np
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from app.services.text_detection.utils.text_detection_image_preprocessor import TextDetectionImagePreprocessor

input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')


class TestTextDetectionImagePreprocessor(unittest.TestCase):
    def test_preprocess_valid_image(self):
        # Create a test image
        input_image_path = os.path.join(input_data_path, 'image.png')
        image = cv2.imread(input_image_path)

        # Convert the image to bytes
        image_bytes = cv2.imencode('.png', image)[1].tobytes()

        # Preprocess the image
        processed_image_bytes = TextDetectionImagePreprocessor.preprocess(image_bytes)

        # Convert the processed image bytes to a cv2 image
        processed_image = cv2.imdecode(np.frombuffer(processed_image_bytes, np.uint8), cv2.IMREAD_UNCHANGED)

        # Assert that the processed image has only one color channel (i.e. is grayscale)
        self.assertEqual(len(processed_image.shape), 2)

        # Assert that the processed image is binary (only black or white pixels)
        self.assertTrue(np.all(np.logical_or(processed_image == 0, processed_image == 255)))
