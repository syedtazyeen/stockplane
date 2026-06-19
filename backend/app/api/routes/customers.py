import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_business_membership, get_customer_service
from app.models.business_member import BusinessMember
from app.models.customer import CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer import CustomerService

router = APIRouter(
    prefix="/businesses/{business_id}/customers",
    tags=["customers"],
)


@router.get("", response_model=list[CustomerRead], summary="List customers for a business")
async def list_customers(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    customer_service: CustomerService = Depends(get_customer_service),
    status_filter: CustomerStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=255),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[CustomerRead]:
    customers = await customer_service.list_customers(
        business_id=business_id,
        status_filter=status_filter,
        search=search,
        offset=offset,
        limit=limit,
    )
    return [CustomerRead.model_validate(customer) for customer in customers]


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer",
)
async def create_customer(
    business_id: uuid.UUID,
    customer_in: CustomerCreate,
    _: BusinessMember = Depends(get_business_membership),
    customer_service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    customer = await customer_service.create_customer(
        business_id=business_id,
        customer_in=customer_in,
    )
    return CustomerRead.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerRead, summary="Get a customer by ID")
async def get_customer(
    business_id: uuid.UUID,
    customer_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    customer_service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    customer = await customer_service.get_customer(
        business_id=business_id,
        customer_id=customer_id,
    )
    return CustomerRead.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerRead, summary="Update a customer")
async def update_customer(
    business_id: uuid.UUID,
    customer_id: uuid.UUID,
    customer_in: CustomerUpdate,
    _: BusinessMember = Depends(get_business_membership),
    customer_service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    customer = await customer_service.update_customer(
        business_id=business_id,
        customer_id=customer_id,
        customer_in=customer_in,
    )
    return CustomerRead.model_validate(customer)


@router.delete(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Soft-delete a customer (sets status to inactive)",
)
async def delete_customer(
    business_id: uuid.UUID,
    customer_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    customer_service: CustomerService = Depends(get_customer_service),
) -> CustomerRead:
    customer = await customer_service.delete_customer(
        business_id=business_id,
        customer_id=customer_id,
    )
    return CustomerRead.model_validate(customer)
