from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserStatus
from app.schemas.business_member import BusinessMemberRead


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    business_name: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    """User data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    status: UserStatus


class TokenPayload(BaseModel):
    """Decoded JWT access token payload."""

    sub: str | None = None


class AuthResponse(BaseModel):
    """Shared response for register and login."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead
    memberships: list[BusinessMemberRead]
