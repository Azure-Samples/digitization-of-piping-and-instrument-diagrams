# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from app.services import storage_path_template_builder
from app.models.enums.inference_result import InferenceResult

class TestBuildImagePath(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        pid_id = 'pid-id'

        # act
        result = storage_path_template_builder.build_image_path(pid_id, InferenceResult.symbol_detection)

        # assert
        self.assertEqual(result, f'{pid_id}/symbol-detection/{pid_id}.png')


class TestBuildDebugImagePath(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        pid_id = 'pid-id'

        # act
        result = storage_path_template_builder.build_debug_image_path(pid_id, InferenceResult.symbol_detection)

        # assert
        self.assertEqual(result, f'{pid_id}/symbol-detection/debug_{pid_id}.png')

    def test_happy_path_with_postfix(self):
        # arrange
        pid_id = 'pid-id'
        postfix = 'symbols_and_text'

        # act
        result = storage_path_template_builder.build_debug_image_path(pid_id, InferenceResult.text_detection, postfix)

        # assert
        self.assertEqual(result, f'{pid_id}/text-detection/debug_{pid_id}_{postfix}.png')


class TestBuildInferenceResponsePath(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        pid_id = 'pid-id'
        inference_result = InferenceResult.symbol_detection

        # act
        result = storage_path_template_builder.build_inference_response_path(pid_id, inference_result)

        # assert
        self.assertEqual(result, f'{pid_id}/symbol-detection/response.json')

class TestBuildInferenceRequestPath(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        pid_id = 'pid-id'
        inference_result = InferenceResult.symbol_detection

        # act
        result = storage_path_template_builder.build_inference_request_path(pid_id, inference_result)

        # assert
        self.assertEqual(result, f'{pid_id}/symbol-detection/request.json')

class TestBuildInferenceJobStatusPath(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        pid_id = 'pid-id'
        inference_result = InferenceResult.graph_construction

        # act
        result = storage_path_template_builder.build_inference_job_status_path(pid_id, inference_result)

        # assert
        self.assertEqual(result, f'{pid_id}/graph-construction/job_status.json')