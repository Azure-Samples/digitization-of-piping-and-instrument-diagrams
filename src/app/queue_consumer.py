# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from queue import Queue
import threading
import logger_config
import signal

logger = logger_config.get_logger(__name__)

_queue = Queue(20)
_kill_now = False


def exit_gracefully(signum, frame):
    global _kill_now
    logger.info("Received signal to exit queue consumer thread")
    _kill_now = True


signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)


def submit_job(func, args):
    """
    This function submits a job to the queue
    """
    _queue.put((func, args))


def consumer_worker():
    """
    This is the worker thread function to process the job submitted to the queue
    """
    while (not _kill_now):
        logger.info("Waiting for queue")
        (func, args) = _queue.get()
        logger.info(f"Got a job from queue: {func.__name__}: {args}")
        try:
            func(*args)
            logger.info(f"Finished job from queue: {func.__name__}: {args}")
        except Exception as e:
            logger.error(f"Error processing job from queue: {func.__name__}: {args}: {e}")


consumer_thread = threading.Thread(target=consumer_worker)


def start_consumer_worker():
    """
    This function starts the worker thread
    """
    if consumer_thread.is_alive() is False:
        consumer_thread.start()
        logger.info("Started queue consumer thread")
    else:
        logger.info("Queue consumer thread is already running")
