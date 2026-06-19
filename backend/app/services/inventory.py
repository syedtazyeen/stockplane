import uuid
from typing import Protocol

from fastapi import status
from sqlalchemy.exc import IntegrityError

from app.exceptions.base import AppError
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.models.product import Product
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_transaction import InventoryTransactionRepository
from app.repositories.product import ProductRepository
from app.schemas.product import InventoryAdjust, InventorySet


class OrderLineLike(Protocol):
    product_id: uuid.UUID
    quantity: int


class InventoryService:
    """Inventory and stock movement workflows."""

    def __init__(
        self,
        product_repository: ProductRepository,
        inventory_repository: InventoryRepository,
        inventory_transaction_repository: InventoryTransactionRepository,
    ) -> None:
        self.product_repository = product_repository
        self.inventory_repository = inventory_repository
        self.inventory_transaction_repository = inventory_transaction_repository

    @property
    def db(self):
        return self.inventory_repository.db

    async def _get_inventory_for_update(
        self, *, business_id: uuid.UUID, product_id: uuid.UUID
    ) -> Inventory:
        inventory = await self.inventory_repository.get_by_product_id_for_update(
            product_id=product_id,
            business_id=business_id,
        )
        if inventory is not None:
            return inventory

        product = await self.product_repository.get_by_id_for_business(
            product_id=product_id,
            business_id=business_id,
        )
        if product is None:
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        inventory = Inventory(product_id=product.id, quantity_on_hand=0)
        try:
            async with self.db.begin_nested():
                await self.inventory_repository.create(obj=inventory)
        except IntegrityError:
            inventory = await self.inventory_repository.get_by_product_id_for_update(
                product_id=product_id,
                business_id=business_id,
            )
            if inventory is None:
                raise AppError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not load inventory for product",
                )

        return inventory

    async def ensure_for_product(self, product: Product) -> Inventory:
        inventory = product.inventory
        if inventory is None:
            inventory = Inventory(product_id=product.id, quantity_on_hand=0)
            await self.inventory_repository.create(obj=inventory)
            product.inventory = inventory
        return inventory

    async def get_many_for_update(
        self, *, product_ids: list[uuid.UUID], business_id: uuid.UUID
    ) -> dict[uuid.UUID, Inventory]:
        locked = await self.inventory_repository.get_many_by_product_ids_for_update(
            product_ids=product_ids,
            business_id=business_id,
        )

        missing_ids = sorted(set(product_ids) - set(locked.keys()))
        for product_id in missing_ids:
            inventory = await self._get_inventory_for_update(
                business_id=business_id,
                product_id=product_id,
            )
            locked[product_id] = inventory

        return locked

    async def get_or_create_for_update(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        inventory_by_product: dict[uuid.UUID, Inventory],
    ) -> Inventory:
        inventory = inventory_by_product.get(product_id)
        if inventory is not None:
            return inventory

        inventory = await self._get_inventory_for_update(
            business_id=business_id,
            product_id=product_id,
        )
        inventory_by_product[product_id] = inventory
        return inventory

    async def create_initial_for_product(
        self,
        *,
        product: Product,
        quantity: int,
        reorder_point: int | None,
        user_id: uuid.UUID,
    ) -> Inventory:
        inventory = Inventory(
            product_id=product.id,
            quantity_on_hand=quantity,
            reorder_point=reorder_point,
        )
        await self.inventory_repository.create(obj=inventory)
        product.inventory = inventory

        if quantity > 0:
            transaction = InventoryTransaction(
                inventory_id=inventory.id,
                quantity_delta=quantity,
                quantity_after=quantity,
                transaction_type=InventoryTransactionType.RESTOCK,
                notes="Initial stock on product creation",
                created_by_id=user_id,
            )
            await self.inventory_transaction_repository.create(obj=transaction)

        return inventory

    async def set_quantity_on_product(
        self,
        *,
        business_id: uuid.UUID,
        product: Product,
        quantity: int,
        user_id: uuid.UUID | None = None,
        notes: str = "Stock updated via product API",
    ) -> None:
        inventory = await self._get_inventory_for_update(
            business_id=business_id,
            product_id=product.id,
        )

        previous_quantity = inventory.quantity_on_hand
        if previous_quantity == quantity:
            return

        inventory.quantity_on_hand = quantity
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            quantity_delta=quantity - previous_quantity,
            quantity_after=quantity,
            transaction_type=InventoryTransactionType.CORRECTION,
            notes=notes,
            created_by_id=user_id,
        )
        await self.inventory_transaction_repository.create(obj=transaction)

    async def set_reorder_point(
        self,
        *,
        business_id: uuid.UUID,
        product: Product,
        reorder_point: int | None,
    ) -> None:
        inventory = await self._get_inventory_for_update(
            business_id=business_id,
            product_id=product.id,
        )
        inventory.reorder_point = reorder_point

    async def deduct_for_order(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: int,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        inventory_by_product: dict[uuid.UUID, Inventory],
        notes: str,
    ) -> None:
        inventory = await self.get_or_create_for_update(
            business_id=business_id,
            product_id=product_id,
            inventory_by_product=inventory_by_product,
        )

        new_quantity = await self.inventory_repository.adjust_quantity_atomically(
            inventory_id=inventory.id,
            quantity_delta=-quantity,
        )
        if new_quantity is None:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available stock",
            )

        inventory.quantity_on_hand = new_quantity
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            quantity_delta=-quantity,
            quantity_after=inventory.quantity_on_hand,
            transaction_type=InventoryTransactionType.SALE,
            notes=notes,
            reference=str(order_id),
            created_by_id=user_id,
        )
        await self.inventory_transaction_repository.create(obj=transaction)

    async def restore_order_lines(
        self,
        *,
        lines: list[OrderLineLike],
        order_id: uuid.UUID,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        restored_notes: str,
    ) -> None:
        product_ids = [line.product_id for line in lines]
        inventory_by_product = await self.get_many_for_update(
            product_ids=product_ids,
            business_id=business_id,
        )

        for line in lines:
            inventory = inventory_by_product.get(line.product_id)
            if inventory is None:
                continue

            quantity = line.quantity
            inventory.quantity_on_hand += quantity
            transaction = InventoryTransaction(
                inventory_id=inventory.id,
                quantity_delta=quantity,
                quantity_after=inventory.quantity_on_hand,
                transaction_type=InventoryTransactionType.ORDER_CANCELLATION,
                notes=restored_notes.format(quantity=quantity),
                reference=str(order_id),
                created_by_id=user_id,
            )
            await self.inventory_transaction_repository.create(obj=transaction)

    async def list_inventory(
        self,
        *,
        business_id: uuid.UUID,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Inventory]:
        return await self.inventory_repository.list_for_business(
            business_id=business_id,
            low_stock_only=low_stock_only,
            offset=offset,
            limit=limit,
        )

    async def adjust_inventory(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        adjustment: InventoryAdjust,
        user_id: uuid.UUID,
    ) -> Inventory:
        inventory = await self._get_inventory_for_update(
            business_id=business_id,
            product_id=product_id,
        )

        new_quantity = await self.inventory_repository.adjust_quantity_atomically(
            inventory_id=inventory.id,
            quantity_delta=adjustment.quantity_delta,
        )
        if new_quantity is None:
            detail = (
                "Insufficient available stock for this adjustment"
                if adjustment.quantity_delta < 0
                else "Insufficient stock for this adjustment"
            )
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )

        inventory.quantity_on_hand = new_quantity

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            quantity_delta=adjustment.quantity_delta,
            quantity_after=new_quantity,
            transaction_type=adjustment.transaction_type,
            notes=adjustment.notes,
            reference=adjustment.reference,
            created_by_id=user_id,
        )
        await self.inventory_transaction_repository.create(obj=transaction)
        await self.db.commit()

        return await self.inventory_repository.get_by_id_for_business(
            inventory_id=inventory.id,
            business_id=business_id,
        )

    async def set_inventory(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        inventory_set: InventorySet,
        user_id: uuid.UUID,
    ) -> Inventory:
        inventory = await self._get_inventory_for_update(
            business_id=business_id,
            product_id=product_id,
        )

        delta = inventory_set.quantity_on_hand - inventory.quantity_on_hand
        inventory.quantity_on_hand = inventory_set.quantity_on_hand

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            quantity_delta=delta,
            quantity_after=inventory_set.quantity_on_hand,
            transaction_type=inventory_set.transaction_type,
            notes=inventory_set.notes,
            reference=inventory_set.reference,
            created_by_id=user_id,
        )
        await self.inventory_transaction_repository.create(obj=transaction)
        await self.db.commit()

        return await self.inventory_repository.get_by_id_for_business(
            inventory_id=inventory.id,
            business_id=business_id,
        )

    async def list_transactions(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ):
        return await self.inventory_transaction_repository.list_for_business(
            business_id=business_id,
            product_id=product_id,
            offset=offset,
            limit=limit,
        )
