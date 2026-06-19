from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_auth_service, get_current_active_user
from app.models.user import User
from app.schemas.user import AuthResponse, UserCreate, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and business",
)
async def register(
    user_in: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    user, memberships, token = await auth_service.register_new_user(user_in)
    return AuthResponse(user=user, memberships=memberships, access_token=token)


@router.post("/login", response_model=AuthResponse, summary="Log in and receive an access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    user, memberships, token = await auth_service.authenticate_user(
        form_data.username, form_data.password
    )
    return AuthResponse(user=user, memberships=memberships, access_token=token)


@router.get("/me", response_model=UserRead, summary="Get the currently authenticated user")
async def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user
