# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import sys
if sys.modules.get('app.services.graph_persistence.graph_persistence_service') is None:
    from .graph_persistence_service import persist as _persist
    persist = _persist
