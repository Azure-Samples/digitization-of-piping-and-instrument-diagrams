# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from app.models.enums.graph_node_type import GraphNodeType
from app.models.line_detection.line_segment import LineSegment
from app.models.text_detection.text_recognized import TextRecognized
from app.services.graph_construction.create_lines import create_line_from_boundingbox
from .graph_service import GraphService


def connect_lines_with_closest_elements(
    graph: GraphService,
    line_connection_candidates: dict,
    all_text: list[TextRecognized],
    line_segments: list[LineSegment],
) -> GraphService:
    """
        Connects lines with closest elements
        :param graph: Graph
        :param line_connection_candidates: Line connection candidates
        :return: Graph
    """
    seen_text_ids = set()
    for line_id in line_connection_candidates:
        candidates = line_connection_candidates[line_id]

        node_line_id = f'l-{line_id}'
        line = line_segments[int(line_id)]

        for candidate in candidates.values():
            if candidate is not None and candidate['type'] != GraphNodeType.unknown:
                if candidate['type'] == GraphNodeType.text:
                    text_id = candidate['node']

                    if text_id not in seen_text_ids:
                        text_info = all_text[int(text_id)]
                        connected_line = create_line_from_boundingbox(text_info, line)
                        connected_node_id = f'l-t-{text_id}'
                        dic = connected_line.dict()
                        dic['node_type'] = GraphNodeType.line
                        graph.add_node(connected_node_id, **dic)

                        # associating text with line
                        line_node = graph.get_node(node_line_id)
                        line_node['text_associated'] = text_info.text

                        seen_text_ids.add(text_id)
                    else:
                        connected_node_id = f'l-t-{text_id}'
                else:
                    if candidate['type'] == GraphNodeType.line:
                        candidate_type = 'l'
                    else:
                        candidate_type = 's'
                    element_id = candidate['node']
                    connected_node_id = f'{candidate_type}-{element_id}'
                graph.add_edge(node_line_id, connected_node_id)

    return graph
