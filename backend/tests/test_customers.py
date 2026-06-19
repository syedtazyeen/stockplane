import pytest
from httpx import AsyncClient

from tests.factories import DataFactory
from tests.helpers import auth_headers, create_customer, register_user


@pytest.mark.asyncio
async def test_create_customer(client: AsyncClient, factory: DataFactory) -> None:
    account = await register_user(client, factory)
    payload = factory.customer_payload()

    response = await client.post(
        f"/api/businesses/{account['business_id']}/customers",
        json=payload,
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_create_customer_duplicate_email_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    email = factory.email()
    await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        email=email,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/customers",
        json=factory.customer_payload(email=email),
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already in use"


@pytest.mark.asyncio
async def test_create_customer_duplicate_phone_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    phone = factory.phone()
    await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        phone=phone,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/customers",
        json=factory.customer_payload(phone=phone),
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Phone already in use"


@pytest.mark.asyncio
async def test_same_email_allowed_across_different_businesses(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account_a = await register_user(client, factory)
    account_b = await register_user(client, factory)
    shared_email = factory.email()

    customer_a = await create_customer(
        client,
        factory,
        token=account_a["token"],
        business_id=account_a["business_id"],
        email=shared_email,
    )
    customer_b = await create_customer(
        client,
        factory,
        token=account_b["token"],
        business_id=account_b["business_id"],
        email=shared_email,
    )

    assert customer_a["email"] == customer_b["email"]
    assert customer_a["id"] != customer_b["id"]


@pytest.mark.asyncio
async def test_list_and_get_customer(client: AsyncClient, factory: DataFactory) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )

    list_response = await client.get(
        f"/api/businesses/{account['business_id']}/customers",
        headers=auth_headers(account["token"]),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(
        f"/api/businesses/{account['business_id']}/customers/{customer['id']}",
        headers=auth_headers(account["token"]),
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == customer["id"]


@pytest.mark.asyncio
async def test_update_customer(client: AsyncClient, factory: DataFactory) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )

    response = await client.patch(
        f"/api/businesses/{account['business_id']}/customers/{customer['id']}",
        json={"name": "Updated Name", "status": "INACTIVE"},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_delete_customer_soft_deletes_to_inactive(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )

    delete_response = await client.delete(
        f"/api/businesses/{account['business_id']}/customers/{customer['id']}",
        headers=auth_headers(account["token"]),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "INACTIVE"

    get_response = await client.get(
        f"/api/businesses/{account['business_id']}/customers/{customer['id']}",
        headers=auth_headers(account["token"]),
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_get_customer_from_other_business_returns_404(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account_a = await register_user(client, factory)
    account_b = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account_a["token"],
        business_id=account_a["business_id"],
    )

    response = await client.get(
        f"/api/businesses/{account_b['business_id']}/customers/{customer['id']}",
        headers=auth_headers(account_b["token"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_customer_endpoints_require_auth(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    response = await client.get(f"/api/businesses/{account['business_id']}/customers")
    assert response.status_code == 401
