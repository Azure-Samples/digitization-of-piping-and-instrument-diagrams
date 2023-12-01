# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel
from app.models.bounding_box import BoundingBox


class BaseConnectedSymbolsItem(BaseModel):
    '''This class represents the base connected symbol'''
    id: int
    label: str
    text_associated: str
    bounding_box: BoundingBox
