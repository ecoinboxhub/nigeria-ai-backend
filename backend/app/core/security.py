from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer = HTTPBearer(auto_error=False)


def verify_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": subject, "role": role, "type": "access", "exp": expires}
    return _encode(payload)


def create_refresh_token(subject: str, role: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_refresh_expires_minutes)
    payload = {"sub": subject, "role": role, "type": "refresh", "exp": expires}
    return _encode(payload)


def decode_raw_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def decode_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Missing token. Get an access token from POST /api/v1/integration/token "
                "with X-API-Key, then send Authorization: Bearer <access_token>."
            ),
        )
    try:
        payload = decode_raw_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_raw_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        sub = payload.get("sub", "")
        role = payload.get("role", "analyst")
        return create_access_token(sub, role), create_refresh_token(sub, role)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
