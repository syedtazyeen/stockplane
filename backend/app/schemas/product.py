from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.inventory_transaction import InventoryTransactionType
from app.models.product import ProductStatus


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity_on_hand: int
    reserved_quantity: int
    reorder_point: int | None
    available_quantity: int
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: ProductStatus = ProductStatus.DRAFT
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    quantity: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("quantity", "initial_quantity"),
    )
    reorder_point: int | None = Field(default=None, ge=0)


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ProductStatus | None = None
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
    reorder_point: int | None = Field(default=None, ge=0)


class ProductPut(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: ProductStatus = ProductStatus.ACTIVE
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    quantity: int = Field(default=0, ge=0)
    reorder_point: int | None = Field(default=None, ge=0)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    description: str | None
    status: ProductStatus
    cost_price: Decimal
    selling_price: Decimal
    quantity: int
    inventory: InventoryRead | None = None


class InventoryAdjust(BaseModel):
    quantity_delta: int = Field(description="Positive to add stock, negative to remove")
    transaction_type: InventoryTransactionType
    notes: str | None = None
    reference: str | None = Field(default=None, max_length=255)


class InventorySet(BaseModel):
    quantity_on_hand: int = Field(ge=0)
    transaction_type: InventoryTransactionType = InventoryTransactionType.CORRECTION
    notes: str | None = None
    reference: str | None = Field(default=None, max_length=255)


class InventoryTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_id: UUID
    quantity_delta: int
    quantity_after: int
    transaction_type: InventoryTransactionType
    notes: str | None
    reference: str | None
    created_by_id: UUID | None
    created_at: datetime
