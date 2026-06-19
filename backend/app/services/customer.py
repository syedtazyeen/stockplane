import uuid

from fastapi import status

from app.exceptions.base import AppError
from app.models.customer import Customer, CustomerStatus
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    """Customer management workflows."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self.customer_repository = customer_repository

    @property
    def db(self):
        return self.customer_repository.db

    async def _ensure_unique_email(
        self,
        *,
        business_id: uuid.UUID,
        email: str,
        exclude_customer_id: uuid.UUID | None = None,
    ) -> None:
        existing = await self.customer_repository.get_by_email_for_business(
            email=email,
            business_id=business_id,
            exclude_customer_id=exclude_customer_id,
        )
        if existing:
            raise AppError(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    async def _ensure_unique_phone(
        self,
        *,
        business_id: uuid.UUID,
        phone: str,
        exclude_customer_id: uuid.UUID | None = None,
    ) -> None:
        existing = await self.customer_repository.get_by_phone_for_business(
            phone=phone,
            business_id=business_id,
            exclude_customer_id=exclude_customer_id,
        )
        if existing:
            raise AppError(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already in use")

    async def list_customers(
        self,
        *,
        business_id: uuid.UUID,
        status_filter: CustomerStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Customer]:
        return await self.customer_repository.list_for_business(
            business_id=business_id,
            status=status_filter,
            search=search,
            offset=offset,
            limit=limit,
        )

    async def get_customer(
        self, *, business_id: uuid.UUID, customer_id: uuid.UUID
    ) -> Customer:
        customer = await self.customer_repository.get_by_id_for_business(
            customer_id=customer_id,
            business_id=business_id,
        )
        if customer is None:
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    async def create_customer(
        self, *, business_id: uuid.UUID, customer_in: CustomerCreate
    ) -> Customer:
        await self._ensure_unique_email(business_id=business_id, email=customer_in.email)
        await self._ensure_unique_phone(business_id=business_id, phone=customer_in.phone)

        customer = Customer(
            business_id=business_id,
            name=customer_in.name,
            email=customer_in.email,
            phone=customer_in.phone,
            status=customer_in.status,
        )
        await self.customer_repository.create(obj=customer)
        await self.db.commit()
        return await self.get_customer(business_id=business_id, customer_id=customer.id)

    async def update_customer(
        self,
        *,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        customer_in: CustomerUpdate,
    ) -> Customer:
        customer = await self.get_customer(business_id=business_id, customer_id=customer_id)

        update_data = customer_in.model_dump(exclude_unset=True)

        if "email" in update_data:
            await self._ensure_unique_email(
                business_id=business_id,
                email=update_data["email"],
                exclude_customer_id=customer.id,
            )
        if "phone" in update_data:
            await self._ensure_unique_phone(
                business_id=business_id,
                phone=update_data["phone"],
                exclude_customer_id=customer.id,
            )

        for field, value in update_data.items():
            setattr(customer, field, value)

        await self.db.commit()
        return await self.get_customer(business_id=business_id, customer_id=customer.id)

    async def delete_customer(
        self, *, business_id: uuid.UUID, customer_id: uuid.UUID
    ) -> Customer:
        customer = await self.get_customer(business_id=business_id, customer_id=customer_id)
        customer.status = CustomerStatus.INACTIVE
        await self.db.commit()
        return await self.get_customer(business_id=business_id, customer_id=customer.id)
