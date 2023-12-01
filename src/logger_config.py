# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import logging
import ecs_logging
import sys

from app.config import config


def get_logger(logger_name) -> logging.Logger:
    logger = logging.getLogger(logger_name)

    if config.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not sys.gettrace():
        # Add an ECS formatter to the Handler
        handler = logging.StreamHandler()
        handler.setFormatter(ecs_logging.StdlibFormatter())
        logger.addHandler(handler)
    else:
        logging.basicConfig(format='[ %(asctime)s loglevel=%(levelname)-6s] %(message)s')
    return logger
