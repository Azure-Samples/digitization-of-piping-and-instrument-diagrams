# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import cv2
import numpy as np

from app.services.base_image_preprocessor import to_grayscale, to_binary


class TextDetectionImagePreprocessor():
    '''
    Helper class to perform preprocessing on an image.
    '''
    @staticmethod
    def preprocess(image_bytes: bytes):
        '''
        Preprocesses the given image bytes. Applies the following transformations:
        1. Converts the image to grayscale
        2. Binarizes the image using Otsu's method for image thresholding
        :param image_bytes: The image bytes to preprocess
        :type image_bytes: bytes'''
        # convert image bytes to cv2 image
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        # Convert to grayscale
        image = to_grayscale(image)

        # Binarization
        image = to_binary(image)

        # return the image bytes
        return cv2.imencode('.png', image)[1].tobytes()
