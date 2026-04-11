from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.auth_jwt import create_access_token
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: dict):
    settings = get_settings()
    u, p = body.get("username"), body.get("password")
    if u != settings.demo_username or p != settings.demo_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=u)
    return {"api_version": "v1", "access_token": token, "token_type": "bearer"}
