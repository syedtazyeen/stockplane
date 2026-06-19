import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction
from app.models.product import Product
from app.repositories.base import BaseRepository


class InventoryTransactionRepository(BaseRepository[InventoryTransaction]):
    """Repository for InventoryTransaction."""

    model = InventoryTransaction

    async def list_for_business(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[InventoryTransaction]:
        query = (
            select(InventoryTransaction)
            .join(Inventory, Inventory.id == InventoryTransaction.inventory_id)
            .join(Product, Product.id == Inventory.product_id)
            .where(Product.business_id == business_id)
            .options(
                selectinload(InventoryTransaction.inventory).selectinload(
                    Inventory.product
                ),
                selectinload(InventoryTransaction.created_by),
            )
            .order_by(InventoryTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if product_id is not None:
            query = query.where(Product.id == product_id)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())
