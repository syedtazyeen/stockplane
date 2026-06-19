from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.user import User


class InventoryTransactionType(enum.Enum):
    """Type of inventory movement."""

    RESTOCK = "RESTOCK"
    SALE = "SALE"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"
    CORRECTION = "CORRECTION"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    ORDER_CANCELLATION = "ORDER_CANCELLATION"
    OTHER = "OTHER"


class InventoryTransaction(Base):
    """Audit log for inventory changes."""

    __tablename__ = "inventory_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)

    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)

    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        Enum(InventoryTransactionType, name="inventory_transaction_type_enum"),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reference: Mapped[str | None] = mapped_column(String(length=255), nullable=True)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    inventory: Mapped["Inventory"] = relationship(back_populates="transactions")
    created_by: Mapped["User | None"] = relationship()
