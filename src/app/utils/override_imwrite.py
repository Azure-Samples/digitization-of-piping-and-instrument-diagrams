# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import cv2
from app.services import blob_storage_client

original_imwrite = cv2.imwrite


def blob_imwrite(file_path: str, img: cv2.Mat) -> bool:
    ret, buffer = cv2.imencode('.png', img)

    tobytes = buffer.tobytes()

    if not ret:
        return False

    blob_storage_client.blob_storage_client.upload_bytes(file_path, tobytes)

    return True


cv2.imwrite = blob_imwrite
