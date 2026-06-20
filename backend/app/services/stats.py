import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.stats import BusinessStatsRead, LowStockProductRead


class StatsService:
    """Aggregated dashboard statistics for a business."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_business_stats(
        self,
        *,
        business_id: uuid.UUID,
        low_stock_limit: int = 50,
    ) -> BusinessStatsRead:
        product_count = await self._count_products(business_id)
        customer_count = await self._count_customers(business_id)
        order_count = await self._count_orders(business_id)
        low_stock_products, low_stock_count = await self._get_low_stock_products(
            business_id=business_id,
            limit=low_stock_limit,
        )

        return BusinessStatsRead(
            product_count=product_count,
            customer_count=customer_count,
            order_count=order_count,
            low_stock_count=low_stock_count,
            low_stock_products=low_stock_products,
        )

    async def _count_products(self, business_id: uuid.UUID) -> int:
        result = await self.db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.business_id == business_id)
        )
        return int(result or 0)

    async def _count_customers(self, business_id: uuid.UUID) -> int:
        result = await self.db.scalar(
            select(func.count())
            .select_from(Customer)
            .where(Customer.business_id == business_id)
        )
        return int(result or 0)

    async def _count_orders(self, business_id: uuid.UUID) -> int:
        result = await self.db.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.business_id == business_id,
                Order.status != OrderStatus.DRAFT,
            )
        )
        return int(result or 0)

    async def _get_low_stock_products(
        self,
        *,
        business_id: uuid.UUID,
        limit: int,
    ) -> tuple[list[LowStockProductRead], int]:
        available_quantity = Inventory.quantity_on_hand - Inventory.reserved_quantity
        low_stock_condition = or_(
            Inventory.quantity_on_hand == 0,
            and_(
                Inventory.reorder_point.is_not(None),
                available_quantity <= Inventory.reorder_point,
            ),
        )

        base_query = (
            select(Inventory, Product)
            .join(Product, Product.id == Inventory.product_id)
            .where(Product.business_id == business_id, low_stock_condition)
        )

        count_result = await self.db.scalar(
            select(func.count())
            .select_from(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Product.business_id == business_id, low_stock_condition)
        )
        low_stock_count = int(count_result or 0)

        result = await self.db.execute(
            base_query.order_by(Product.name).limit(limit)
        )
        rows = result.all()

        products = [
            LowStockProductRead(
                product_id=inventory.product_id,
                product_name=product.name,
                product_sku=product.sku,
                quantity_on_hand=inventory.quantity_on_hand,
                reserved_quantity=inventory.reserved_quantity,
                available_quantity=inventory.available_quantity,
                reorder_point=inventory.reorder_point,
            )
            for inventory, product in rows
        ]

        return products, low_stock_count
