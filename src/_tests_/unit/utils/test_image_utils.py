import os
import unittest
import sys
import pytest

from app.models.bounding_box import BoundingBox
from app.utils.image_utils import get_image_dimensions, is_data_element_within_bounding_box, validate_normalized_bounding_box

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestGetImageDimensions(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        image_path = os.path.join(os.path.dirname(__file__), 'data', 'input', 'image.png')
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        # act
        result = get_image_dimensions(image_bytes)

        # assert
        self.assertEqual(result, (768, 1110))


class TestValidateNormalizedBoundingBox(unittest.IsolatedAsyncioTestCase):
    def test_valid_bounding_box_does_not_raise_error(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.0, bottomX=1.0, bottomY=1.0)

        # act
        result = validate_normalized_bounding_box(bounding_box_inclusive)

        # assert
        self.assertEqual(result, None)

    async def test_invalid_bounding_box_raises_value_error(self):
        # arrange
        bounding_box_inclusive_denormalized = BoundingBox(topX=0.0, topY=0.0, bottomX=2.0, bottomY=2.0)
        bounding_box_inclusive_coords_wrong_order = BoundingBox(bottomX=0.0, bottomY=0.0, topX=1.0, topY=1.0)

        # act
        with pytest.raises(Exception) as e1:
            await validate_normalized_bounding_box(bounding_box_inclusive_denormalized)

        with pytest.raises(Exception) as e2:
            await validate_normalized_bounding_box(bounding_box_inclusive_coords_wrong_order)

        # assert
        assert e1.type == ValueError
        assert 'Invalid bounding_box_inclusive coordinates. Normalized coordinates must be between 0 and 1.' in str(e1.value)

        assert e2.type == ValueError
        assert 'Invalid bounding_box_inclusive coordinates. Normalized coordinates must be between 0 and 1.' in str(e2.value)


class TestValidateDataElementInclusion(unittest.TestCase):
    def test_to_include(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.0, bottomX=1.0, bottomY=1.0)
        topX = 0.0
        topY = 0.0
        bottomX = 0.6
        bottomY = 0.5

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, True)

    def test_to_not_include_case1(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.0, bottomX=0.5, bottomY=0.5)
        topX = 0.0
        topY = 0.0
        bottomX = 0.6
        bottomY = 0.5

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, False)

    def test_to_not_include_case2(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.0, bottomX=0.5, bottomY=0.5)
        topX = 0.0
        topY = 0.0
        bottomX = 0.3
        bottomY = 0.6

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, False)

    def test_to_not_include_case3(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.0, topY=0.7, bottomX=0.5, bottomY=0.5)
        topX = 0.0
        topY = 0.6
        bottomX = 0.3
        bottomY = 0.4

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, False)

    def test_to_not_include_case4(self):
        # arrange
        bounding_box_inclusive = BoundingBox(topX=0.5, topY=0.5, bottomX=0.5, bottomY=0.5)
        topX = 0.6
        topY = 0.1
        bottomX = 0.3
        bottomY = 0.4

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, False)

    def test_with_empty_bounding_box(self):
        # arrange
        bounding_box_inclusive = None
        topX = 0.1
        topY = 0.1
        bottomX = 0.6
        bottomY = 0.5

        # act
        result = is_data_element_within_bounding_box(bounding_box_inclusive, topX, topY, bottomX, bottomY)

        # assert
        self.assertEqual(result, True)
