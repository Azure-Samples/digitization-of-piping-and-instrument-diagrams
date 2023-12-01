# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.bounding_box import BoundingBox


class TextRecognized(BoundingBox):
    """"
    Class that represents the text detected properties
    """
    text: str
