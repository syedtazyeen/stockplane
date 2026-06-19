import uuid
import enum
from datetime import datetime

from sqlalchemy import String, text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class CustomerStatus(enum.Enum):
    """Customer status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class Customer(Base):
    """Customer model."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status_enum"),
        nullable=False,
        default=CustomerStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        server_onupdate=text("now()"),
    )

    __table_args__ = (
        UniqueConstraint("business_id", "email", name="uq_business_id_email"),
        UniqueConstraint("business_id", "phone", name="uq_business_id_phone"),
    )
