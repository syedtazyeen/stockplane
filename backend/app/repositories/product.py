import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductStatus
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product."""

    model = Product

    async def list_for_business(
        self,
        *,
        business_id: uuid.UUID,
        status: ProductStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        query = (
            select(Product)
            .where(Product.business_id == business_id)
            .options(selectinload(Product.inventory))
            .order_by(Product.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status is not None:
            query = query.where(Product.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                Product.name.ilike(pattern) | Product.sku.ilike(pattern)
            )

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_id_for_business(
        self, *, product_id: uuid.UUID, business_id: uuid.UUID
    ) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id, Product.business_id == business_id)
            .options(selectinload(Product.inventory))
        )
        return result.scalar_one_or_none()

    async def get_by_sku_for_business(
        self,
        *,
        sku: str,
        business_id: uuid.UUID,
        exclude_product_id: uuid.UUID | None = None,
    ) -> Product | None:
        query = select(Product).where(
            Product.business_id == business_id,
            Product.sku == sku,
        )
        if exclude_product_id is not None:
            query = query.where(Product.id != exclude_product_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
