import sys
if sys.modules.get('app.services.line_detection_service') is None:
    from .line_detection_service import detect_lines as _detect_lines
    detect_lines = _detect_lines
