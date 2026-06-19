"""Order status transition rules.

Valid forward transitions:
    PENDING -> CONFIRMED -> SHIPPED -> DELIVERED

Allowed cancellation transitions:
    PENDING -> CANCELLED
    CONFIRMED -> CANCELLED

No other status may transition to CANCELLED.
"""

from app.models.order import OrderStatus

CANCELLABLE_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.PENDING,
        OrderStatus.CONFIRMED,
    }
)

INVENTORY_AFFECTED_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.PENDING,
        OrderStatus.CONFIRMED,
    }
)

NON_CANCELLABLE_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
        OrderStatus.RETURNED,
        OrderStatus.REFUNDED,
    }
)
