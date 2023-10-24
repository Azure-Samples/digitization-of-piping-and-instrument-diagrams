import json
import os
import unittest
import sys
import cv2


sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from app.models.bounding_box import BoundingBox
from app.services.line_detection.line_segments_service import detect_line_segments
input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')
expect_data_path = os.path.join(os.path.dirname(__file__), 'data', 'expect')


class TestDetectLineSegments(unittest.TestCase):
    def test_happy_path_excluding_legend_outer_box(self):
        # arrange
        preprocessed_image_path = os.path.join(input_data_path,
                                               'HW4-cropped_text.jpg')
        bounding_box_coordinates = BoundingBox(
            topX=45.0,
            topY=49.0,
            bottomX=997.0,
            bottomY=728.0
        )

        gray = cv2.cvtColor(
            cv2.imread(preprocessed_image_path),
            cv2.COLOR_BGR2GRAY)

        thresh = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        expected_output_path = os.path.join(expect_data_path,
                                            'HW4_line_segments_filtered.json')
        with open(expected_output_path, 'r') as f:
            expected_output = json.load(f)

        height = 781
        width = 1388
        # act
        result = detect_line_segments(
            'pid_id',
            thresh,
            781, 1388,
            5, 5, None, 0.1, 1080,
            bounding_box_coordinates
        )

        # assert that the result is not empty
        assert len(result) > 0

        # assert that the line segment coordinates are within the bounding box
        for line in result:
            assert line.startX >= bounding_box_coordinates.topX/width
            assert line.startY >= bounding_box_coordinates.topY/height
            assert line.endX <= bounding_box_coordinates.bottomX/width
            assert line.endY <= bounding_box_coordinates.bottomY/height

        # assert that the expected line segments are all returned
        result = [elem.dict() for elem in result]
        assert result == expected_output

    def test_happy_path_including_legend_outer_box(self):
        # arrange
        preprocessed_image_path = os.path.join(input_data_path,
                                               'HW4-cropped_text.jpg')
        bounding_box_coordinates = None

        gray = cv2.cvtColor(
            cv2.imread(preprocessed_image_path),
            cv2.COLOR_BGR2GRAY)

        thresh = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        expected_output_path = os.path.join(
            expect_data_path,
            'HW4_line_segments_non_filtered.json')
        with open(expected_output_path, 'r') as f:
            expected_output = json.load(f)

        # act
        result = detect_line_segments(
            'pid_id',
            thresh,
            781, 1388,
            5, 5, None, 0.1, 1080,
            bounding_box_coordinates
        )

        # assert that the result is not empty
        assert len(result) > 0

        # assert that the expected line segments are all returned
        result = [elem.dict() for elem in result]
        assert result == expected_output

    def test_lines_touching_bounding_box(self):
        # arrange
        preprocessed_image_path = os.path.join(input_data_path,
                                               's1_3.png')
        # read image into nd.array
        img = cv2.imread(preprocessed_image_path, cv2.IMREAD_GRAYSCALE)

        bounding_box_coordinates = BoundingBox(
            topX=0.0,
            topY=0.0,
            bottomX=1052.0,
            bottomY=1401.0
        )

        expected_output_path = os.path.join(expect_data_path,
                                            's1_3_line-detection.json')
        with open(expected_output_path, 'r') as f:
            expected_output = json.load(f)

        height = 1401
        width = 1052
        # act
        result = detect_line_segments(
            'pid_id',
            img,
            1401, 1052,
            None, 5, 10, 0.1, 1080,
            bounding_box_coordinates
        )

        # assert that the result is not empty
        assert len(result) > 0
        print(len(result))

        # assert that the line segment coordinates are within the bounding box
        for line in result:
            assert line.startX >= bounding_box_coordinates.topX/width
            assert line.startY >= bounding_box_coordinates.topY/height
            assert line.endX <= bounding_box_coordinates.bottomX/width
            assert line.endY <= bounding_box_coordinates.bottomY/height

        # assert that the expected line segments are all returned
        result = [elem.dict() for elem in result]
        assert result == expected_output
