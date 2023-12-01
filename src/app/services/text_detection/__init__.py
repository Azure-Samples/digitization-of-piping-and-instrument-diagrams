# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import sys
if sys.modules.get('app.services.text_detection.text_detection_service') is None:
    from .text_detection_service import run_inferencing as _run_inferencing
    run_inferencing = _run_inferencing
