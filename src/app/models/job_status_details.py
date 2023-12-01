
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.enums.job_status import JobStatus
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.enums.job_step import JobStep


class JobStatusDetails(BaseModel):
    """
    This class represents the status of a job.
    """
    status: JobStatus
    step: JobStep
    message: Optional[str]
    updated_at: datetime
