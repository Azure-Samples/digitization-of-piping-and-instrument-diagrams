from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi_health import health
from app.routes.controllers.pid_digitization_controller import router as pid_digitalization_router
from app.services.symbol_detection.symbol_detection_endpoint_client import symbol_detection_endpoint_client
from app.services.blob_storage_client import blob_storage_client
import logger_config
from app.routes.tracing_middleware import TracingMiddleware


logger = logger_config.get_logger(__name__)
logger.info('Starting python PID Digitization application')


def applicationLivenessCheck():
    logger.info("Checking liveness of the application")
    return True


def applicationReadinessCheck():
    logger.info("Checking readiness of the application")
    return True


def is_application_live(liveness_check: bool = Depends(applicationLivenessCheck)):
    return liveness_check


def is_application_ready(readiness_check: bool = Depends(applicationReadinessCheck)):
    return readiness_check


def is_dependency_online(startup_status: bool = Depends(symbol_detection_endpoint_client.check_health)):
    logger.info("Checking if the dependent service is online: " + str(startup_status))
    return startup_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    blob_storage_client.init()
    yield
    return


app = FastAPI(lifespan=lifespan)
app.add_middleware(TracingMiddleware, blob_storage_client=blob_storage_client)
app.add_api_route("/health/liveness", health([is_application_live]), include_in_schema=False)
app.add_api_route("/health/readiness", health([is_application_ready]), include_in_schema=False)
app.add_api_route("/health/startup", health([is_dependency_online]), include_in_schema=False)
app.include_router(pid_digitalization_router)
