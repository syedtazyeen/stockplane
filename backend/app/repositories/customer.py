import uuid

from sqlalchemy import select

from app.models.customer import Customer, CustomerStatus
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer."""

    model = Customer

    async def list_for_business(
        self,
        *,
        business_id: uuid.UUID,
        status: CustomerStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Customer]:
        query = (
            select(Customer)
            .where(Customer.business_id == business_id)
            .order_by(Customer.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status is not None:
            query = query.where(Customer.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                Customer.name.ilike(pattern)
                | Customer.email.ilike(pattern)
                | Customer.phone.ilike(pattern)
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id_for_business(
        self, *, customer_id: uuid.UUID, business_id: uuid.UUID
    ) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.business_id == business_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_for_business(
        self,
        *,
        email: str,
        business_id: uuid.UUID,
        exclude_customer_id: uuid.UUID | None = None,
    ) -> Customer | None:
        query = select(Customer).where(
            Customer.business_id == business_id,
            Customer.email == email,
        )
        if exclude_customer_id is not None:
            query = query.where(Customer.id != exclude_customer_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone_for_business(
        self,
        *,
        phone: str,
        business_id: uuid.UUID,
        exclude_customer_id: uuid.UUID | None = None,
    ) -> Customer | None:
        query = select(Customer).where(
            Customer.business_id == business_id,
            Customer.phone == phone,
        )
        if exclude_customer_id is not None:
            query = query.where(Customer.id != exclude_customer_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
