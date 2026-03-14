from typing import Annotated

from fastapi import Depends, HTTPException

from app.core.security import decode_token


class Role:
    ADMIN = "admin"
    PM = "project_manager"
    PROCUREMENT = "procurement"
    SAFETY = "safety"
    LEGAL = "legal"
    ANALYST = "analyst"


def require_role(allowed_roles: list[str]):
    def _checker(payload: Annotated[dict, Depends(decode_token)]) -> dict:
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return payload

    return _checker
