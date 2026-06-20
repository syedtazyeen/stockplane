import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderLine, OrderStatus
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order."""

    model = Order

    async def list_for_business(
        self,
        *,
        business_id: uuid.UUID,
        status: OrderStatus | None = None,
        customer_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        query = (
            select(Order)
            .where(Order.business_id == business_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.lines),
            )
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status is not None:
            query = query.where(Order.status == status)
        else:
            query = query.where(Order.status != OrderStatus.DRAFT)
        if customer_id is not None:
            query = query.where(Order.customer_id == customer_id)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_id_for_business(
        self, *, order_id: uuid.UUID, business_id: uuid.UUID
    ) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id, Order.business_id == business_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.lines),
            )
        )
        return result.scalar_one_or_none()


class OrderLineRepository(BaseRepository[OrderLine]):
    """Repository for OrderLine."""

    model = OrderLine
