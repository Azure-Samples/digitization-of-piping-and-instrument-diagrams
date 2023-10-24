import os
import sys
import unittest

from app.models.bounding_box import BoundingBox
from app.models.text_detection.text_recognized import TextRecognized
from app.services.graph_construction.remove_text_outside_main_inclusive_box \
    import remove_text_outside_main_inclusive_box

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                             '..'))

input_data_path = os.path.join(os.path.dirname(__file__), 'data', 'input')


class TestRemoveText(unittest.TestCase):
    def test_filter_by_bounding_box_with_text_list(self):
        bounding_box = BoundingBox(topX=0, topY=0, bottomX=100, bottomY=100)
        text_list = [
            TextRecognized(topX=50, topY=50, bottomX=80, bottomY=80,
                           text="text1"),
            TextRecognized(topX=110, topY=110, bottomX=130, bottomY=130,
                           text="text2"),
            TextRecognized(topX=20, topY=20, bottomX=30, bottomY=30,
                           text="text3"),
        ]
        expected_result = [
            TextRecognized(topX=50, topY=50, bottomX=80, bottomY=80,
                           text="text1"),
            TextRecognized(topX=20, topY=20, bottomX=30, bottomY=30,
                           text="text3"),
        ]

        result = remove_text_outside_main_inclusive_box(bounding_box,
                                                        text_list)

        self.assertEqual(result, expected_result)

    def test_filter_by_bounding_box_with_none_bounding_box(self):
        bounding_box = None
        text_list = [
            TextRecognized(topX=50, topY=50, bottomX=80, bottomY=80,
                           text="text1"),
            TextRecognized(topX=110, topY=110, bottomX=130, bottomY=130,
                           text="text2"),
            TextRecognized(topX=20, topY=20, bottomX=30, bottomY=30,
                           text="text3"),
        ]
        expected_result = text_list

        result = remove_text_outside_main_inclusive_box(bounding_box,
                                                        text_list)

        self.assertEqual(result, expected_result)
