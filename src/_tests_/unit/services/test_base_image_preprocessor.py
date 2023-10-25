import cv2
import os
import sys
import numpy as np
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.services.base_image_preprocessor import to_binary, to_grayscale

input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')


class TestBaseImagePreprocessor(unittest.TestCase):
    def test_preprocessing_methods(self):
        # Create a test image
        input_image_path = os.path.join(input_data_path, 'image.png')
        image = cv2.imread(input_image_path)

        # Make image grayscale
        grayscale_image = to_grayscale(image)

        # Assert that the processed image has only one color channel (i.e. is grayscale)
        self.assertEqual(len(grayscale_image.shape), 2)

        # Binarize image
        # Note that we need to do this in the same test as grayscale since Otsu's
        # thresholding method requires a single-channel image as input
        binarized_image = to_binary(grayscale_image)

        # Assert that the processed image is binary (only black or white pixels)
        self.assertTrue(np.all(np.logical_or(binarized_image == 0, binarized_image == 255)))
