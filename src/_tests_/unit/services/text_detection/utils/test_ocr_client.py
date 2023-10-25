from azure.ai.formrecognizer import AnalysisFeature
import os
import unittest
from unittest.mock import MagicMock
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from app.services.text_detection.utils.ocr_client import OcrClient


class TestReadText(unittest.IsolatedAsyncioTestCase):
    def test_happy_path(self):
        # arrange
        ocr_client = OcrClient(MagicMock())

        image = b"test_image"

        line_1 = MagicMock()
        line_1.content = "test_text"
        line_1.polygon = [[1, 2], [3, 4], [5, 6], [7, 8]]

        line_2 = MagicMock()
        line_2.content = "test_text_2"
        line_2.polygon = [[9, 10], [11, 12], [13, 14], [15, 16]]

        page_1 = MagicMock()
        page_1.lines = [line_1, line_2]
        result = MagicMock()
        result.pages = [page_1]

        poller = MagicMock()
        poller.result.return_value = result
        ocr_client._document_analysis_client.begin_analyze_document.return_value = poller

        # act
        result = ocr_client.read_text(image)

        # assert
        actual_results = list(result)
        self.assertEqual(actual_results, [("test_text", [[1, 2], [3, 4], [5, 6], [7, 8]]), ("test_text_2", [[9, 10], [11, 12], [13, 14], [15, 16]])])
        ocr_client._document_analysis_client.begin_analyze_document.assert_called_once_with(
            "prebuilt-read",
            image,
            features=[AnalysisFeature.OCR_HIGH_RESOLUTION])

    def test_when_no_result_from_poller_then_raises_exception(self):
        # arrange
        ocr_client = OcrClient(MagicMock())

        image = b"test_image"

        poller = MagicMock()
        poller.result.return_value = None
        ocr_client._document_analysis_client.begin_analyze_document.return_value = poller

        # act
        with self.assertRaises(Exception) as context:
            list(ocr_client.read_text(image))

        # assert
        self.assertEqual(str(context.exception), "No text detected")
        ocr_client._document_analysis_client.begin_analyze_document.assert_called_once_with(
            "prebuilt-read",
            image,
            features=[AnalysisFeature.OCR_HIGH_RESOLUTION])

