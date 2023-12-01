# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from fastapi import Response


class ImageResponse(Response):
    def __init__(self, image, filename):
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        super().__init__(content=image, media_type="application/octet-stream", headers=headers)

    def __eq__(self, other):
        return (self.headers) == (other.headers) and (self.body) == (other.body)
