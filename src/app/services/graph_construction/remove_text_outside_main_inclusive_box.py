from typing import Optional
from app.models.text_detection.text_recognized import TextRecognized
from app.models.bounding_box import BoundingBox
from app.utils.image_utils import is_data_element_within_bounding_box


def remove_text_outside_main_inclusive_box(
        bounding_box_inclusive: Optional[BoundingBox],
        text_list: list[TextRecognized]
        ) -> list[TextRecognized]:
    '''Include items that are within the defined
    bounding box's coordinates (topX, topY, bottomX, and bottomY)
    to avoid noise for graph construction
    bounding_box_inclusive: BoundingBox normalized coordinates to filter the list items
    text_list: list[TextRecognized] - List of items to filter with normalised coordinates
    Returns: list[TextRecognized]
    '''

    filtered_list = []

    for item in text_list:
        if (is_data_element_within_bounding_box(bounding_box_inclusive, item.topX, item.topY, item.bottomX, item.bottomY)):
            filtered_list.append(item)

    return filtered_list
