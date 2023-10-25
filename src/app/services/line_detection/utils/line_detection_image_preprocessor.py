import cv2
import numpy as np
from app.services.base_image_preprocessor import to_grayscale, to_binary
from app.models.bounding_box import BoundingBox


class LineDetectionImagePreprocessor:
    '''
    Helper class to perform preprocessing on an image.
    '''
    @staticmethod
    def preprocess(image_bytes: bytes,
                   symbol_bounding_boxes: list[BoundingBox],
                   text_bounding_boxes: list[BoundingBox]):
        '''
        Preprocesses the given image bytes. Applies the following transformations:
        1. Clears symbol bounding boxes
        2. Clears text bounding boxes
        3. Converts the image to grayscale
        4. Binarizes the image using Otsu's method for image thresholding

        :param image_bytes: The image bytes to preprocess
        :type image_bytes: bytes
        :param symbol_bounding_boxes: The symbol bounding boxes to clear
        :type symbol_bounding_boxes: list
        :param text_bounding_boxes: The text bounding boxes to clear
        :type text_bounding_boxes: list
        :return: The preprocessed image bytes
        :rtype: bytes
        '''
        # convert image bytes to cv2 image
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        # Clear symbol bounding boxes
        image = LineDetectionImagePreprocessor.clear_bounding_boxes(image, symbol_bounding_boxes)

        # Clear text bounding boxes
        image = LineDetectionImagePreprocessor.clear_bounding_boxes(image, text_bounding_boxes)

        # Convert to grayscale
        image = to_grayscale(image)

        # Binarization
        image = to_binary(image)

        # return the image
        return image

    @staticmethod
    def clear_bounding_boxes(image, bounding_boxes: list[BoundingBox]):
        '''
        Clears the given bounding boxes from the image.
        :param image: The image to clear the bounding boxes from
        :type image: np.ndarray
        :param bounding_boxes: The bounding boxes to clear
        :type bounding_boxes: list[BoundingBox]
        :return: The image with the bounding boxes cleared
        '''

        # Compute the histogram of the image
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])

        # Find the index of the most frequent pixel value
        background_value = int(np.argmax(hist))

        for bb in bounding_boxes:
            points = np.array([[bb.bottomX, bb.topY],
                              [bb.bottomX, bb.bottomY],
                              [bb.topX, bb.bottomY],
                              [bb.topX, bb.topY]],
                              np.int32)
            cv2.fillPoly(image, [points], (background_value, background_value, background_value))

        return image

    @staticmethod
    def apply_thinning(image):
        '''
        Applies the Zhang-Suen thinning algorithm to the given image.
        :param image: The image to apply the thinning algorithm to'''
        thinningType = cv2.ximgproc.THINNING_ZHANGSUEN
        return cv2.ximgproc.thinning(image, thinningType=thinningType)
