# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from enum import Enum


class JobStatus(str, Enum):
    '''Enum for the job status type'''
    submitted = "submitted"
    in_progress = "in_progress"
    done = "done"
    failure = "failure"
