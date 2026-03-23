from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_TOKEN_HEADER = APIKeyHeader(name="X-UADIB-Token", auto_error=False)


def validate_api_token(token: str | None = Security(API_TOKEN_HEADER)) -> str:
    expected = os.getenv("UADIB_AUTH_TOKEN", "changeme")
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token
