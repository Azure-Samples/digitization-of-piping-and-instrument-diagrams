import argparse
import networkx as nx
from app.models.enums.graph_node_type import GraphNodeType
import logger_config
from app.config import config
from app.models.graph_construction.graph_construction_request import GraphConstructionInferenceRequest
from app.models.line_detection.line_detection_response import LineDetectionInferenceResponse
from app.models.line_detection.line_segment import LineSegment
from .find_symbol_connectivities import find_symbol_connectivities
from .pre_find_symbol_connectivities import pre_find_symbol_connectivities
from .post_find_symbol_connectivities import post_find_symbol_connectivities
from .connect_lines_with_closest_elements import connect_lines_with_closest_elements
from .connect_lines_with_arrows import connect_lines_with_arrows
from .remove_text_outside_main_inclusive_box import remove_text_outside_main_inclusive_box
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.services.graph_construction.utils.normalize_config import normalize_pixel_config_value
from .extend_lines import extend_lines
from .create_line_connection_candidates import create_line_connection_candidates
from .connect_symbols_that_are_close import connect_symbols_that_are_close
from .graph_service import GraphService
from .utils.id_builder_util import create_node_id
from .draw_persistent_graph import draw_persistent_graph_networkx, draw_persistent_graph_annotated
import time

logger = logger_config.get_logger(__name__)


