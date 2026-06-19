import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from tests.factories import DataFactory


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def persist_business(
    db_session: AsyncSession,
    factory: DataFactory,
    *,
    name: str | None = None,
) -> uuid.UUID:
    business = Business(name=name or factory.business_name())
    db_session.add(business)
    await db_session.flush()
    return business.id


async def register_user(
    client: AsyncClient,
    factory: DataFactory,
    **overrides: Any,
) -> dict[str, Any]:
    payload = factory.register_payload(**overrides)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "email": payload["email"],
        "password": payload["password"],
        "user": data["user"],
        "token": data["access_token"],
        "business_id": data["memberships"][0]["business"]["id"],
    }


async def create_product(
    client: AsyncClient,
    factory: DataFactory,
    *,
    token: str,
    business_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    payload = factory.product_payload(**overrides)
    response = await client.post(
        f"/api/businesses/{business_id}/products",
        json=payload,
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_customer(
    client: AsyncClient,
    factory: DataFactory,
    *,
    token: str,
    business_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    payload = factory.customer_payload(**overrides)
    response = await client.post(
        f"/api/businesses/{business_id}/customers",
        json=payload,
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_order(
    client: AsyncClient,
    factory: DataFactory,
    *,
    token: str,
    business_id: str,
    customer_id: str,
    product_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    payload = factory.order_payload(customer_id=customer_id, product_id=product_id, **overrides)
    response = await client.post(
        f"/api/businesses/{business_id}/orders",
        json=payload,
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def submit_order(
    client: AsyncClient,
    *,
    token: str,
    business_id: str,
    order_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/businesses/{business_id}/orders/{order_id}/submit",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


async def confirm_order(
    client: AsyncClient,
    *,
    token: str,
    business_id: str,
    order_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/businesses/{business_id}/orders/{order_id}/confirm",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


async def advance_order_to_confirmed(
    client: AsyncClient,
    *,
    token: str,
    business_id: str,
    order_id: str,
) -> dict[str, Any]:
    return await confirm_order(
        client, token=token, business_id=business_id, order_id=order_id
    )


async def ship_order(
    client: AsyncClient,
    *,
    token: str,
    business_id: str,
    order_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/businesses/{business_id}/orders/{order_id}/ship",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


async def deliver_order(
    client: AsyncClient,
    *,
    token: str,
    business_id: str,
    order_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/businesses/{business_id}/orders/{order_id}/deliver",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return response.json()
