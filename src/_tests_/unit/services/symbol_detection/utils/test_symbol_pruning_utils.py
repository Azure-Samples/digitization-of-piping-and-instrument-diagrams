# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
import sys

from app.models.bounding_box import BoundingBox
from app.models.symbol_detection.label import Label

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
from app.services.symbol_detection.utils.symbol_pruning_utils import prune_overlapping_symbols


class TestPrintOverlappingSymbols(unittest.TestCase):
    def test_when_no_symbols_overlap_returns_all_symbols(self):
        # arrange
        labels = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=2,
                label='label2',
                score=0.9,
                topX=0.5,
                topY=0.5,
                bottomX=1.0,
                bottomY=1.0
            ),
            Label(
                id=3,
                label='label3',
                score=0.9,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        expect = labels

        # act
        result = prune_overlapping_symbols(labels, 0.5)

        # assert
        self.assertEqual(expect, result)

    def test_when_symbols_overlap_returns_only_symbols_that_dont_overlap(self):
        # arrange
        labels = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=2,
                label='label2',
                score=0.8,
                topX=0.0,
                topY=0.25,
                bottomX=0.5,
                bottomY=0.75
            ),
            Label(
                id=3,
                label='label3',
                score=0.9,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        expect = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=3,
                label='label3',
                score=0.9,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        # act
        result = prune_overlapping_symbols(labels, 0.49)

        # assert
        print(result)
        self.assertEqual(expect, result)

    def test_when_larger_label_with_low_confidence_over_symbols_with_high_confidence_returns_correct_symbols(self):
        # arrange
        labels = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=2,
                label='label2',
                score=0.2,
                topX=0.0,
                topY=0.0,
                bottomX=1.5,
                bottomY=1.5
            ),
            Label(
                id=3,
                label='label3',
                score=0.9,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        expect = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=3,
                label='label3',
                score=0.9,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        # act
        result = prune_overlapping_symbols(labels, 0.49)

        # assert
        print(result)
        self.assertEqual(expect, result)

    def test_with_larger_bounding_box_masks_symbols_with_low_and_high_labels_returns_correct_labels(self):
        # arrange
        labels = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=2,
                label='label2',
                score=0.2,
                topX=0.0,
                topY=0.0,
                bottomX=1.5,
                bottomY=1.5
            ),
            Label(
                id=3,
                label='label3',
                score=0.2,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        expect = [
            Label(
                id=1,
                label='label1',
                score=0.9,
                topX=0.0,
                topY=0.0,
                bottomX=0.5,
                bottomY=0.5
            ),
            Label(
                id=3,
                label='label3',
                score=0.2,
                topX=1.0,
                topY=1.0,
                bottomX=1.5,
                bottomY=1.5
            )
        ]

        # act
        result = prune_overlapping_symbols(labels, 0.49)

        # assert
        print(result)
        self.assertEqual(expect, result)
