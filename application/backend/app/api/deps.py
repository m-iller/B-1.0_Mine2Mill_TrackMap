from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.auth_jwt import decode_token
from app.config import get_settings

bearer = HTTPBearer(auto_error=False)


async def require_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    settings = get_settings()
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    sub = decode_token(creds.credentials)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return sub


async def optional_api_key(x_api_key: str | None = None) -> bool:
    """Optional service key for internal paths."""
    settings = get_settings()
    if x_api_key and x_api_key == settings.api_secret:
        return True
    return False