def construct_graph(
            pid_id: str,
            pid_image: bytes,
            text_detection_results: GraphConstructionInferenceRequest,
            line_detection_results: LineDetectionInferenceResponse,
            output_image_graph_path: str,
            debug_image_graph_connections_path: str,
            debug_image_graph_with_lines_and_symbols_path: str,
            symbol_label_prefixes_to_include_in_graph_image_output: set[str]):
    """
        Constructs the graph from the text detection and line detection results
        :param pid_id: PID ID
        :param pid_image: PID image
        :param text_detection_results: Text detection results
        :param line_detection_results: Line detection results
        :param output_image_graph_path: Debug image graph path
        :param debug_image_graph_with_lines_path: Debug image graph with lines path
        :param debug_image_graph_with_lines_and_symbols_path: Debug image graph with lines and symbols path
        :param symbol_label_prefixes_to_include_in_graph_image_output: Symbol label prefixes to include in graph image output
    """
    starting_time = time.time()

    # Required pre-processing step: normalize pixel config values to [0, 1] inclusive for use in later calculations
    # Note that this is needed since these values are provided in the config as absolute pixel values,
    # but later calculations use bounding box coordinates normalized by image width/height.
    image_width = line_detection_results.image_details.width
    image_height = line_detection_results.image_details.height
    norm_line_segment_padding_default = config.line_segment_padding_default
    norm_graph_distance_threshold_for_symbols = normalize_pixel_config_value(config.graph_distance_threshold_for_symbols_pixels,
                                                                             image_width,
                                                                             image_height)
    norm_graph_distance_threshold_for_text = normalize_pixel_config_value(config.graph_distance_threshold_for_text_pixels,
                                                                          image_width,
                                                                          image_height)
    norm_graph_distance_threshold_for_lines = normalize_pixel_config_value(config.graph_distance_threshold_for_lines_pixels,
                                                                           image_width,
                                                                           image_height)
    norm_graph_line_buffer = normalize_pixel_config_value(config.graph_line_buffer_pixels,
                                                          image_width,
                                                          image_height)
    norm_graph_symbol_to_symbol_distance_threshold = normalize_pixel_config_value(config.graph_symbol_to_symbol_distance_threshold_pixels,
                                                                                  image_width,
                                                                                  image_height)

    # step 1: extending the lines
    logger.debug("Step 1: Extending the line up to max width and height of the image...")
    start_time = time.time()
    extended_lines = extend_lines(line_detection_results.line_segments, norm_line_segment_padding_default)
    end_time = time.time()
    logger.debug(f"Step 1: Total time taken for extending the lines: {end_time - start_time}")

    # step 2: removing all text outside of the main inclusive box
    logger.debug("Step 2: Removing all text outside of the main inclusive box...")
    start_time = time.time()
    text_results = remove_text_outside_main_inclusive_box(
        text_detection_results.bounding_box_inclusive,
        text_detection_results.all_text_list)
    end_time = time.time()
    logger.debug(f"Step 2: Total time taken for removing all text outside of the main inclusive box: {end_time - start_time}")

    # step 3: initialize the graph
    logger.debug("Step 3: Creating the nodes on the graph...")
    start_time = time.time()
    graph = initialize_graph(text_detection_results.text_and_symbols_associated_list, line_detection_results.line_segments)
    end_time = time.time()
    logger.debug(f"Step 3: Total time taken for creating the nodes on the graph: {end_time - start_time}")

    # step 4: line with symbol connection
    logger.info("Step 4: Create line start and end connection candidates...")
    start_time = time.time()
    line_connection_candidates = create_line_connection_candidates(
        line_detection_results.line_segments,
        extended_lines,
        text_detection_results.text_and_symbols_associated_list,
        text_results,
        norm_graph_line_buffer,
        norm_graph_distance_threshold_for_symbols,
        norm_graph_distance_threshold_for_text,
        norm_graph_distance_threshold_for_lines,)
    end_time = time.time()
    logger.info(f"Step 4: Total time taken for creating line start and end connection candidates: {end_time - start_time}")

    # step 5: connecting lines with the closest elements
    logger.debug("Step 5: Connecting lines with the closest elements...")
    start_time = time.time()
    connect_lines_with_closest_elements(
        graph,
        line_connection_candidates,
        text_detection_results.all_text_list,
        line_detection_results.line_segments)
    end_time = time.time()
    logger.debug(f"Step 5: Total time taken for connecting lines with the closest elements: {end_time - start_time}")

    # step 6: connecting the symbols that are close
    logger.debug("Step 6: Connecting the symbols that are close")
    start_time = time.time()
    connect_symbols_that_are_close(graph,
                                   text_detection_results.text_and_symbols_associated_list,
                                   norm_graph_symbol_to_symbol_distance_threshold)
    end_time = time.time()
    logger.debug(f"Step 6: Total time taken for connecting the symbols that are close: {end_time - start_time}")

    graph.draw_graph(text_detection_results.image_details, pid_image, debug_image_graph_with_lines_and_symbols_path)

    # step 7: connecting the lines with arrows
    logger.debug("Step 7: Connecting the lines with arrows...")
    start_time = time.time()
    arrow_nodes = connect_lines_with_arrows(graph, line_detection_results.line_segments, extended_lines)
    end_time = time.time()
    logger.debug(f"Step 7: Total time taken for connecting the lines with arrows: {end_time - start_time}")

    # step 8: graph traversal for finding asset connectivities
    logger.info("Step 8: Graph traversal for finding asset connectivities...")
    start_time = time.time()
    pre_find_symbol_connectivities_result = pre_find_symbol_connectivities(graph)
    symbol_connections = find_symbol_connectivities(
        graph,
        pre_find_symbol_connectivities_result,
        text_detection_results.propagation_pass_exhaustive_search)
    asset_connectivities = post_find_symbol_connectivities(
        graph,
        symbol_connections,
        pre_find_symbol_connectivities_result.flow_direction_asset_ids,
        pre_find_symbol_connectivities_result.asset_valve_symbol_ids)
    end_time = time.time()
    logger.info(f"Step 8: Total time taken for graph traversal for finding asset connectivities: {end_time - start_time}")

    draw_persistent_graph_networkx(asset_connectivities,
                                   output_image_graph_path,
                                   symbol_label_prefixes_to_include_in_graph_image_output)

    draw_persistent_graph_annotated(asset_connectivities,
                                    pid_image,
                                    text_detection_results.image_details,
                                    debug_image_graph_connections_path)

    logger.info(f"Total time taken for constructing the graph: {time.time() - starting_time}")
    return (asset_connectivities, arrow_nodes)


