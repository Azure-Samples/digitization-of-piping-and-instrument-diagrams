# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from pydantic import BaseModel, validator


class AssetType(BaseModel):
    '''This class represents the Asset Type node in the graph database.'''
    uniquestring: str = None

    @property
    def category(self) -> str:
        return self.uniquestring.split('/')[0]

    @property
    def subcategory(self) -> str:
        return self.uniquestring.split('/')[1]

    @property
    def displayname(self) -> str:
        return self.uniquestring.split('/')[2]

    @validator('uniquestring')
    def validate_uniquestring(cls, value):
        parts = value.split('/')

        if len(parts) != 3:
            raise ValueError(f'Asset Type label must be in the form of "category/subcategory/displayname". Got "{value}".')

        return value
