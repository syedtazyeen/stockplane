import uuid

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.exceptions.base import AppError
from app.models.business_member import BusinessMember
from app.models.user import User, UserStatus
from app.repositories.business import BusinessRepository
from app.repositories.business_member import BusinessMemberRepository
from app.repositories.customer import CustomerRepository
from app.idempotency.repository import IdempotencyRecordRepository
from app.idempotency.service import IdempotencyService
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_transaction import InventoryTransactionRepository
from app.repositories.order import OrderLineRepository, OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.business import BusinessService
from app.services.customer import CustomerService
from app.services.inventory import InventoryService
from app.services.order import OrderService
from app.services.product import ProductService

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login"
)


async def get_business_service(
    db: AsyncSession = Depends(get_db),
) -> BusinessService:
    return BusinessService(
        business_repository=BusinessRepository(db),
        business_member_repository=BusinessMemberRepository(db),
    )


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    business_service: BusinessService = Depends(get_business_service),
) -> AuthService:
    return AuthService(
        user_repository=UserRepository(db),
        business_service=business_service,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None or not payload.sub:
        raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc

    user = await UserRepository(db).get_by_id(id=user_id)
    if user is None:
        raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or suspended account")
    return current_user


async def get_business_membership(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BusinessMember:
    membership = await BusinessMemberRepository(db).get_membership(
        user_id=current_user.id,
        business_id=business_id,
    )
    if membership is None:
        raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return membership


async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(
        product_repository=ProductRepository(db),
        inventory_service=InventoryService(
            product_repository=ProductRepository(db),
            inventory_repository=InventoryRepository(db),
            inventory_transaction_repository=InventoryTransactionRepository(db),
        ),
    )


async def get_inventory_service(db: AsyncSession = Depends(get_db)) -> InventoryService:
    product_repository = ProductRepository(db)
    inventory_repository = InventoryRepository(db)
    return InventoryService(
        product_repository=product_repository,
        inventory_repository=inventory_repository,
        inventory_transaction_repository=InventoryTransactionRepository(db),
    )


async def get_idempotency_service(db: AsyncSession = Depends(get_db)) -> IdempotencyService:
    return IdempotencyService(repository=IdempotencyRecordRepository(db))


async def get_customer_service(db: AsyncSession = Depends(get_db)) -> CustomerService:
    return CustomerService(customer_repository=CustomerRepository(db))


async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    product_repository = ProductRepository(db)
    return OrderService(
        order_repository=OrderRepository(db),
        order_line_repository=OrderLineRepository(db),
        customer_repository=CustomerRepository(db),
        product_repository=product_repository,
        inventory_service=InventoryService(
            product_repository=product_repository,
            inventory_repository=InventoryRepository(db),
            inventory_transaction_repository=InventoryTransactionRepository(db),
        ),
    )
