# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import random
import networkx as nx
import io
import cv2
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from app.models.image_details import ImageDetails
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.models.enums.flow_direction import FlowDirection
from app.services.draw_elements import draw_annotation_on_image, draw_line
from app.models.line_detection.line_segment import LineSegment
matplotlib.use('pdf')


def draw_persistent_graph_networkx(
        assets: list[ConnectedSymbolsItem],
        file_path: str,
        symbol_label_prefixes_to_include: set[str]):
    """
        Shows the output graph
        :param connectivites: Connectivities
    """
    symbol_label_prefixes_to_include = {prefix.lower() for prefix in symbol_label_prefixes_to_include}
    g = nx.DiGraph()
    # Only add assets to this graph view if they are in the set of symbol label prefixes to include
    for asset in assets:
        if asset.label.lower().startswith(tuple(symbol_label_prefixes_to_include)):
            g.add_node(asset.id, **asset.dict())

    # Only add edges between assets if they are in the set of symbol label prefixes to include
    # Only include edges where FlowDirection is unknown or downstream - this ensures that we don't
    # include upstream connections as those should already be captured in the graph.
    for asset in assets:
        if asset.label.lower().startswith(tuple(symbol_label_prefixes_to_include)):
            for connected_asset in asset.connections:
                if connected_asset.label.lower().startswith(tuple(symbol_label_prefixes_to_include)) \
                  and (connected_asset.flow_direction == FlowDirection.unknown or
                       connected_asset.flow_direction == FlowDirection.downstream):
                    g.add_edge(asset.id, connected_asset.id)

    # color map for nodes
    # current categories: Equipment, Valve, Connector, Indicator
    color_map = {
        'Equipment/': 'blue',
        'Instrument/Valve/': 'yellow',
        'Piping/Endpoint/Pagination': 'green',
        'Instrument/Indicator/': 'red'}
    node_colors = []

    # dictionary of nodes and their text
    labels = {}

    for n, attrs in g.nodes(data=True):
        # Extract text associated with each node
        labels[n] = attrs[SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY]

        # Construct list of colors to classify nodes by symbol category
        # Note that color map corresponds to prefixes of symbol labels
        symbol_category = attrs[SymbolNodeKeysConfig.LABEL_KEY]
        set_color = False
        for prefix in color_map:
            if symbol_category.lower().startswith(prefix.lower()):
                node_colors.append(color_map[prefix])
                set_color = True
                break

        if not set_color:
            node_colors.append('black')  # if symbol category is not in color map, set color to black

    fig, ax = plt.subplots(1, 1, squeeze=True)

    pos = nx.spring_layout(g, k=3, iterations=50)
    nx.draw_networkx(g,
                     pos=pos,
                     ax=ax,
                     with_labels=True,
                     labels=labels,
                     node_color=node_colors,
                     node_size=250,
                     font_size=14,)

    buf = io.BytesIO()

    plt.gcf().set_size_inches(12, 8)
    fig.savefig(buf, format="png")

    image = cv2.imdecode(np.frombuffer(buf.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    cv2.imwrite(file_path, image)


def draw_persistent_graph_annotated(
        assets: list[ConnectedSymbolsItem],
        pid_image: bytes,
        image_details: ImageDetails,
        output_file_path: str):
    '''
        Draws the computed graph connected on top of the input PID image.
        :param assets: List of assets (result of graph construction step)
        :param pid_image: PID image in bytes
        :param image_details: Image details
        :param output_file_path: Output file path
  '''

    img = cv2.imdecode(np.frombuffer(pid_image, np.uint8), cv2.IMREAD_COLOR)

    # All assets are included in this debug view - this can be tuned in the future
    for asset in assets:
        # Generate a random color for each asset and all its connected paths
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255))

        # Draw asset bounding box - this will draw all recognized assets
        draw_annotation_on_image(asset.id,
                                 img,
                                 image_details,
                                 asset.bounding_box,
                                 asset.text_associated,
                                 None,
                                 color,
                                 color)

        # Draw lines for all the connections
        # Note that this doesn't show in the same color what assets are connected to each other,
        # but rather the line segments that were detected for each asset
        for connected_asset in asset.connections:

            for segment in connected_asset.segments:

                # Draw a line on the image for each segment
                # Note that this will render the non-terminal symbols that are part of a path
                # as a diagonal line (from the top left to bottom right corner). This
                # is intentional to disambiguate between the assets starting the path and the
                # non-terminal symbols that are part of the path.
                line_segment = LineSegment(startX=segment.bottomX, startY=segment.bottomY, endX=segment.topX, endY=segment.topY)
                draw_line(img,
                          image_details,
                          line_segment,
                          color)

    cv2.imwrite(output_file_path, img)
