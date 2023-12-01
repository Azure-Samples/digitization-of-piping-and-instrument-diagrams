# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import sys
if sys.modules.get('app.services.graph_construction.graph_construction_service') is None:
    from .graph_construction_service import construct_graph as _construct_graph
    construct_graph = _construct_graph
