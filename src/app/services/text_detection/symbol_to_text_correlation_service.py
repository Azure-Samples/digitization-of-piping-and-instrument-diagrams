from app.models.symbol_detection.symbol_detection_inference_response import SymbolDetectionInferenceResponse
from app.models.text_detection.text_recognized import TextRecognized
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.models.symbol_detection.label import Label
from app.utils.regex_utils import does_string_contain_at_least_one_number_and_one_letter
from app.utils.regex_utils import is_symbol_text_invalid
from app.utils.shapely_utils import bounding_box_to_polygon, is_high_overlap
from logger_config import get_logger
import time
from typing import Optional


logger = get_logger(__name__)


def _create_symbol_and_text_associated(
    symbol_label: Label,
    text_associated: Optional[str]
) -> SymbolAndTextAssociated:
    '''Creates a symbol and text associated.

    :param symbol_label: The symbol label.
    :type symbol_label: Label
    :param text_associated: The text associated.
    :type text_associated: Optional[str]
    :return: The symbol and text associated.
    :rtype: SymbolAndTextAssociated'''
    symbol_and_text_associated = SymbolAndTextAssociated(**symbol_label.dict(), text_associated=text_associated)
    # Clearing the score if passed in for cleanness because it is not needed for the response
    symbol_and_text_associated.score = None
    return symbol_and_text_associated


def correlate_symbols_with_text(
    located_text: list[TextRecognized],
    located_symbols: SymbolDetectionInferenceResponse,
    area_threshold: float,
    distance_threshold: float,
    symbols_label_prefixes_with_text_lowered_tuple: tuple[str]
) -> list[SymbolAndTextAssociated]:
    '''Finds the text associated with the symbols.

    :param located_text: The located text.
    :type located_text: list[TextRecognized]
    :param located_symbols: The located symbols.
    :type located_symbols: SymbolDetectionInferenceResponse
    :param area_threshold: The threshold for the area of the text polygon.
    :type area_threshold: float
    :param distance_threshold: The threshold for the distance between the text and symbol polygons.
    :type distance_threshold: float
    :param symbols_label_prefixes_with_text_lowered_tuple: The set of excluded symbols for which we will not associate any text
    :type symbols_label_prefixes_with_text_lowered_tuple: set[str]
    :return: The list of symbols and associated text
    :rtype: list[SymbolAndTextAssociated]'''
    logger.info('Starting to correlate the symbols with detected text')
    tic = time.perf_counter()

    symbol_and_text_associated_list: list[SymbolAndTextAssociated] = []
    for symbol_label in located_symbols.label:
        if not symbol_label.label.lower().startswith(symbols_label_prefixes_with_text_lowered_tuple):
            symbol_and_text_associated = _create_symbol_and_text_associated(symbol_label, None)
            symbol_and_text_associated_list.append(symbol_and_text_associated)
            continue

        seen_text_within_symbol = False
        closest_text_label = None
        closest_text_distance = None

        text_within_list = []
        symbol_polygon = bounding_box_to_polygon(symbol_label)
        for text_label in located_text:
            if is_symbol_text_invalid(text_label.text):
                continue

            text_polygon = bounding_box_to_polygon(text_label)
            if is_high_overlap(text_polygon, symbol_polygon, area_threshold):
                seen_text_within_symbol = True
                text_within_list.append((text_label.text, text_polygon))
                continue

            distance = text_polygon.distance(symbol_polygon)
            if distance > distance_threshold:
                continue

            if closest_text_distance is None or distance < closest_text_distance:
                closest_text_distance = distance
                closest_text_label = text_label.text

        closest_is_alpha_numeric_text = (
            closest_text_label is not None and
            does_string_contain_at_least_one_number_and_one_letter(closest_text_label))
        if seen_text_within_symbol:
            sorted_text_polygons = sorted(text_within_list, key=lambda x: x[1].bounds[1])
            associated_text = [elem[0] for elem in sorted_text_polygons]
            symbol_text = ' '.join(associated_text)
            if does_string_contain_at_least_one_number_and_one_letter(symbol_text) or not closest_is_alpha_numeric_text:
                symbol_and_text_associated = _create_symbol_and_text_associated(symbol_label, symbol_text)
                symbol_and_text_associated_list.append(symbol_and_text_associated)
                continue

        symbol_text = None
        if closest_text_label is not None:
            symbol_text = closest_text_label

        symbol_and_text_associated = _create_symbol_and_text_associated(symbol_label, symbol_text)
        symbol_and_text_associated_list.append(symbol_and_text_associated)

    toc = time.perf_counter()
    logger.info(f'Correlated all symbols and text after {toc - tic:0.4f} seconds')
    return symbol_and_text_associated_list
