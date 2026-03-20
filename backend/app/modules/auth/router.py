from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.auth.schemas import Token, UserCreate, UserLogin, UserResponse, SocialSyncCreate
from app.modules.auth.service import authenticate_user, create_tokens, register_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate):
    return register_user(user_in, provider="email")

@router.post("/social-sync", response_model=Token)
def social_sync(user_in: SocialSyncCreate):
    """
    Syncs a social login user with the app_verified_users table and returns tokens.
    """
    user = register_user(user_in, provider=user_in.provider)
    return create_tokens(user_id=str(user["id"]), role=user["role"])

@router.post("/login", response_model=Token)
def login(user_login: UserLogin):
    user = authenticate_user(user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return create_tokens(user_id=str(user["id"]), role=user["role"])
