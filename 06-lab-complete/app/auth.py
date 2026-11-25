"""API key authentication: missing or wrong X-API-Key -> 401."""
import hmac

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str | None = Security(_header)) -> str:
    if not key or not settings.agent_api_key or not hmac.compare_digest(key, settings.agent_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key
