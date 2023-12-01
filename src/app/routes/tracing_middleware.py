# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from starlette.types import Message
from starlette.middleware.base import BaseHTTPMiddleware
import logger_config
from app.services.blob_storage_client import BlobStorageClient
from app.models.enums.inference_result import InferenceResult
from app.services import storage_path_template_builder

logger = logger_config.get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    '''
    This class is used to log the requests and responses of the API.
    '''
    def __init__(self, app: FastAPI, blob_storage_client: BlobStorageClient):
        super().__init__(app)
        self.enable_storing_data = True
        self.blob_storage_client = blob_storage_client

    async def set_body(self, request: Request, body: bytes):
        async def receive() -> Message:
            return {"type": "http.request", "body": body}
        request._receive = receive

    async def get_form(self, request: Request) -> bytes:
        body = await request.body()
        form = await request.form()
        await self.set_body(request, body)
        return form

    def validate_file_to_upload(self, file_name: str) -> bool:
        file_name = file_name.lower()
        if not (file_name.endswith(".jpg") or file_name.endswith(".jpeg") or file_name.endswith(".png")):
            raise HTTPException(status_code=400, detail="Bad Request")

    async def validate_body_to_upload(self, id: str, request: Request) -> bool:
        body = await request.json()

        if 'image_url' in body:
            image_url = body.get('image_url').rsplit('.', 1)[0]

            if not id == image_url:
                raise HTTPException(status_code=400, detail="Bad Request. The id in the url and the image_url in the body are not the same")

    async def dispatch(self, request: Request, call_next):
        try:
            is_log_needed = request.url.path.startswith("/api")

            # log the content of the form data
            if is_log_needed and request.method == "POST":
                logger.info(f"Logging request for {request.url.path}")

                await self.set_body(request, await request.body())
                form_data = await self.get_form(request)

                qualifiers = request.url.path.split("/")
                method_name = qualifiers[qualifiers.index("api") + 2]
                id = qualifiers[qualifiers.index("api") + 3]

                # Validate the method name
                inference_method = InferenceResult(method_name)

                # checking the existance of the file in the form data
                if 'file' in form_data:
                    file = UploadFile(form_data['file'])

                    # only will upload jpg/png files
                    self.validate_file_to_upload(file.file.filename)

                    blob_name = storage_path_template_builder.build_image_path(id, inference_method)
                    file_content = await file.file.read()

                    self.blob_storage_client.upload_bytes(blob_name, file_content)

                    logger.info(f"Uploaded file to: {blob_name}")

                if request.headers['Content-Type'] == 'application/json':
                    await self.validate_body_to_upload(id, request)

                    # upload the body of the request as a json file
                    file_content = await request.body()
                    blob_name = storage_path_template_builder.build_inference_request_path(id, inference_method)
                    self.blob_storage_client.upload_bytes(blob_name, file_content)
                    logger.info(f"Uploaded file to: {blob_name}")

            response = await call_next(request)

            if is_log_needed:
                logger.info(f"Logging response for {request.url.path}")

                # log the body of the response
                if request.method == "POST" and response.status_code == 200:
                    response_body = b""
                    async for chunk in response.body_iterator:
                        response_body += chunk
                    blob_name = storage_path_template_builder.build_inference_response_path(id, inference_method)
                    self.blob_storage_client.upload_bytes(blob_name, response_body.decode())
                    logger.info(f"Uploaded file to: {blob_name}")

                    return Response(content=response_body, status_code=response.status_code,
                                    headers=dict(response.headers), media_type=response.media_type)

            return response
        except HTTPException as ex:
            return Response(content=str(ex.detail), status_code=ex.status_code)
        except Exception as ex:
            logger.error(f"An error has occurred: {ex}")
            return Response(content="An error has occurred", status_code=500)
