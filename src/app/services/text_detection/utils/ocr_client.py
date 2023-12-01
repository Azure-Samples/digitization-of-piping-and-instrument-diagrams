# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.formrecognizer import AnalysisFeature
from azure.identity import DefaultAzureCredential
from app.config import config


class OcrClient(object):
    '''
    Client for reading text from an image using the Azure Cognitive Services Computer Vision API.
    '''
    def __init__(self, document_analysis_client: DocumentAnalysisClient):
        self._document_analysis_client = document_analysis_client

    def read_text(self, image):
        '''
        Reads text from an image and returns a generator of tuples containing the text and bounding box of each line.
        :param image: Image stream to read in the form of bytes.
        :type image: bytes
        '''
        poller = self._document_analysis_client.begin_analyze_document(
            "prebuilt-read",
            image,
            features=[AnalysisFeature.OCR_HIGH_RESOLUTION])
        result = poller.result()

        if not result:
            raise Exception("No text detected")

        for page in result.pages:
            for line in page.lines:
                yield (line.content, line.polygon)


# Initialize OCR client
document_analysis_client = DocumentAnalysisClient(
    endpoint=config.form_recognizer_endpoint,
    credential=DefaultAzureCredential())

ocr_client = OcrClient(document_analysis_client)
