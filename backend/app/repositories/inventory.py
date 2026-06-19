import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.inventory import Inventory
from app.models.product import Product
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    """Repository for Inventory."""

    model = Inventory

    async def get_by_product_id(self, *, product_id: uuid.UUID) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory).where(Inventory.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_product_id_for_update(
        self, *, product_id: uuid.UUID, business_id: uuid.UUID
    ) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Inventory.product_id == product_id, Product.business_id == business_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_many_by_product_ids_for_update(
        self, *, product_ids: list[uuid.UUID], business_id: uuid.UUID
    ) -> dict[uuid.UUID, Inventory]:
        if not product_ids:
            return {}

        sorted_ids = sorted(product_ids)
        result = await self.db.execute(
            select(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Inventory.product_id.in_(sorted_ids), Product.business_id == business_id)
            .order_by(Inventory.product_id)
            .with_for_update()
        )
        inventories = result.scalars().all()
        return {inventory.product_id: inventory for inventory in inventories}

    async def get_by_id_for_business(
        self, *, inventory_id: uuid.UUID, business_id: uuid.UUID
    ) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Inventory.id == inventory_id, Product.business_id == business_id)
            .options(selectinload(Inventory.product))
        )
        return result.scalar_one_or_none()

    async def list_for_business(
        self,
        *,
        business_id: uuid.UUID,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Inventory]:
        query = (
            select(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Product.business_id == business_id)
            .options(selectinload(Inventory.product))
            .order_by(Product.name)
            .offset(offset)
            .limit(limit)
        )
        if low_stock_only:
            query = query.where(
                Inventory.reorder_point.is_not(None),
                (Inventory.quantity_on_hand - Inventory.reserved_quantity)
                <= Inventory.reorder_point,
            )

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def adjust_quantity_atomically(
        self, *, inventory_id: uuid.UUID, quantity_delta: int
    ) -> int | None:
        """Apply a delta in one statement; return new quantity or None if insufficient."""
        stmt = (
            update(Inventory)
            .where(Inventory.id == inventory_id)
            .values(quantity_on_hand=Inventory.quantity_on_hand + quantity_delta)
        )
        if quantity_delta < 0:
            stmt = stmt.where(Inventory.quantity_on_hand >= abs(quantity_delta))

        result = await self.db.execute(stmt.returning(Inventory.quantity_on_hand))
        return result.scalar_one_or_none()
