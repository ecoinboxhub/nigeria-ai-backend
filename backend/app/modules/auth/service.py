import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.supabase import supabase
from app.modules.auth.schemas import Token, UserCreate

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def register_user(user_in: UserCreate) -> Dict[str, Any]:
    # 1. Check if user already exists in Supabase 'users' table
    existing_user = supabase.table("users").select("*").eq("email", user_in.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # 2. Hash password and insert
    user_data = {
        "email": user_in.email,
        "username": user_in.username,
        "hashed_password": hash_password(user_in.password),
        "role": user_in.role,
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat()
    }
    
    try:
        result = supabase.table("users").insert(user_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create user record.")
        return result.data[0]
    except Exception as e:
        logger.error(f"Supabase registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration.")

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        result = supabase.table("users").select("*").eq("email", email).execute()
        if not result.data:
            return None
        
        user = result.data[0]
        if verify_password(password, user["hashed_password"]):
            return user
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

def create_tokens(user_id: str, role: str) -> Token:
    from app.core.security import create_access_token, create_refresh_token
    access = create_access_token(subject=user_id, role=role)
    refresh = create_refresh_token(subject=user_id, role=role)
    return Token(access_token=access, refresh_token=refresh)
