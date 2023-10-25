import sys
if sys.modules.get('app.services.symbol_detection.symbol_detection_service') is None:
    from .symbol_detection_service import run_inferencing as _run_inferencing
    run_inferencing = _run_inferencing
