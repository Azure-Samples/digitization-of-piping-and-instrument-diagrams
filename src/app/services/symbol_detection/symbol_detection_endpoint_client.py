from app.config import Config, config
from app.constants.http_methods import HttpMethods
from app.services.request_session_builder import build_request_session
import logger_config
from requests import Session


logger = logger_config.get_logger(__name__)


class SymbolDetectionEndpointClient(object):
    def __init__(self, config: Config, session: Session):
        '''Initializes a new instance of the SymbolDetectionEndpointClient class.

        :param config: The configuration to use
        :type config: Config
        :param session: The session to use
        :type session: Session'''
        self._object_detection_inference_api = config.symbol_detection_api
        self._bearer_token = config.symbol_detection_api_bearer_token
        self._session = session

    def send_request(
        self,
        image_bytes: bytes
    ):
        '''Sends a request to the object detection inference endpoint.

        :param image_bytes: The bytes of the image to send
        :type image_bytes: bytes
        :return: The response from the object detection inference endpoint
        :rtype: dict'''
        logger.info(f'Sending request to {self._object_detection_inference_api}/score')

        response = self._session.post(
            f'{self._object_detection_inference_api}/score',
            files={'image': image_bytes},
            headers={'Authorization': f'Bearer {self._bearer_token}'})

        response.raise_for_status()
        return response.json()

    def check_health(self):
        '''Checks the health of the object detection inference endpoint.

        :return: True if the object detection inference endpoint is healthy; otherwise, False
        :rtype: bool'''
        logger.info(f'Checking health of {self._object_detection_inference_api}')

        try:
            response = self._session.get(
                self._object_detection_inference_api,
                headers={'Authorization': f'Bearer {self._bearer_token}'})
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f'Health check failed with error: {e}')
            return False


RETRY_STATUS_FORCELIST = [503, 504]
RETRY_MOUNT_PREFIXES = ['https://', 'http://']

session = build_request_session(
    config.inference_service_retry_count,
    config.inference_service_retry_backoff_factor,
    RETRY_STATUS_FORCELIST,
    [HttpMethods.POST],
    RETRY_MOUNT_PREFIXES)


symbol_detection_endpoint_client = SymbolDetectionEndpointClient(config, session)
