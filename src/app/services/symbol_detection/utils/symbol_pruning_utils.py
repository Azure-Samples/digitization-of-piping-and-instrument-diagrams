from app.models.symbol_detection.label import Label
from app.utils.shapely_utils import bounding_box_to_polygon, is_high_overlap
from logger_config import get_logger
import time


logger = get_logger(__name__)


def prune_overlapping_symbols(
    symbols: list[Label],
    area_threshold: float,
):
    '''Prunes the overlapping symbols.

    :param symbols: The list of symbols.
    :type symbols: list[Label]
    :param area_threshold: The threshold for the area of the text polygon.
    :type area_threshold: float
    :return: The list of symbols after pruning.
    :rtype: list[Label]'''
    logger.info('Starting to prune overlapping symbols')
    tic = time.perf_counter()

    # We sort the symbols by area so that we can prune the larger symbols first
    # We do this as a larger box can be over multiple smaller boxes and we want to keep the smaller boxes
    symbols_with_polygons = [(symbol, bounding_box_to_polygon(symbol)) for symbol in symbols]
    symbols_with_polygons = sorted(symbols_with_polygons, key=lambda x: x[1].area, reverse=True)
    symbols_pruned_ids = set()
    for i, symbol_tuple in enumerate(symbols_with_polygons):
        iteration_prune_ids = set()
        exited_early = False

        symbol, symbol_polygon = symbol_tuple
        starting_index = i + 1
        if starting_index >= len(symbols):
            break
        for compare_symbol_tuple in symbols_with_polygons[starting_index:]:
            compare_symbol, compare_symbol_polygon = compare_symbol_tuple
            if is_high_overlap(symbol_polygon, compare_symbol_polygon, area_threshold) or \
                    is_high_overlap(compare_symbol_polygon, symbol_polygon, area_threshold):
                if symbol.score >= compare_symbol.score:
                    iteration_prune_ids.add(compare_symbol.id)
                else:
                    symbols_pruned_ids.add(symbol.id)
                    exited_early = True
                    break

        if not exited_early:
            symbols_pruned_ids.update(iteration_prune_ids)

    toc = time.perf_counter()
    logger.info(f'Finished pruning overlapping symbols in {toc - tic:0.4f} seconds')

    symbols_filtered = [symbol for symbol in symbols if symbol.id not in symbols_pruned_ids]
    return symbols_filtered
