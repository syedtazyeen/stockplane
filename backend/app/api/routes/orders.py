import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, Query, status

from app.core.deps import (
    get_business_membership,
    get_current_active_user,
    get_idempotency_service,
    get_order_service,
)
from app.idempotency import IdempotencyResourceType
from app.idempotency.service import IdempotencyService
from app.models.business_member import BusinessMember
from app.models.order import OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services.order import OrderService

router = APIRouter(
    prefix="/businesses/{business_id}/orders",
    tags=["orders"],
)


def _to_order_read(order) -> OrderRead:
    return OrderRead(
        id=order.id,
        customer_id=order.customer_id,
        customer=order.customer,
        status=order.status,
        notes=order.notes,
        lines=order.lines,
        total_amount=sum((line.line_total for line in order.lines), Decimal("0.00")),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("", response_model=list[OrderRead], summary="List orders for a business")
async def list_orders(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    customer_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[OrderRead]:
    orders = await order_service.list_orders(
        business_id=business_id,
        status_filter=status_filter,
        customer_id=customer_id,
        offset=offset,
        limit=limit,
    )
    return [_to_order_read(order) for order in orders]


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order, optionally saving as draft",
)
async def create_order(
    business_id: uuid.UUID,
    order_in: OrderCreate,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> OrderRead:
    async def place_order() -> OrderRead:
        order = await order_service.create_order(
            business_id=business_id,
            order_in=order_in,
            user_id=current_user.id,
            commit=idempotency_service.normalize_key(idempotency_key) is None,
        )
        return _to_order_read(order)

    return await idempotency_service.execute(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        idempotency_key=idempotency_key,
        request_payload=order_in,
        response_status=status.HTTP_201_CREATED,
        handler=place_order,
        serialize=lambda response: response.model_dump(mode="json"),
        deserialize=OrderRead.model_validate,
        commit=order_service.db.commit,
    )


@router.get("/{order_id}", response_model=OrderRead, summary="Get an order by ID")
async def get_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.get_order(
        business_id=business_id,
        order_id=order_id,
    )
    return _to_order_read(order)


@router.patch("/{order_id}", response_model=OrderRead, summary="Update a draft or pending order")
async def update_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    order_in: OrderUpdate,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.update_order(
        business_id=business_id,
        order_id=order_id,
        order_in=order_in,
    )
    return _to_order_read(order)


@router.post(
    "/{order_id}/submit",
    response_model=OrderRead,
    summary="Submit a draft order and deduct inventory",
)
async def submit_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.submit_order(
        business_id=business_id,
        order_id=order_id,
        user_id=current_user.id,
    )
    return _to_order_read(order)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderRead,
    summary="Confirm a pending order",
)
async def confirm_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.confirm_order(
        business_id=business_id,
        order_id=order_id,
    )
    return _to_order_read(order)


@router.post(
    "/{order_id}/ship",
    response_model=OrderRead,
    summary="Ship a confirmed order",
)
async def ship_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.ship_order(
        business_id=business_id,
        order_id=order_id,
    )
    return _to_order_read(order)


@router.post(
    "/{order_id}/deliver",
    response_model=OrderRead,
    summary="Mark a shipped order as delivered",
)
async def deliver_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.deliver_order(
        business_id=business_id,
        order_id=order_id,
    )
    return _to_order_read(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancel a pending or confirmed order",
)
async def cancel_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await order_service.cancel_order(
        business_id=business_id,
        order_id=order_id,
        user_id=current_user.id,
    )
    return _to_order_read(order)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a draft or pending order",
)
async def delete_order(
    business_id: uuid.UUID,
    order_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service),
) -> None:
    await order_service.delete_order(
        business_id=business_id,
        order_id=order_id,
        user_id=current_user.id,
    )
