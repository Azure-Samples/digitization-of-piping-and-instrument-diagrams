import os
import unittest
import sys
import shapely

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.models.bounding_box import BoundingBox
from app.utils.shapely_utils import is_high_overlap, is_high_overlap_in_horizontal_region, is_high_overlap_in_vertical_region, horizontal_shape_padding, vertical_shape_padding


class TestIsHighOverlap(unittest.TestCase):
    def test_no_intersection_returns_false(self):
        # arrange
        polygon1 = shapely.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        polygon2 = shapely.Polygon([(2, 2), (2, 3), (3, 3), (3, 2)])

        expect = False

        # act
        result = is_high_overlap(polygon1, polygon2, 0.5)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_intersection_is_less_than_threshold_returns_false(self):
        # arrange
        polygon1 = shapely.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        polygon2 = shapely.Polygon([(0.5, 0), (0.5, 1), (1.5, 1), (1.5, 0)])

        expect = False

        # act
        result = is_high_overlap(polygon1, polygon2, 0.5)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_intersection_is_greater_than_threshold_returns_true(self):
        # arrange
        polygon1 = shapely.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        polygon2 = shapely.Polygon([(0.5, 0), (0.5, 1), (1.5, 1), (1.5, 0)])

        expect = True

        # act
        result = is_high_overlap(polygon1, polygon2, 0.49)

        # assert
        self.assertEqual(expect, result)


class TestIsHighOverlapInHorizontalRegion(unittest.TestCase):
    def test_no_overlap_returns_false(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.1, 0.0), (0.2, 0.0), (0.2, 0.1), (0.1, 0.1)])

        expect = False

        # act
        result = is_high_overlap_in_horizontal_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_overlap_is_zero_returns_true(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.0, 0.1), (0.1, 0.1), (0.1, 0.2), (0.0, 0.2)])

        expect = True

        # act
        result = is_high_overlap_in_horizontal_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_overlap_is_not_zero_and_is_less_than_threshold_returns_true(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.05, 0.1), (0.1, 0.1), (0.1, 0.2), (0.05, 0.2)])

        expect = True

        # act
        result = is_high_overlap_in_horizontal_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)


class TestIsHighOverlapInVerticalRegion(unittest.TestCase):
    def test_no_overlap_returns_false(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.0, 0.1), (0.1, 0.1), (0.1, 0.2), (0.0, 0.2)])

        expect = False

        # act
        result = is_high_overlap_in_vertical_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_overlap_is_zero_returns_true(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.1, 0.0), (0.2, 0.0), (0.2, 0.1), (0.1, 0.1)])

        expect = True

        # act
        result = is_high_overlap_in_vertical_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)

    def test_when_ratio_of_overlap_is_not_zero_and_is_less_than_threshold_returns_true(self):
        # arrange
        polygon1 = shapely.Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)])
        polygon2 = shapely.Polygon([(0.1, 0.05), (0.2, 0.05), (0.2, 0.1), (0.1, 0.1)])

        expect = True

        # act
        result = is_high_overlap_in_vertical_region(polygon1, polygon2, 0.3)

        # assert
        self.assertEqual(expect, result)


class TestHorizontalShapePadding(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        bounding_box = BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)

        # act
        result = horizontal_shape_padding(bounding_box, 0.1)

        # assert
        expect = shapely.Polygon([(-0.05, 0.0), (0.15, 0.0), (0.15, 0.1), (-0.05, 0.1), (-0.05, 0.0)])
        self.assertTrue(expect, result)


class TestVerticalShapePadding(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        bounding_box = BoundingBox(topX=0.0, topY=0.0, bottomX=0.1, bottomY=0.1)

        # act
        result = vertical_shape_padding(bounding_box, 0.1)

        # assert
        expect = shapely.Polygon([(0.0, -0.05), (0.1, -0.05), (0.1, 0.15), (0.0, 0.15), (0.0, -0.05)])
        self.assertTrue(expect, result)
