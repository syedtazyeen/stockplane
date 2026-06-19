import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_business_membership, get_current_active_user, get_inventory_service
from app.models.business_member import BusinessMember
from app.models.user import User
from app.schemas.product import InventoryAdjust, InventoryRead, InventorySet, InventoryTransactionRead
from app.services.inventory import InventoryService

router = APIRouter(
    prefix="/businesses/{business_id}/inventory",
    tags=["inventory"],
)


@router.get("", response_model=list[InventoryRead], summary="List inventory levels for a business")
async def list_inventory(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    inventory_service: InventoryService = Depends(get_inventory_service),
    low_stock_only: bool = Query(default=False),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[InventoryRead]:
    items = await inventory_service.list_inventory(
        business_id=business_id,
        low_stock_only=low_stock_only,
        offset=offset,
        limit=limit,
    )
    return [InventoryRead.model_validate(item) for item in items]


@router.get(
    "/transactions",
    response_model=list[InventoryTransactionRead],
    summary="List inventory transaction history",
)
async def list_inventory_transactions(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    inventory_service: InventoryService = Depends(get_inventory_service),
    product_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[InventoryTransactionRead]:
    transactions = await inventory_service.list_transactions(
        business_id=business_id,
        product_id=product_id,
        offset=offset,
        limit=limit,
    )
    return [InventoryTransactionRead.model_validate(tx) for tx in transactions]


@router.post(
    "/{product_id}/adjust",
    response_model=InventoryRead,
    summary="Adjust stock by a relative quantity delta",
)
async def adjust_inventory(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    adjustment: InventoryAdjust,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    inventory_service: InventoryService = Depends(get_inventory_service),
) -> InventoryRead:
    inventory = await inventory_service.adjust_inventory(
        business_id=business_id,
        product_id=product_id,
        adjustment=adjustment,
        user_id=current_user.id,
    )
    return InventoryRead.model_validate(inventory)


@router.put(
    "/{product_id}/set",
    response_model=InventoryRead,
    summary="Set stock to an absolute quantity",
)
async def set_inventory(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    inventory_set: InventorySet,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    inventory_service: InventoryService = Depends(get_inventory_service),
) -> InventoryRead:
    inventory = await inventory_service.set_inventory(
        business_id=business_id,
        product_id=product_id,
        inventory_set=inventory_set,
        user_id=current_user.id,
    )
    return InventoryRead.model_validate(inventory)
