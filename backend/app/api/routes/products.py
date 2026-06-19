import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_business_membership, get_current_active_user, get_product_service
from app.models.business_member import BusinessMember
from app.models.product import ProductStatus
from app.models.user import User
from app.schemas.product import ProductCreate, ProductPut, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(
    prefix="/businesses/{business_id}/products",
    tags=["products"],
)


def _to_product_read(product) -> ProductRead:
    inventory = product.inventory
    return ProductRead(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        status=product.status,
        cost_price=product.cost_price,
        selling_price=product.selling_price,
        quantity=inventory.quantity_on_hand if inventory else 0,
        inventory=inventory,
    )


@router.get("", response_model=list[ProductRead], summary="List products for a business")
async def list_products(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    product_service: ProductService = Depends(get_product_service),
    status_filter: ProductStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=255),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ProductRead]:
    products = await product_service.list_products(
        business_id=business_id,
        status_filter=status_filter,
        search=search,
        offset=offset,
        limit=limit,
    )
    return [_to_product_read(product) for product in products]


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product with optional initial stock",
)
async def create_product(
    business_id: uuid.UUID,
    product_in: ProductCreate,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await product_service.create_product(
        business_id=business_id,
        product_in=product_in,
        user_id=current_user.id,
    )
    return _to_product_read(product)


@router.get("/{product_id}", response_model=ProductRead, summary="Get a product by ID")
async def get_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    product_service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await product_service.get_product(
        business_id=business_id,
        product_id=product_id,
    )
    return _to_product_read(product)


@router.put("/{product_id}", response_model=ProductRead, summary="Replace a product")
async def replace_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    product_in: ProductPut,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await product_service.replace_product(
        business_id=business_id,
        product_id=product_id,
        product_in=product_in,
        user_id=current_user.id,
    )
    return _to_product_read(product)


@router.patch("/{product_id}", response_model=ProductRead, summary="Partially update a product")
async def update_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    _: BusinessMember = Depends(get_business_membership),
    current_user: User = Depends(get_current_active_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await product_service.update_product(
        business_id=business_id,
        product_id=product_id,
        product_in=product_in,
        user_id=current_user.id,
    )
    return _to_product_read(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product")
async def delete_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    product_service: ProductService = Depends(get_product_service),
) -> None:
    await product_service.delete_product(
        business_id=business_id,
        product_id=product_id,
    )
