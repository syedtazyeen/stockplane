import uuid
from datetime import UTC, datetime

from fastapi import status

from app.exceptions.base import AppError
from app.models.customer import CustomerStatus
from app.models.inventory import Inventory
from app.models.order import Order, OrderLine, OrderStatus
from app.models.order_transitions import CANCELLABLE_STATUSES, INVENTORY_AFFECTED_STATUSES
from app.models.product import Product, ProductStatus
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderLineRepository, OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.inventory import InventoryService

CANCELLATION_NOT_ALLOWED_DETAIL = "Order cannot be cancelled in current status"


class OrderService:
    """Order workflows with inventory deduction on placement."""

    def __init__(
        self,
        order_repository: OrderRepository,
        order_line_repository: OrderLineRepository,
        customer_repository: CustomerRepository,
        product_repository: ProductRepository,
        inventory_service: InventoryService,
    ) -> None:
        self.order_repository = order_repository
        self.order_line_repository = order_line_repository
        self.customer_repository = customer_repository
        self.product_repository = product_repository
        self.inventory_service = inventory_service

    @property
    def db(self):
        return self.order_repository.db

    async def list_orders(
        self,
        *,
        business_id: uuid.UUID,
        status_filter: OrderStatus | None = None,
        customer_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        return await self.order_repository.list_for_business(
            business_id=business_id,
            status=status_filter,
            customer_id=customer_id,
            offset=offset,
            limit=limit,
        )

    async def get_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        order = await self.order_repository.get_by_id_for_business(
            order_id=order_id,
            business_id=business_id,
        )
        if order is None:
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    async def _validate_customer_for_order(
        self, *, business_id: uuid.UUID, customer_id: uuid.UUID
    ) -> None:
        customer = await self.customer_repository.get_by_id_for_business(
            customer_id=customer_id,
            business_id=business_id,
        )
        if customer is None:
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        if customer.status != CustomerStatus.ACTIVE:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer must be active to place an order",
            )

    async def _validate_products_for_order(
        self,
        *,
        business_id: uuid.UUID,
        lines: list,
    ) -> dict[uuid.UUID, Product]:
        product_ids = [line.product_id for line in lines]
        products_by_id: dict[uuid.UUID, Product] = {}
        for product_id in product_ids:
            product = await self.product_repository.get_by_id_for_business(
                product_id=product_id,
                business_id=business_id,
            )
            if product is None:
                raise AppError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )
            if product.status != ProductStatus.ACTIVE:
                raise AppError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product must be active to order",
                )
            products_by_id[product_id] = product
        return products_by_id

    async def _deduct_order_lines(
        self,
        *,
        lines: list,
        order_id: uuid.UUID,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        notes_template: str,
        inventory_by_product: dict[uuid.UUID, Inventory] | None = None,
    ) -> None:
        if inventory_by_product is None:
            product_ids = [line.product_id for line in lines]
            inventory_by_product = await self.inventory_service.get_many_for_update(
                product_ids=product_ids,
                business_id=business_id,
            )

        for line in lines:
            await self.inventory_service.deduct_for_order(
                business_id=business_id,
                product_id=line.product_id,
                quantity=line.quantity,
                order_id=order_id,
                user_id=user_id,
                inventory_by_product=inventory_by_product,
                notes=notes_template.format(quantity=line.quantity),
            )

    async def create_order(
        self,
        *,
        business_id: uuid.UUID,
        order_in: OrderCreate,
        user_id: uuid.UUID,
        commit: bool = True,
    ) -> Order:
        await self._validate_customer_for_order(
            business_id=business_id,
            customer_id=order_in.customer_id,
        )
        products_by_id = await self._validate_products_for_order(
            business_id=business_id,
            lines=order_in.lines,
        )
        product_ids = [line.product_id for line in order_in.lines]
        inventory_by_product = await self.inventory_service.get_many_for_update(
            product_ids=product_ids,
            business_id=business_id,
        )

        order = Order(
            business_id=business_id,
            customer_id=order_in.customer_id,
            status=OrderStatus.PENDING,
            notes=order_in.notes,
            created_by_id=user_id,
        )
        await self.order_repository.create(obj=order)

        for line_in in order_in.lines:
            product = products_by_id[line_in.product_id]
            line = OrderLine(
                order_id=order.id,
                product_id=product.id,
                quantity=line_in.quantity,
                unit_price=product.selling_price,
                product_sku=product.sku,
                product_name=product.name,
            )
            await self.order_line_repository.create(obj=line)

        await self._deduct_order_lines(
            lines=order_in.lines,
            order_id=order.id,
            business_id=business_id,
            user_id=user_id,
            notes_template="Deducted {quantity} units for order",
            inventory_by_product=inventory_by_product,
        )

        if commit:
            await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def submit_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status != OrderStatus.DRAFT:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft orders can be submitted",
            )
        if not order.lines:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must have at least one line item",
            )

        await self._deduct_order_lines(
            lines=order.lines,
            order_id=order.id,
            business_id=business_id,
            user_id=user_id,
            notes_template="Deducted {quantity} units on order submission",
        )

        order.status = OrderStatus.PENDING
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def confirm_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status != OrderStatus.PENDING:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending orders can be confirmed",
            )

        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def ship_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status != OrderStatus.CONFIRMED:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only confirmed orders can be shipped",
            )

        order.status = OrderStatus.SHIPPED
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def deliver_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status != OrderStatus.SHIPPED:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only shipped orders can be delivered",
            )

        order.status = OrderStatus.DELIVERED
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def update_order(
        self,
        *,
        business_id: uuid.UUID,
        order_id: uuid.UUID,
        order_in: OrderUpdate,
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status not in (OrderStatus.DRAFT, OrderStatus.PENDING):
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft or pending orders can be updated",
            )

        update_data = order_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def cancel_order(
        self, *, business_id: uuid.UUID, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status not in CANCELLABLE_STATUSES:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CANCELLATION_NOT_ALLOWED_DETAIL,
            )

        if order.status in INVENTORY_AFFECTED_STATUSES:
            await self.inventory_service.restore_order_lines(
                lines=order.lines,
                order_id=order.id,
                business_id=business_id,
                user_id=user_id,
                restored_notes="Restored {quantity} deducted units on order cancellation",
            )

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_order(business_id=business_id, order_id=order.id)

    async def delete_order(
        self,
        *,
        business_id: uuid.UUID,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        order = await self.get_order(business_id=business_id, order_id=order_id)
        if order.status not in (OrderStatus.DRAFT, OrderStatus.PENDING):
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft or pending orders can be deleted",
            )

        if order.status == OrderStatus.PENDING:
            await self.inventory_service.restore_order_lines(
                lines=order.lines,
                order_id=order.id,
                business_id=business_id,
                user_id=user_id,
                restored_notes="Restored {quantity} units from deleted order",
            )

        await self.order_repository.delete(obj=order)
        await self.db.commit()
