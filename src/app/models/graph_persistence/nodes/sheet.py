
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.graph_persistence.nodes.base_node import BaseNode


class Sheet(BaseNode):
    '''This class represents sheet nodes in the graph database.'''
    name: str
