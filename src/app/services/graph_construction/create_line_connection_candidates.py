import time
from app.models.line_detection.line_segment import LineSegment
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.text_detection.text_recognized import TextRecognized
from app.models.enums.graph_node_type import GraphNodeType
from app.models.graph_construction.extended_line_segment import ExtendedLineSegment
from app.models.graph_construction.connection_candidate import ConnectionCandidate
from app.config import config
from app.utils import shapely_utils
from logger_config import get_logger
from shapely import Point
import concurrent.futures

logger = get_logger(__name__)


def create_line_connection_candidates(
    line_segments: list[LineSegment],
    extended_lines: list[ExtendedLineSegment],
    text_and_symbols_associated_list: list[SymbolAndTextAssociated],
    text_results: list[TextRecognized],
    graph_line_buffer: float,
    graph_distance_threshold_for_symbols: float,
    graph_distance_threshold_for_text: float,
    graph_distance_threshold_for_lines: float
) -> dict:
    """
        Creates line connection candidates
        :param line_segments: Line segments
        :param extended_lines: Extended lines
        :param text_and_symbols_associated_list: Text and symbols associated list
        :param text_results: Text results
        :return: Line connection candidates
    """
    line_connection_candidates = {}

    if len(line_segments) == 0:
        return line_connection_candidates

    logger.debug('Starting candidate matching on line segments from process file...')
    time_start = time.time()
    logger.info(f'Number of line segments: {len(line_segments)}')
    # data batch size calculation based on the number of worker processes
    batch_size = max(len(line_segments) // config.workers_count_for_data_batch, 1)
    logger.info(f'Number of batches/processes: {batch_size}')

    # Divide line segments into batches so that the batches can be processed in parallel
    logger.info(f'Batch size for each process: {batch_size}')
    lines_batch_data = list(batch(line_segments, batch_size))

    # max workers will depend on the cpu cores available, its advisable to use lesser workers
    # than cpu cores so that current process is not starved of cpu resources
    # and can perform its task efficiently. Each process can use a core depending upon
    # the number of computations it has to perform. Each process will have its own memory space
    # and will not share memory with other processes
    max_workers_count = config.workers_count_for_data_batch

    # Create a ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers_count) as executor:
        # Submit the tasks to the executor so that they get executed in parallel
        futures = []
        for batch_data_index_list in lines_batch_data:
            future = executor.submit(process_line_segments,
                                     batch_data_index_list,
                                     line_segments,
                                     extended_lines,
                                     text_and_symbols_associated_list,
                                     text_results,
                                     graph_line_buffer,
                                     graph_distance_threshold_for_symbols,
                                     graph_distance_threshold_for_text,
                                     graph_distance_threshold_for_lines)
            futures.append(future)

        # Collect the results from futures
        line_connection_candidates = {}
        for future in concurrent.futures.as_completed(futures):
            # data available in the future object is in the same order as the futures list
            # data is returned when the process is completed
            results = future.result()
            for source_line_index, result in results:
                line_connection_candidates[str(source_line_index)] = result

    logger.info(f'***Time taken for candidate matching on line segments***: {time.time() - time_start} seconds')
    return line_connection_candidates


def process_line_segments(batch_data_index_list,
                          line_segments,
                          extended_lines,
                          text_and_symbols_associated_list,
                          text_results,
                          graph_line_buffer,
                          graph_distance_threshold_for_symbols,
                          graph_distance_threshold_for_text,
                          graph_distance_threshold_for_lines):
    '''
    Iterate through batched line segments and find connection candidates in a single process
    :param batch_data_index_list: Batched line segments
    :param line_segments: Line segments detected in image
    :param extended_lines: Extended line segments
    :param text_and_symbols_associated_list: Text and symbols associated list
    :param text_results: Text results
    '''
    matched_candidates = [(0, None)] * len(batch_data_index_list)
    logger.debug(f'***Processing line segments start: {batch_data_index_list}')
    zipLines = list(zip(line_segments, extended_lines))
    # iterate through batched data and find candidate match for each line segment
    for i, source_line_index in enumerate(batch_data_index_list):
        result = process_line_segment(source_line_index,
                                      line_segments[source_line_index],
                                      extended_lines[source_line_index],
                                      text_and_symbols_associated_list,
                                      text_results,
                                      zipLines,
                                      graph_line_buffer,
                                      graph_distance_threshold_for_symbols,
                                      graph_distance_threshold_for_text,
                                      graph_distance_threshold_for_lines)
        matched_candidates[i] = (source_line_index, result)
    logger.debug(f'***Processing line segments end: {batch_data_index_list}')
    return matched_candidates


def process_line_segment(source_line_index,
                         source_line_segment,
                         source_extended_line_segment,
                         text_and_symbols_associated_list,
                         text_results,
                         zipLines,
                         graph_line_buffer,
                         graph_distance_threshold_for_symbols,
                         graph_distance_threshold_for_text,
                         graph_distance_threshold_for_lines):

    # Create polygon for extended line + add padding
    source_line_polygon_extended = shapely_utils.convert_line_to_line_string(source_extended_line_segment)
    # buffer value is added to solve for the horizontal lines that are broken into multiple row lines
    source_line_polygon_extended = source_line_polygon_extended.buffer(graph_line_buffer)

    # Get start/end points
    source_start_point = Point(source_line_segment.startX, source_line_segment.startY)
    source_end_point = Point(source_line_segment.endX, source_line_segment.endY)

    # Construct candidate dict for this line segment - begin logic with empty candidates
    start_connection_candidate = ConnectionCandidate()
    end_connection_candidate = ConnectionCandidate()
    current_connection_candidates = {
        'start': start_connection_candidate.__dict__,
        'end': end_connection_candidate.__dict__
    }

    # Candidate matching: line to symbol
    logger.debug(f'Candidate matching for line {source_line_index} to symbols...')
    for i, symbol_data in enumerate(text_and_symbols_associated_list):
        current_connection_candidates = create_line_connection_candidates_helper(
            symbol_data,
            str(symbol_data.id),
            source_line_polygon_extended,
            source_start_point,
            source_end_point,
            GraphNodeType.symbol,
            graph_distance_threshold_for_symbols,
            current_connection_candidates)

    # Candidate matching: line to text
    logger.debug(f'Candidate matching for line {source_line_index} to text...')
    for i, text_data in enumerate(text_results):
        current_connection_candidates = create_line_connection_candidates_helper(
            text_data,
            str(i),
            source_line_polygon_extended,
            source_start_point,
            source_end_point,
            GraphNodeType.text,
            graph_distance_threshold_for_text,
            current_connection_candidates)

    # Candidate matching: line to line
    logger.debug(f'Candidate matching for line {source_line_index} to lines...')
    for target_line_index, (target_line_segment, target_extended_line_segment) in enumerate(zipLines):
        line_distance_threshold = graph_distance_threshold_for_lines
        current_connection_candidates = create_line_to_line_connection_candidates(
            target_line_segment,
            target_extended_line_segment,
            str(target_line_index),
            str(source_line_index),
            source_line_polygon_extended,
            source_start_point,
            source_end_point,
            current_connection_candidates,
            line_distance_threshold,
            graph_line_buffer)

    # Update line connection candidates
    return current_connection_candidates


def create_line_connection_candidates_helper(
            item,
            id,
            line_polygon_extended,
            start_point,
            end_point,
            node_type,
            category_distance_threshold,
            current_connection_candidates) -> dict:
    '''
    Helper function for create_line_connection_candidates.

    Contains the shared logic for line-to-symbol and line-to-text association - this
    method takes in the information for the current item being evaluated to add
    to the connection candidates, the information about the line segment being evaluated,
    and the current connection candidates dictionary. It then returns the updated
    connection candidates dictionary if the input symbol or text element is closer to the
    start or end point of the line segment than the current value in the connection candidates dict.
    '''
    try:
        if item.topX is None or item.topY is None or item.bottomX is None or item.bottomY is None:
            raise ValueError('Item does not have proper bounding box')
    except AttributeError:
        raise ValueError('Item does not have proper bounding box')

    item_polygon = shapely_utils.bounding_box_to_polygon(item)

    # If no intersection, return current_connection_candidates unchanged
    if not line_polygon_extended.intersects(item_polygon):
        return current_connection_candidates

    # Compute start/end point distances
    start_point_distance = item_polygon.distance(start_point)
    end_point_distance = item_polygon.distance(end_point)

    # Update connection candidates if closer than existing current value or if current value is None
    if start_point_distance <= end_point_distance and \
            (start_point_distance <= category_distance_threshold and
             (current_connection_candidates['start']['distance'] is None or
              start_point_distance < current_connection_candidates['start']['distance'])):
        start_connection_candidate = ConnectionCandidate(
            node=id,
            type=node_type,
            distance=start_point_distance,
            intersection=False
        )
        current_connection_candidates['start'] = start_connection_candidate.__dict__
    elif end_point_distance < start_point_distance and \
            (end_point_distance <= category_distance_threshold and
             (current_connection_candidates['end']['distance'] is None or
              end_point_distance < current_connection_candidates['end']['distance'])):
        end_connection_candidate = ConnectionCandidate(
            node=id,
            type=node_type,
            distance=end_point_distance,
            intersection=False
        )
        current_connection_candidates['end'] = end_connection_candidate.__dict__

    return current_connection_candidates


def create_line_to_line_connection_candidates(
            target_line_item,
            target_extended_line_item,
            target_line_id,
            source_line_id,
            source_line_polygon_extended,
            source_start_point,
            source_end_point,
            current_connection_candidates,
            line_distance_threshold,
            graph_line_buffer):

    # skip if comparing the same line segments
    if target_line_id == source_line_id:
        return current_connection_candidates

    # Convert target line segment and extended line segment to polygons
    target_line_polygon = shapely_utils.convert_line_to_line_string(target_line_item)

    target_line_polygon_extended = shapely_utils.convert_line_to_line_string(target_extended_line_item)

    # Buffer value is added to solve for horizontal lines that are broken into multiple row lines
    target_line_polygon_extended = target_line_polygon_extended.buffer(graph_line_buffer)

    # If the source line and target line do not intersect, return the current connection candidates
    if not source_line_polygon_extended.intersects(target_line_polygon_extended):
        return current_connection_candidates

    target_start_point = Point(target_line_item.startX, target_line_item.startY)
    target_end_point = Point(target_line_item.endX, target_line_item.endY)

    # Calculate distances between source and target line points
    start_point_distance = min(target_start_point.distance(source_start_point), target_end_point.distance(source_start_point))
    end_point_distance = min(target_start_point.distance(source_end_point), target_end_point.distance(source_end_point))
    start_line_distance = target_line_polygon.distance(source_start_point)
    end_line_distance = target_line_polygon.distance(source_end_point)

    # Case 1.
    # Cases 1 and 2 are for when lines are connected either by start or end point (not a junction).
    # Update current_connection_candidates if the start point distance is below the threshold
    # and one of the following is true:
    if start_point_distance <= end_point_distance and \
        start_point_distance < line_distance_threshold and \
            has_update_on_point_distance(current_connection_candidates['start'], start_point_distance):
        connection_candidate = ConnectionCandidate(
            node=target_line_id,
            type=GraphNodeType.line,
            distance=start_point_distance,
            intersection=False
        )
        current_connection_candidates['start'] = connection_candidate.__dict__
        return current_connection_candidates
    # Case 2.
    # Update current_connection_candidates if the end point distance is below the threshold
    # and one of the following is true:
    elif end_point_distance < start_point_distance and \
        end_point_distance < line_distance_threshold and \
            has_update_on_point_distance(current_connection_candidates['end'], end_point_distance):
        connection_candidate = ConnectionCandidate(
            node=target_line_id,
            type=GraphNodeType.line,
            distance=end_point_distance,
            intersection=False
        )
        current_connection_candidates['end'] = connection_candidate.__dict__
        return current_connection_candidates
    # Case 3.
    # Cases 3 and 4 are for lines intersecting as a T-junction (3-way intersection).
    # Update current_connection_candidates if the start line distance is below the threshold
    # and one of the following is true:
    elif start_line_distance <= end_line_distance and \
        start_line_distance < line_distance_threshold and \
            has_update_on_line_distance(current_connection_candidates['start'], start_line_distance):
        connection_candidate = ConnectionCandidate(
            node=target_line_id,
            type=GraphNodeType.line,
            distance=start_line_distance,
            intersection=True
        )
        current_connection_candidates['start'] = connection_candidate.__dict__
        return current_connection_candidates
    # Case 4
    # Update current_connection_candidates if the end line distance is below the threshold
    # and one of the following is true:
    elif end_line_distance < start_line_distance and \
        end_line_distance < line_distance_threshold and \
            has_update_on_line_distance(current_connection_candidates['end'], end_line_distance):
        connection_candidate = ConnectionCandidate(
            node=target_line_id,
            type=GraphNodeType.line,
            distance=end_line_distance,
            intersection=True
        )
        current_connection_candidates['end'] = connection_candidate.__dict__
        return current_connection_candidates

    # If none of the above conditions are met, return unchanged current_connection_candidates
    # I.e., if there is a 4-way intersection, we are assuming the perpendicular lines are not connected,
    # so we don't want to update the connection candidates.
    return current_connection_candidates


def has_update_on_point_distance(connection: dict, point_distance: float) -> bool:
    '''
    - if the previous candidate was an intersection, then non-intersection connections should be picked or
    - if the start point is closer than the current value in the connection candidates dictionary or
    - if there is no previous value set in the connection candidates dictionary
    '''

    return connection['intersection'] is True or \
        connection['distance'] is None or \
        point_distance < connection['distance']


def has_update_on_line_distance(connection: dict, line_distance: float) -> bool:
    '''
    - if the previous candidate is an intersecting line and the end line distance
     is closer than the current value in the connection candidates dictionary. If the previous
     candidate is a non-intersection line, we don't update the connection candidates because
     we want to prefer non-intersection connections
    - if the previous candidate is a symbol or text node and the end line distance is closer
     than the current value in the connection candidates dictionary
    - if there is no current connection candidate in the dictionary
    '''
    is_intersection = connection['intersection']
    is_symbol_or_text = connection['type'] is GraphNodeType.symbol or connection['type'] is GraphNodeType.text
    previous_distance = connection['distance']

    return (is_intersection and line_distance < previous_distance) or \
           (is_symbol_or_text and line_distance < previous_distance) or \
        previous_distance is None


def batch(iterable, n=1):
    '''
    Generates batches of n elements from iterable
    :param iterable: Iterable
    :param n: Number of elements in each batch
    return: Batched elements index list
    '''
    length = len(iterable)
    for ndx in range(0, length, n):
        yield list(range(ndx, min(ndx + n, length)))
