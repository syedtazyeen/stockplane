from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.order import OrderStatus


class OrderLineCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    customer_id: UUID
    lines: list[OrderLineCreate] = Field(min_length=1)
    notes: str | None = None

    @field_validator("lines")
    @classmethod
    def validate_unique_products(
        cls, lines: list[OrderLineCreate]
    ) -> list[OrderLineCreate]:
        product_ids = [line.product_id for line in lines]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate product in order lines")
        return lines


class OrderUpdate(BaseModel):
    notes: str | None = None


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    customer: CustomerSummary
    status: OrderStatus
    notes: str | None
    lines: list[OrderLineRead]
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
