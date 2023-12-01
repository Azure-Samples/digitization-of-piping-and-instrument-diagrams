# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.enums.inference_result import InferenceResult
from typing import Optional


def build_image_path(pid_id: str, inference_result: InferenceResult) -> str:
    '''Builds the base image storage path for the given pid id and image name.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    :return: The base image storage path.
    :rtype: str'''
    return f'{pid_id}/{inference_result}/{pid_id}.png'


def build_debug_image_path(pid_id: str, inference_result: InferenceResult, postfix: Optional[str] = None) -> str:
    '''Builds the debug image storage path for the given pid id and image name.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    :param postfix: The postfix to append to the debug image name.
    :type postfix: Optional[str]
    :return: The debug image storage path.
    :rtype: str'''
    if postfix is None:
        return f'{pid_id}/{inference_result}/debug_{pid_id}.png'
    else:
        return f'{pid_id}/{inference_result}/debug_{pid_id}_{postfix}.png'


def build_inference_request_path(pid_id: str, inference_result: InferenceResult) -> str:
    '''Builds the inference request storage path for the given pid id.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    :return: The inference request storage path.
    :rtype: str'''
    return f'{pid_id}/{inference_result}/request.json'


def build_inference_response_path(pid_id: str, inference_result: InferenceResult, postfix: Optional[str] = None) -> str:
    '''Builds the inference response storage path for the given pid id.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    :return: The inference response storage path.
    :rtype: str'''
    if postfix is None:
        return f'{pid_id}/{inference_result}/response.json'
    else:
        return f'{pid_id}/{inference_result}/response_{postfix}.json'


def build_inference_job_status_path(pid_id: str, inference_result: InferenceResult) -> str:
    '''Builds the inference job status storage path for the given pid id.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    :return: The inference job status storage path.
    :rtype: str'''
    return f'{pid_id}/{inference_result}/job_status.json'


def build_output_image_path(pid_id: str, inference_result: InferenceResult, postfix: Optional[str] = None) -> str:
    '''Builds the output image storage path for the given pid id, inference result type and detection step.

    :param pid_id: The pid id of the request.
    :type pid_id: str
    :param inference_result: The inference result type.
    :type inference_result: InferenceResult
    '''
    return f'{pid_id}/{inference_result}/output_{pid_id}_{postfix}.png'
