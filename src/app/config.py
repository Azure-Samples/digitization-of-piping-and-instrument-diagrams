from pydantic import BaseSettings, root_validator, validator

from typing import Union, Optional


class Config(BaseSettings):
    arrow_symbol_label: str = 'Piping/Fittings/Mid arrow flow direction'
    blob_storage_account_url: str = str()
    blob_storage_container_name: str = str()
    centroid_distance_threshold: float = 0.5
    debug: bool = False
    detect_dotted_lines: bool = False
    enable_preprocessing_text_detection: bool = True
    enable_thinning_preprocessing_line_detection: bool = True
    flow_direction_asset_prefixes: Union[str, set[str]] = \
        {'Equipment/', 'Piping/Endpoint/Pagination'}
    form_recognizer_endpoint: str = str()
    graph_db_authenticate_with_azure_ad: bool = False
    graph_db_connection_string: str = str()
    graph_distance_threshold_for_lines_pixels: int = 50
    graph_distance_threshold_for_symbols_pixels: int = 5
    graph_distance_threshold_for_text_pixels: int = 5
    graph_line_buffer_pixels: int = 5
    graph_symbol_to_symbol_distance_threshold_pixels: int = 10
    graph_symbol_to_symbol_overlap_region_threshold: float = 0.7
    inference_score_threshold: float = 0.5
    inference_service_retry_count: int = 3
    inference_service_retry_backoff_factor: float = 0.3
    line_detection_hough_max_line_gap: Optional[int] = None  # Note conditional validation below based on detect_dotted_lines
    line_detection_hough_min_line_length: Optional[int] = 10  # Note conditional validation below based on detect_dotted_lines
    # line_detection_hough_max_line_gap value helps with returning the smaller dashed line segments
    # into single solid line segments wherever the dashed line segments are detected by Hough.
    # The default value will not work for all the images.
    # This is something that is good to start with but has to be adjusted based on the images dashed lines
    # in the graph construction post api request
    line_detection_hough_rho: float = 0.1
    line_detection_hough_theta: int = 1080
    line_detection_hough_threshold: int = 5
    line_detection_job_timeout_seconds: int = 300
    line_segment_padding_default: float = 0.2

    port: int = 8000
    symbol_detection_api: str = str()
    symbol_detection_api_bearer_token: str = str()
    symbol_label_prefixes_to_connect_if_close: Union[str, set[str]] = \
        {'Equipment', 'Instrument/Valve/', 'Piping/Fittings/Mid arrow flow direction', 'Piping/Fittings/Flanged connection'}
    symbol_label_prefixes_to_include_in_graph_image_output: Union[str, set[str]] = \
        {'Equipment/', 'Instrument/Valve/', 'Piping/Endpoint/Pagination'}
    symbol_label_prefixes_with_text: Union[str, set[str]] = \
        {'Equipment/', 'Instrument/', 'Piping/Endpoint/Pagination'}
    symbol_overlap_threshold: float = 0.6
    text_detection_area_intersection_ratio_threshold: float = 0.8
    text_detection_distance_threshold: float = 0.01
    symbol_label_for_connectors: Union[str, set[str]] = \
        {'Piping/Endpoint/Pagination'}
    valve_symbol_prefix: str = 'Instrument/Valve/'
    workers_count_for_data_batch: int = 3

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    @validator(
        "blob_storage_account_url",
        "blob_storage_container_name",
        "form_recognizer_endpoint",
        "symbol_detection_api",
        "symbol_detection_api_bearer_token",
        "graph_db_connection_string",
        allow_reuse=True)
    def validate_string(cls, v):
        if v is None or len(v) == 0:
            raise ValueError("Value must be a non-empty string")
        return v

    @validator(
            "flow_direction_asset_prefixes",
            "symbol_label_prefixes_with_text",
            "symbol_label_prefixes_to_include_in_graph_image_output",
            "symbol_label_prefixes_to_connect_if_close",
            pre=True,
            allow_reuse=True)
    def validate_and_transform_comma_separated_list(cls, val):
        if isinstance(val, str):
            val_arr = val.split(',')
            val_arr = [x.strip() for x in val_arr]
            return set(val_arr)
        return val

    @root_validator(allow_reuse=True)
    def update_config_based_on_dotted_lines_detection(cls, values):
        if values.get('detect_dotted_lines') is True:
            values['line_detection_hough_min_line_length'] = None

            if values['line_detection_hough_max_line_gap'] is None:
                values['line_detection_hough_max_line_gap'] = 10
        elif values.get('detect_dotted_lines') is False:
            if values['line_detection_hough_min_line_length'] is None or \
                    values['line_detection_hough_min_line_length'] < 10:
                values['line_detection_hough_min_line_length'] = 10

            values['line_detection_hough_max_line_gap'] = None

        return values


config = Config()
