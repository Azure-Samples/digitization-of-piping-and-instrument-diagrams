from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import start_http_server
import logger_config
import app.utils.override_imwrite
from app.routes.controller import app
from app.queue_consumer import start_consumer_worker

"""
    Creates the app for the docker
"""
logger = logger_config.get_logger(__name__)
Instrumentator().instrument(app).expose(app, endpoint='')

start_http_server(port=7000)

start_consumer_worker()

if __name__ == "__main__":
    import uvicorn
    from app.config import config

    uvicorn.run(app, host="0.0.0.0", port=config.port)