def initialize_graph(text_and_symbols_associated_list: list[SymbolAndTextAssociated],
                     line_detection_results: list[LineSegment]) -> GraphService:
    """
        Initializes the graph
        :param text_and_symbols_associated_list: Text and symbols associated list
        :return: Graph
    """
    graph = GraphService(nx.Graph())

    for ls, line_segment in enumerate(line_detection_results):
        dic = line_segment.dict()
        dic['node_type'] = GraphNodeType.line
        node_id = create_node_id(GraphNodeType.line, ls)
        graph.add_node(node_id, **dic)

    for symbol_and_text_associated in text_and_symbols_associated_list:
        dic = symbol_and_text_associated.dict()
        dic['node_type'] = GraphNodeType.symbol
        node_id = create_node_id(GraphNodeType.symbol, symbol_and_text_associated.id)
        graph.add_node(node_id, **dic)

    return graph


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pid-id',
        dest='pid_id',
        type=str,
        default='hw2_sub1',
        help='PID ID'
    )
    parser.add_argument(
        '--image-path',
        dest='image_path',
        type=str,
        help='Original image path'
    )
    parser.add_argument(
        '--line-detection-path',
        dest='line_detection_path',
        type=str,
        help='line detection results path'
    )
    parser.add_argument(
        '--text-detection-path',
        dest='text_detection_path',
        type=str,
        help='text detection results path'
    )
    parser.add_argument(
        '--output-image-graph-path',
        dest='output_image_graph_path',
        type=str,
        help='output image graph path'
    )
    parser.add_argument(
        '--debug-image-graph-connections-path',
        dest='debug_image_graph_connections_path',
        type=str,
        help='debug image graph connections path'
    )
    parser.add_argument(
        '--output-connectivity-json-path',
        dest='output_connectivity_json_path',
        type=str,
        help='output connectivity json path'
    )
    parser.add_argument(
        '--debug-image-graph-with-lines-and-symbols-path',
        dest='debug_image_graph_with_lines_and_symbols_path',
        type=str,
        help='debug image graph with lines and symbols path'
    )
    parser.add_argument(
        '--symbol-label-prefixes-to-include-in-graph-image-output',
        dest='symbol_label_prefixes_to_include_in_graph_image_output',
        type=set[str],
        default={'Equipment/', 'Instrument/Valve/', 'Piping/Endpoint/Pagination'},
        help='symbol label prefixes to include in graph image output'
    )
    parser.add_argument(
        '--propagation-should-use-exhaustive-search',
        dest='propagation_should_use_exhaustive_search',
        action='store_true',
        help='propagation should use exhaustive search'
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    import json
    from app.models.graph_construction.graph_construction_response import GraphConstructionInferenceResponse
    from app.models.image_details import ImageDetails
    args = get_args()

    with open(args.image_path, 'rb') as fimage:
        pid_image = fimage.read()

    with open(args.text_detection_path, 'r') as ftext:
        results = ftext.read()
        text_detection_results = GraphConstructionInferenceRequest.parse_raw(results)

    with open(args.line_detection_path, 'r') as fline:
        results = fline.read()
        line_detection_results = LineDetectionInferenceResponse.parse_raw(results)

    text_detection_results.propagation_pass_exhaustive_search = args.propagation_should_use_exhaustive_search
    asset_connectivities, _ = construct_graph(
        pid_id=args.pid_id,
        pid_image=pid_image,
        text_detection_results=text_detection_results,
        line_detection_results=line_detection_results,
        output_image_graph_path=args.output_image_graph_path,
        debug_image_graph_connections_path=args.debug_image_graph_connections_path,
        debug_image_graph_with_lines_and_symbols_path=args.debug_image_graph_with_lines_and_symbols_path,
        symbol_label_prefixes_to_include_in_graph_image_output=args.symbol_label_prefixes_to_include_in_graph_image_output
    )

    graph_construction_response = GraphConstructionInferenceResponse(
        image_url=args.output_image_graph_path,
        image_details=ImageDetails(
            format='png',
            width=0,
            height=0,
        ),
        connected_symbols=asset_connectivities
    )

    with open(args.output_connectivity_json_path, 'w') as f:
        json.dump(graph_construction_response.dict(), f)
