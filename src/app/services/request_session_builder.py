from requests import Session
from requests.adapters import HTTPAdapter, Retry
from typing import List


def build_request_session(
    retry_count: int,
    retry_backoff_factor: float,
    status_forcelist: List[int],
    allowed_methods: List[str],
    mount_prefixes: List[str]
) -> Session:
    '''Builds a request session with retry logic.

    :param retry_count: The number of times to retry
    :type retry_count: int
    :param retry_backoff_factor: The backoff factor to use
    :type retry_backoff_factor: float
    :param status_forcelist: The list of status codes to retry on
    :type status_forcelist: List[int]
    :param allowed_methods: The list of methods to retry on
    :type allowed_methods: List[str]
    :param mount_prefixes: The list of prefixes to mount the retry logic to
    :type mount_prefixes: List[str]
    :return: The request session with retry logic
    :rtype: Session'''

    session = Session()
    retries = Retry(
        total=retry_count,
        backoff_factor=retry_backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods)

    for mount_prefix in mount_prefixes:
        session.mount(mount_prefix, HTTPAdapter(max_retries=retries))
    return session
