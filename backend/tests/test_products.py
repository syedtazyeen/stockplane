import uuid

import pytest
from httpx import AsyncClient

from tests.factories import DataFactory
from tests.helpers import auth_headers, create_product, register_user


@pytest.mark.asyncio
async def test_create_product_with_initial_inventory(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    payload = factory.product_payload(
        quantity=25,
        reorder_point=5,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/products",
        json=payload,
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == payload["sku"]
    assert data["name"] == payload["name"]
    assert data["status"] == "ACTIVE"
    assert data["quantity"] == 25
    assert data["inventory"]["quantity_on_hand"] == 25
    assert data["inventory"]["available_quantity"] == 25
    assert data["inventory"]["reorder_point"] == 5


@pytest.mark.asyncio
async def test_create_product_without_initial_stock_has_no_restock_transaction(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=0,
    )

    response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_product_duplicate_sku_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    sku = factory.sku()
    await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        sku=sku,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/products",
        json=factory.product_payload(sku=sku),
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "SKU already in use"


@pytest.mark.asyncio
async def test_same_sku_allowed_across_different_businesses(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account_a = await register_user(client, factory)
    account_b = await register_user(client, factory)
    shared_sku = factory.sku()

    product_a = await create_product(
        client,
        factory,
        token=account_a["token"],
        business_id=account_a["business_id"],
        sku=shared_sku,
    )
    product_b = await create_product(
        client,
        factory,
        token=account_b["token"],
        business_id=account_b["business_id"],
        sku=shared_sku,
    )

    assert product_a["sku"] == product_b["sku"]
    assert product_a["id"] != product_b["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload,expected_loc",
    [
        ({"name": "No SKU"}, "sku"),
        ({"sku": "", "name": "Empty SKU"}, "sku"),
        ({"sku": "OK", "name": ""}, "name"),
        ({"sku": "OK", "name": "Bad Price", "selling_price": "-1"}, "selling_price"),
        ({"sku": "OK", "name": "Bad Qty", "quantity": -1}, "quantity"),
    ],
)
async def test_create_product_validation_errors(
    client: AsyncClient,
    factory: DataFactory,
    payload: dict,
    expected_loc: str,
) -> None:
    account = await register_user(client, factory)
    response = await client.post(
        f"/api/businesses/{account['business_id']}/products",
        json=payload,
        headers=auth_headers(account["token"]),
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == expected_loc for error in errors)


@pytest.mark.asyncio
async def test_list_products_with_filters(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    active_product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        name="Alpha Shirt",
        status="ACTIVE",
    )
    draft_product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        name="Beta Draft",
        status="DRAFT",
    )

    all_products = await client.get(
        f"/api/businesses/{account['business_id']}/products",
        headers=auth_headers(account["token"]),
    )
    assert all_products.status_code == 200
    assert len(all_products.json()) == 2

    active_only = await client.get(
        f"/api/businesses/{account['business_id']}/products",
        params={"status": "ACTIVE"},
        headers=auth_headers(account["token"]),
    )
    assert active_only.status_code == 200
    assert len(active_only.json()) == 1
    assert active_only.json()[0]["sku"] == active_product["sku"]

    search = await client.get(
        f"/api/businesses/{account['business_id']}/products",
        params={"search": "beta"},
        headers=auth_headers(account["token"]),
    )
    assert search.status_code == 200
    assert len(search.json()) == 1
    assert search.json()[0]["name"] == draft_product["name"]


@pytest.mark.asyncio
async def test_get_update_and_delete_product(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    original_name = factory.product_name()
    created = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        name=original_name,
        quantity=10,
        reorder_point=2,
    )
    product_id = created["id"]
    assert created["quantity"] == 10

    fetched = await client.get(
        f"/api/businesses/{account['business_id']}/products/{product_id}",
        headers=auth_headers(account["token"]),
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == original_name

    updated_name = factory.product_name()
    updated = await client.patch(
        f"/api/businesses/{account['business_id']}/products/{product_id}",
        json={
            "name": updated_name,
            "selling_price": factory.price(),
            "quantity": 15,
            "reorder_point": 8,
        },
        headers=auth_headers(account["token"]),
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["name"] == updated_name
    assert body["quantity"] == 15
    assert body["inventory"]["reorder_point"] == 8

    deleted = await client.delete(
        f"/api/businesses/{account['business_id']}/products/{product_id}",
        headers=auth_headers(account["token"]),
    )
    assert deleted.status_code == 204

    missing = await client.get(
        f"/api/businesses/{account['business_id']}/products/{product_id}",
        headers=auth_headers(account["token"]),
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_put_product_replaces_fields_and_quantity(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    created = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
        reorder_point=2,
    )

    replacement = factory.product_payload(quantity=30, reorder_point=6)
    response = await client.put(
        f"/api/businesses/{account['business_id']}/products/{created['id']}",
        json=replacement,
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sku"] == replacement["sku"]
    assert body["name"] == replacement["name"]
    assert body["quantity"] == 30
    assert body["inventory"]["quantity_on_hand"] == 30
    assert body["inventory"]["reorder_point"] == 6


@pytest.mark.asyncio
async def test_create_product_accepts_initial_quantity_alias(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    payload = factory.product_payload()
    payload.pop("quantity")
    payload["initial_quantity"] = 12

    response = await client.post(
        f"/api/businesses/{account['business_id']}/products",
        json=payload,
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 201
    assert response.json()["quantity"] == 12


@pytest.mark.asyncio
async def test_update_product_duplicate_sku_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    sku_a = factory.sku()
    sku_b = factory.sku()
    await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        sku=sku_a,
    )
    product_b = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        sku=sku_b,
    )

    response = await client.patch(
        f"/api/businesses/{account['business_id']}/products/{product_b['id']}",
        json={"sku": sku_a},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "SKU already in use"


@pytest.mark.asyncio
async def test_product_not_found_returns_404(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    missing_id = uuid.uuid4()

    response = await client.get(
        f"/api/businesses/{account['business_id']}/products/{missing_id}",
        headers=auth_headers(account["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_product_access_requires_authentication(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    response = await client.get(f"/api/businesses/{account['business_id']}/products")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_product_access_denied_for_other_business(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    owner = await register_user(client, factory)
    outsider = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=owner["token"],
        business_id=owner["business_id"],
    )

    response = await client.get(
        f"/api/businesses/{outsider['business_id']}/products/{product['id']}",
        headers=auth_headers(outsider["token"]),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unknown_business_returns_404(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    unknown_business_id = uuid.uuid4()

    response = await client.get(
        f"/api/businesses/{unknown_business_id}/products",
        headers=auth_headers(account["token"]),
    )
    assert response.status_code == 404
