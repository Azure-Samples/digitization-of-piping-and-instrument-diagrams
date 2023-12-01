# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.graph_persistence.nodes.base_node import BaseNode


class Asset(BaseNode):
    '''This class represents the Asset node in the graph database.'''
    text_associated: str
