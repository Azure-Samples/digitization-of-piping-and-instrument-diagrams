# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from typing import Optional
from app.models.graph_persistence.nodes.base_node import BaseNode


class Connector(BaseNode):
    '''This class represents Connector nodes in the graph database.'''
    text_associated: Optional[str] = None
