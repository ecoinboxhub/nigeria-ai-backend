from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.auth.schemas import Token, UserCreate, UserLogin, UserResponse
from app.modules.auth.service import authenticate_user, create_tokens, register_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate):
    return register_user(user_in)

@router.post("/login", response_model=Token)
def login(user_login: UserLogin):
    user = authenticate_user(user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    # user['id'] is from Supabase (it could be an int or a uuid string)
    return create_tokens(user_id=str(user["id"]), role=user["role"])
