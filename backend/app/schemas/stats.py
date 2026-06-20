from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LowStockProductRead(BaseModel):
    product_id: UUID
    product_name: str
    product_sku: str
    quantity_on_hand: int
    reserved_quantity: int
    available_quantity: int
    reorder_point: int | None


class BusinessStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_count: int = Field(ge=0)
    customer_count: int = Field(ge=0)
    order_count: int = Field(ge=0)
    low_stock_count: int = Field(ge=0)
    low_stock_products: list[LowStockProductRead]
