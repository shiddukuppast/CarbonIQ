from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_current_user, get_db_dep
from app.schemas.auth import TokenResponse, UserLoginRequest, UserProfileResponse, UserRegisterRequest
from app.services.auth_service import get_user_profile, login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: UserRegisterRequest,
    db: Any = Depends(get_db_dep),
) -> TokenResponse:
    """
    Registers a new user, provisions a private workspace, and returns a signed JWT.
    Enforces email validation and normalized uniqueness.
    """
    return await register_user(req, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: UserLoginRequest,
    db: Any = Depends(get_db_dep),
) -> TokenResponse:
    """
    Authenticates email and password, returning a signed JWT access token.
    """
    return await login_user(req, db)


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db_dep),
) -> UserProfileResponse:
    """
    Returns the profile and authorized workspace details of the currently authenticated user.
    """
    return await get_user_profile(current_user, db)
