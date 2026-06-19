from fastapi import status
from app.exceptions.base import AppError
from app.models.business_member import BusinessMember
from app.models.user import User, UserStatus
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.core.security import create_access_token, get_password_hash, verify_password
from app.services.business import BusinessService


class AuthService:
    """Authentication and registration workflows."""

    def __init__(
        self,
        user_repository: UserRepository,
        business_service: BusinessService,
    ) -> None:
        self.user_repository = user_repository
        self.business_service = business_service

    @property
    def db(self):
        return self.user_repository.db

    async def register_new_user(
        self, user_in: UserCreate
    ) -> tuple[User, list[BusinessMember], str]:
        existing = await self.user_repository.get_by_email(user_in.email)
        if existing:
            raise AppError(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            status=UserStatus.ACTIVE,
        )
        await self.user_repository.create(obj=user)

        membership = await self.business_service.create_business_for_owner(
            user_id=user.id,
            name=user_in.business_name,
        )

        await self.db.commit()
        await self.db.refresh(user)

        token = create_access_token(str(user.id))
        return user, [membership], token

    async def authenticate_user(
        self, email: str, password: str
    ) -> tuple[User, list[BusinessMember], str]:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or suspended account")

        memberships = await self.business_service.get_memberships_for_user(user.id)
        token = create_access_token(str(user.id))
        return user, memberships, token
