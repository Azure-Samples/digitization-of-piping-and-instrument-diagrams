import os
import unittest
import sys
import json
import cv2

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.draw_elements import draw_bounding_boxes
from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.bounding_box import BoundingBox


input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')
expect_data_path = os.path.join(os.path.dirname(__file__), 'data', 'expect')


class TestDrawBoundingBoxes(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        input_image_path = os.path.join(input_data_path, 'image.png')
        input_symbol_inference_result_path = os.path.join(input_data_path, 'predictions.json')
        expect_image_path = os.path.join(expect_data_path, 'image.png')

        with open(input_symbol_inference_result_path, 'r') as f:
            inference_response = json.load(f)

        inference_response = SymbolDetectionInferenceResponse(**inference_response)
        image_details = inference_response.image_details
        bounding_boxes = [BoundingBox(**label.dict()) for label in inference_response.label]
        labels = [label.label for label in inference_response.label]

        with open(input_image_path, 'rb') as f:
            input_image = f.read()

        expect_image = cv2.imread(expect_image_path)
        expect_image_bytes = cv2.imencode('.png', expect_image)[1].tobytes()

        # act
        actual_image = draw_bounding_boxes(
            image_bytes=input_image,
            image_details=image_details,
            ids=None,
            bounding_boxes=bounding_boxes,
            annotations=labels
        )

        # assert
        actual_image_bytes = cv2.imencode('.png', actual_image)[1].tobytes()
        self.assertEqual(actual_image_bytes, expect_image_bytes)

    def test_happy_path_with_ids(self):
        # arrange
        input_image_path = os.path.join(input_data_path, 'image.png')
        input_symbol_inference_result_path = os.path.join(input_data_path, 'predictions.json')
        expect_image_path = os.path.join(expect_data_path, 'image_with_ids.png')

        with open(input_symbol_inference_result_path, 'r') as f:
            inference_response = json.load(f)

        inference_response = SymbolDetectionInferenceResponse(**inference_response)
        ids = [label.id for label in inference_response.label]
        image_details = inference_response.image_details
        bounding_boxes = [BoundingBox(**label.dict()) for label in inference_response.label]
        labels = [label.label for label in inference_response.label]

        with open(input_image_path, 'rb') as f:
            input_image = f.read()

        expect_image = cv2.imread(expect_image_path)
        expect_image_bytes = cv2.imencode('.png', expect_image)[1].tobytes()

        # act
        actual_image = draw_bounding_boxes(
            image_bytes=input_image,
            image_details=image_details,
            ids=ids,
            bounding_boxes=bounding_boxes,
            annotations=labels
        )

        # assert
        actual_image_bytes = cv2.imencode('.png', actual_image)[1].tobytes()
        self.assertEqual(actual_image_bytes, expect_image_bytes)

    def test_when_len_bounding_boxes_not_match_len_labels_throws_value_error(self):
        # arrange
        input_image_path = os.path.join(input_data_path, 'image.png')
        input_symbol_inference_result_path = os.path.join(input_data_path, 'predictions.json')

        with open(input_symbol_inference_result_path, 'r') as f:
            inference_response = json.load(f)

        inference_response = SymbolDetectionInferenceResponse(**inference_response)
        image_details = inference_response.image_details
        bounding_boxes = [BoundingBox(**label.dict()) for label in inference_response.label]
        labels = [label.label for label in inference_response.label]
        labels.append('extra-label')

        with open(input_image_path, 'rb') as f:
            input_image = f.read()

        # act
        with self.assertRaises(ValueError) as ex:
            draw_bounding_boxes(
                image_bytes=input_image,
                image_details=image_details,
                ids=None,
                bounding_boxes=bounding_boxes,
                annotations=labels
            )

        # assert
        self.assertEqual(str(ex.exception), 'The number of bounding boxes must match the number of annotations.')

    def test_when_len_ids_not_match_len_bounding_boxes_throws_value_error(self):
        # arrange
        input_image_path = os.path.join(input_data_path, 'image.png')
        input_symbol_inference_result_path = os.path.join(input_data_path, 'predictions.json')

        with open(input_symbol_inference_result_path, 'r') as f:
            inference_response = json.load(f)

        inference_response = SymbolDetectionInferenceResponse(**inference_response)
        image_details = inference_response.image_details
        ids = [1]
        bounding_boxes = [BoundingBox(**label.dict()) for label in inference_response.label]
        labels = [label.label for label in inference_response.label]

        with open(input_image_path, 'rb') as f:
            input_image = f.read()

        # act
        with self.assertRaises(ValueError) as ex:
            draw_bounding_boxes(
                image_bytes=input_image,
                image_details=image_details,
                ids=ids,
                bounding_boxes=bounding_boxes,
                annotations=labels
            )

        # assert
        self.assertEqual(str(ex.exception), 'The number of ids must match the number of bounding boxes.')
