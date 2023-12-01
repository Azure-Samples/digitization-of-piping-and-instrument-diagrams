# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel


class BoundingBox(BaseModel):
    """
    This class represents the bounding box of a symbol detected on a P&ID image.
    """
    topX: float
    topY: float
    bottomX: float
    bottomY: float
