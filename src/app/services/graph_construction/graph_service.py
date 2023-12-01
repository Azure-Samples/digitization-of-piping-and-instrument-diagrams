# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import cv2
import networkx as nx
from logger_config import get_logger
from app.models.enums.graph_node_type import GraphNodeType
from app.models.enums.flow_direction import FlowDirection
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig
from app.models.image_details import ImageDetails
from app.models.line_detection.line_segment import LineSegment
from app.services.draw_elements import draw_annotation_on_image, draw_line
from app.models.bounding_box import BoundingBox
from app.config import config
from app.models.graph_construction.traversal_connection import TraversalConnection
import numpy as np
from typing import Union


logger = get_logger(__name__)


class GraphService:
    def __init__(self, G: nx.Graph):
        self.G = G

    def add_node(self, node_id: str, node_type: GraphNodeType, **kwargs):
        '''Adds a node to the graph

        :param node_id: The id of the node
        :type node_id: str
        :param node_type: The type of the node
        :type node_type: GraphNodeType
        :param kwargs: The additional properties of the node
        :type kwargs: dict
        '''

        if node_type == GraphNodeType.symbol and SymbolNodeKeysConfig.LABEL_KEY not in kwargs:
            raise Exception('Symbol nodes must have a label')

        # deleting the type key from the kwargs to not add duplicate type to node
        # duplicate type attribute will cause an error
        if SymbolNodeKeysConfig.TYPE_KEY in kwargs:
            del kwargs[SymbolNodeKeysConfig.TYPE_KEY]

        kwargs[SymbolNodeKeysConfig.SOURCES_KEY] = set()

        self.G.add_node(node_id, type=node_type, **kwargs)

    def add_edge(self, node_id_1: str, node_id_2: str, **kwargs):
        '''Adds an edge to the graph

        :param node_id_1: The id of the first node
        :type node_id_1: str
        :param node_id_2: The id of the second node
        :type node_id_2: str
        '''
        self.G.add_edge(node_id_1, node_id_2, **kwargs)

    def get_node(self, node_id: str):
        '''Gets the node from the graph

        :param node_id: The id of the node
        :type node_id: str
        :return: The node
        :rtype: dict
        '''
        return self.G.nodes[node_id]

    def get_degree(self, node_id: str):
        '''Gets the degree of the node

        :param node_id: The id of the node
        :type node_id: str
        :return: The degree of the node
        :rtype: int
        '''
        return self.G.degree[node_id]

    def get_symbol_nodes(self):
        '''Gets the symbol nodes from the graph

        :return: The symbol nodes
        :rtype: dict
        '''
        nodes = []
        for node_id, node in self.G.nodes(data=True):
            if node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.symbol:
                nodes.append((node_id, node))
        return nodes

    def get_arrow_symbols_at_T_junction(self, arrow_symbol_label: str = config.arrow_symbol_label):
        '''Gets the arrow symbols with high degree

        :param arrow_symbol_label: The label of the arrow symbol
        :type arrow_symbol_label: str
        :return: The arrow symbols with high degree
        :rtype: list
        '''
        degree_criteria = 2
        nodes = self.G.nodes(data=True)

        # getting the arrows with a degree higher than the criteria
        arrow_symbols = [
            node_id for node_id, node in nodes if (
                node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.symbol and
                SymbolNodeKeysConfig.LABEL_KEY in node and
                node[SymbolNodeKeysConfig.LABEL_KEY] == arrow_symbol_label and
                self.get_degree(node_id) > degree_criteria
            )
        ]

        # checking the neighbors of the arrow symbols to see if they are lines
        high_degree_arrow_symbols = []
        for arrow_symbol in arrow_symbols:
            neighbors = self.get_neighbors(arrow_symbol)
            line_count = 0
            for neighbor in neighbors:
                neighbor_node = self.get_node(neighbor)
                if neighbor_node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.line:
                    line_count += 1
            if line_count > degree_criteria:
                high_degree_arrow_symbols.append(arrow_symbol)
        return high_degree_arrow_symbols

    def publish_sources(self, temp_sources_key: str):
        '''Publishes the sources to the source key

        :param temp_source_key: The temporary source key
        :type temp_source_key: str
        '''
        untraceable_node_ids = self._get_untraceable_node_ids(temp_sources_key)
        for untraceable_node_id in untraceable_node_ids:
            node = self.get_node(untraceable_node_id)
            if temp_sources_key in node:
                del node[temp_sources_key]

        nodes = self.G.nodes(data=True)
        for _, node in nodes:
            if temp_sources_key in node:
                node[SymbolNodeKeysConfig.SOURCES_KEY] = node[temp_sources_key]
                del node[temp_sources_key]

    def get_symbol_nodes_by_key(self, key: str, value: str):
        '''Gets the symbol nodes from the graph that match the key criteria

        :return: The symbol nodes
        :rtype: dict
        '''
        nodes = []
        for node_id, node in self.G.nodes(data=True):
            if node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.symbol and node[key] == value:
                nodes.append((node_id, node))
        return nodes

    def get_neighbors(self, node_id: str):
        '''Get the neighboring nodes (connected to the given node)

        :return: The edges
        :rtype: list
        '''
        return list(self.G.neighbors(node_id))

    def get_connected_nodes(
        self,
        starting_node: str,
        asset_symbol_ids: set[str],
        exhaust_paths: bool = False,
        propagation_pass: bool = False,
        junction_arrow_ids: Union[set[str], None] = None,
        arrow_symbol_label: str = config.arrow_symbol_label
    ) -> list[TraversalConnection]:
        '''Traverses the graph from the starting node

        :param starting_node: The id of the starting node
        :type starting_node: str
        :param asset_symbol_ids: The ids of the asset symbols
        :type asset_symbol_ids: set[str]
        :param exhaust_paths: Whether to exhaust all paths or not
        :type exhaust_paths: bool
        :param propagation_pass: Whether this is a propagation pass or not
        :type propagation_pass: bool
        :param junction_arrow_ids: The ids of the junction arrows. The junction arrow ids are only used in the propagation pass
        :type junction_arrow_ids: set[str]
        :param arrow_symbol_label: The label of the arrow symbol
        :type arrow_symbol_label: str
        :return: The list of connected objects with flow direction
        :rtype: list[TraversalConnection]
        '''
        queue = []
        queue.append(TraversalConnection(node_id=starting_node, flow_direction=FlowDirection.unknown))
        visited = {starting_node}
        connected_objects = []

        while queue:
            traversal_connection = queue.pop(0)
            s = traversal_connection.node_id
            flow_direction = traversal_connection.flow_direction
            current_visited_ids = traversal_connection.visited_ids

            neighbors = list(self.G.neighbors(s))
            for neighbor in neighbors:
                if (exhaust_paths and neighbor in current_visited_ids) or \
                        (not exhaust_paths and neighbor in visited) or \
                        neighbor == starting_node:
                    continue

                visited.add(neighbor)

                new_visited_ids = current_visited_ids.copy()
                new_flow_direction = flow_direction
                node = self.G.nodes[neighbor]

                last_node = self.G.nodes[s]
                # checking if flow direction is moving in the wrong direction (upstream)
                if SymbolNodeKeysConfig.SOURCES_KEY in last_node and \
                        neighbor in last_node[SymbolNodeKeysConfig.SOURCES_KEY]:
                    continue

                # checking if flow direction is moving in the right direction (downstream)
                if SymbolNodeKeysConfig.SOURCES_KEY in node and s in node[SymbolNodeKeysConfig.SOURCES_KEY]:
                    new_flow_direction = FlowDirection.downstream
                    if propagation_pass and SymbolNodeKeysConfig.LABEL_KEY in node and \
                            node[SymbolNodeKeysConfig.LABEL_KEY] == arrow_symbol_label and \
                            neighbor in junction_arrow_ids:
                        connected_objects.append(
                            TraversalConnection(node_id=neighbor, flow_direction=new_flow_direction, visited_ids=new_visited_ids)
                        )
                        continue

                # if the neighbor is an asset symbol, add it to the connected objects
                if node[SymbolNodeKeysConfig.TYPE_KEY] == GraphNodeType.symbol and neighbor in asset_symbol_ids:
                    connected_objects.append(
                        TraversalConnection(node_id=neighbor, flow_direction=new_flow_direction, visited_ids=new_visited_ids)
                    )
                    continue

                new_visited_ids.append(neighbor)
                queue.append(TraversalConnection(node_id=neighbor, flow_direction=new_flow_direction, visited_ids=new_visited_ids))

        return connected_objects

    def propagate_flow_direction(self, symbol_node_id: str, traversal_connections: list[TraversalConnection], key: str):
        '''Propagates the flow direction to the connected symbols

        :param symbol_node_id: The id of the symbol
        :type symbol_node_id: str
        :param traversal_connections: The list of connected objects with flow direction
        :type traversal_connections: list[TraversalConnection]
        :param key: The key to use for the source lines
        :type key: str
        '''
        for connected_node in traversal_connections:
            # init the key for all the seen nodes
            for visited in connected_node.visited_ids:
                node = self.get_node(visited)
                if key not in node:
                    node[key] = node[SymbolNodeKeysConfig.SOURCES_KEY].copy()

            node = self.get_node(connected_node.node_id)
            if key not in node:
                node[key] = node[SymbolNodeKeysConfig.SOURCES_KEY].copy()

            # check if the flow direction is unknown
            if connected_node.flow_direction == FlowDirection.unknown.value:
                continue

            last = symbol_node_id
            for visited in connected_node.visited_ids:
                node = self.get_node(visited)
                node[key].add(last)
                last = visited

            node = self.get_node(connected_node.node_id)
            node[key].add(last)

    def draw_graph(self, image_details: ImageDetails, pid_image: bytes, file_path: str):
        """
        This function will draw the graph based on line and symbol locations and save it to the file path.
        """
        img = cv2.imdecode(np.frombuffer(pid_image, np.uint8), cv2.IMREAD_COLOR)

        for node in self.G.nodes(data=True):
            node_info = node[1]
            node_type = node_info['type']

            color = (0, 155, 0)

            if node_type == GraphNodeType.symbol:
                draw_annotation_on_image(node_info['id'],
                                         img,
                                         image_details,
                                         BoundingBox(
                                              topX=node_info['topX'],
                                              bottomX=node_info['bottomX'],
                                              topY=node_info['topY'],
                                              bottomY=node_info['bottomY'],
                                         ),
                                         node_info['text_associated'],
                                         None,
                                         color,
                                         color)
            else:
                draw_line(
                    img,
                    image_details,
                    LineSegment(
                        startX=node_info['startX'],
                        endX=node_info['endX'],
                        startY=node_info['startY'],
                        endY=node_info['endY']),
                    color)

        cv2.imwrite(file_path, img)

    def _get_untraceable_node_ids(self, source_key: str):
        '''Gets the untraceable nodes from the graph

        :param source_key: The source key to check for
        :type source_key: str'''

        node_ids: list[str] = []
        for node_id, node in self.G.nodes(data=True):
            blocking = True
            sources = node.get(source_key, set())

            # we could check the following:
            # if not sources or len(sources) < 2:
            #     continue
            # The reason not to is because a node of degree 1 can have the wrong assignment to make the node untraceable
            # so in this case, we still perform the check below

            for source in sources:
                source_node = self.get_node(source)
                if source_key not in source_node:  # not blocking since the node is not in the source
                    blocking = False
                    break
                if node_id not in source_node[source_key]:  # not blocking since the node is not in the source
                    blocking = False
                    break
            if blocking:
                node_ids.append(node_id)

        return node_ids
