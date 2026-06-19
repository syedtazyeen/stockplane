from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IdempotencyResourceType(enum.Enum):
    """Typed resource identifiers for idempotent write operations."""

    ORDER = "ORDER"
    PRODUCT = "PRODUCT"
    CUSTOMER = "CUSTOMER"


class IdempotencyRecord(Base):
    """Idempotency records scoped per business and resource type."""

    __tablename__ = "idempotency_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[IdempotencyResourceType] = mapped_column(
        Enum(IdempotencyResourceType, name="idempotency_resource_type_enum"),
        nullable=False,
    )

    key: Mapped[str] = mapped_column(String(length=255), nullable=False)

    request_hash: Mapped[str] = mapped_column(String(length=64), nullable=False)

    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)

    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "resource_type",
            "key",
            name="uq_idempotency_business_resource_key",
        ),
    )

    @property
    def is_complete(self) -> bool:
        return self.response_body is not None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return self.expires_at <= current
