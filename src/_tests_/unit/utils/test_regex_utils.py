# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
import sys
import parameterized

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.utils.regex_utils import (
    does_string_contain_only_one_number_or_one_fraction,
    does_string_contain_at_least_one_number_and_one_letter,
    is_symbol_text_invalid
)


class TestDoesStringContainOnlyOneNumberOrOneFraction(unittest.TestCase):
    @parameterized.parameterized.expand([
        (' 1 '),
        (' 3/4 '),
        ('22'),
        ('1/12'),
    ])
    def test_happy_path(self, string: str):
        # arrange

        # act
        result = does_string_contain_only_one_number_or_one_fraction(string)

        # assert
        self.assertEqual(result, True)


    @parameterized.parameterized.expand([
        ('abc'),
        ('abc123'),
        ('abc 123 def'),
        ('123 abc'),
    ])
    def test_without_number_or_fraction(self, string: str):
        # arrange

        # act
        result = does_string_contain_only_one_number_or_one_fraction(string)

        # assert
        self.assertEqual(result, False)


class TestDoesStringContainAtLeastOneNumberAndOneLetter(unittest.TestCase):
    @parameterized.parameterized.expand([
        (' abc123 '),
        ('123abc'),
        ('abc123abc'),
        ('123abc123'),
        ('123ABC'),
        (' ABC123 '),
        ('ABC123abc!'),
        ('$#&*(abc123'),
    ])
    def test_happy_path(self, string: str):
        # arrange

        # act
        result = does_string_contain_at_least_one_number_and_one_letter(string)

        # assert
        self.assertEqual(result, True)

    @parameterized.parameterized.expand([
        ('123'),
        (' !@#123 '),
        ('123!@#'),
    ])
    def test_string_without_letters(self, string: str):
        # arrange

        # act
        result = does_string_contain_at_least_one_number_and_one_letter(string)

        # assert
        self.assertEqual(result, False)

    @parameterized.parameterized.expand([
        ('abc'),
        ('ABC'),
        (' abcABC '),
        ('abcABC!'),
        (' $#&*(abc '),
    ])
    def test_string_without_numbers(self, string: str):
        # arrange

        # act
        result = does_string_contain_at_least_one_number_and_one_letter(string)

        # assert
        self.assertEqual(result, False)

    @parameterized.parameterized.expand([
        (''),
        (' '),
    ])
    def test_string_empty(self, string: str):
        # arrange

        # act
        result = does_string_contain_at_least_one_number_and_one_letter(string)

        # assert
        self.assertEqual(result, False)

class TestIsSymbolTextInvalid(unittest.TestCase):
    @parameterized.parameterized.expand([
        ('2"'),
        ('3/4"'),
        ('3/4%'),
        ('3/4"x1/2"'),
        ('1" x 2"'),
        ('1"x2"'),
        ('1"x2'),
        ('1x2"'),
        ('1x1'),
        ('123"X456"'),
        ('12/34"x56/78"'),
        ('12/34" x 56'),
    ])
    def test_when_invalid_symbol_name_returns_true(self, string: str):
        # arrange

        # act
        result = is_symbol_text_invalid(string)

        # assert
        self.assertEqual(result, True)

    @parameterized.parameterized.expand([
        ("Symbol 123"),
        ("11"),
        ("3/4"),
        ("sample 1x1"),
        ('test 12/34" x 56'),
        ('test 1" x 2"'),
    ])
    def test_when_valid_symbol_name_returns_false(self, string: str):
        # arrange

        # act
        result = is_symbol_text_invalid(string)

        # assert
        self.assertEqual(result, False)
