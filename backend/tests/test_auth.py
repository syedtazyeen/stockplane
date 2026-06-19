import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User, UserStatus
from tests.factories import DataFactory
from tests.helpers import auth_headers, register_user


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_creates_user_business_and_token(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    business_name = factory.business_name()
    payload = factory.register_payload(business_name=business_name)

    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == payload["email"]
    assert data["user"]["status"] == "ACTIVE"
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["role"] == "OWNER"
    assert data["memberships"][0]["business"]["name"] == business_name


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    payload = factory.register_payload()

    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload,expected_loc",
    [
        ({"password": "password123", "business_name": "Biz"}, "email"),
        ({"email": "not-an-email", "password": "password123", "business_name": "Biz"}, "email"),
        ({"email": "a@b.com", "password": "short", "business_name": "Biz"}, "password"),
        ({"email": "a@b.com", "password": "password123", "business_name": ""}, "business_name"),
    ],
)
async def test_register_validation_errors(
    client: AsyncClient,
    payload: dict,
    expected_loc: str,
) -> None:
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == expected_loc for error in errors)


@pytest.mark.asyncio
async def test_login_with_valid_credentials(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    response = await client.post(
        "/api/auth/login",
        data={"username": account["email"], "password": account["password"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == account["email"]
    assert data["memberships"][0]["business"]["id"] == account["business_id"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    response = await client.post(
        "/api/auth/login",
        data={"username": account["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    response = await client.post(
        "/api/auth/login",
        data={"username": factory.email(), "password": factory.password()},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_me_returns_current_user(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    response = await client.get("/api/auth/me", headers=auth_headers(account["token"]))

    assert response.status_code == 200
    assert response.json()["id"] == account["user"]["id"]
    assert response.json()["email"] == account["email"]


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    ["", "not-a-jwt", "Bearer.bad.token"],
)
async def test_me_with_invalid_token_returns_401(client: AsyncClient, token: str) -> None:
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_suspended_user(
    client: AsyncClient,
    db_session,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    user = await db_session.get(User, uuid.UUID(account["user"]["id"]))
    assert user is not None
    user.status = UserStatus.SUSPENDED
    await db_session.flush()

    response = await client.get("/api/auth/me", headers=auth_headers(account["token"]))
    assert response.status_code == 401
    assert response.json()["detail"] == "Inactive or suspended account"
