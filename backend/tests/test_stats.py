import pytest
from httpx import AsyncClient

from tests.factories import DataFactory
from tests.helpers import (
    auth_headers,
    create_customer,
    create_order,
    create_product,
    register_user,
)


@pytest.mark.asyncio
async def test_get_business_stats(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    product_a = await create_product(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
        quantity=0,
        reorder_point=5,
    )
    product_b = await create_product(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
        quantity=4,
        reorder_point=10,
    )
    await create_product(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
        quantity=100,
        reorder_point=5,
    )

    await create_customer(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
    )
    await create_customer(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
    )

    customer = await create_customer(
        client,
        token=account["token"],
        business_id=account["business_id"],
        factory=factory,
    )
    await create_order(
        client,
        factory=factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product_b["id"],
    )

    response = await client.get(
        f"/api/businesses/{account['business_id']}/stats",
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_count"] == 3
    assert data["customer_count"] == 3
    assert data["order_count"] == 1
    assert data["low_stock_count"] == 2

    low_stock_ids = {item["product_id"] for item in data["low_stock_products"]}
    assert product_a["id"] in low_stock_ids
    assert product_b["id"] in low_stock_ids


@pytest.mark.asyncio
async def test_get_business_stats_requires_membership(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    other = await register_user(client, factory)

    response = await client.get(
        f"/api/businesses/{account['business_id']}/stats",
        headers=auth_headers(other["token"]),
    )

    assert response.status_code == 404
