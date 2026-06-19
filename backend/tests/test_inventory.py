import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from tests.concurrency import run_concurrent_session_requests
from tests.factories import DataFactory
from tests.helpers import auth_headers, create_product, register_user


@pytest.mark.asyncio
async def test_initial_stock_creates_restock_transaction(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    initial_quantity = factory.faker.random_int(min=10, max=100)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=initial_quantity,
    )

    response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 1
    assert transactions[0]["transaction_type"] == "RESTOCK"
    assert transactions[0]["quantity_delta"] == initial_quantity
    assert transactions[0]["quantity_after"] == initial_quantity
    assert transactions[0]["created_by_id"] == account["user"]["id"]

    filtered = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        params={"product_id": product["id"]},
        headers=auth_headers(account["token"]),
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


@pytest.mark.asyncio
async def test_adjust_inventory_restock_and_sale(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )

    restock_qty = factory.faker.random_int(min=5, max=20)
    restock = await client.post(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/adjust",
        json={
            "quantity_delta": restock_qty,
            "transaction_type": "RESTOCK",
            "notes": factory.product_description(),
        },
        headers=auth_headers(account["token"]),
    )
    assert restock.status_code == 200
    assert restock.json()["quantity_on_hand"] == 10 + restock_qty

    sale_qty = factory.faker.random_int(min=1, max=5)
    sale = await client.post(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/adjust",
        json={
            "quantity_delta": -sale_qty,
            "transaction_type": "SALE",
            "reference": factory.faker.bothify(text="ORDER-#####"),
        },
        headers=auth_headers(account["token"]),
    )
    assert sale.status_code == 200
    assert sale.json()["quantity_on_hand"] == 10 + restock_qty - sale_qty
    assert sale.json()["available_quantity"] == 10 + restock_qty - sale_qty


@pytest.mark.asyncio
async def test_adjust_inventory_insufficient_stock_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=3,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/adjust",
        json={"quantity_delta": -10, "transaction_type": "SALE"},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient available stock for this adjustment"


@pytest.mark.asyncio
async def test_set_inventory_absolute_quantity(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    initial_quantity = 12
    target_quantity = 7
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=initial_quantity,
    )

    response = await client.put(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/set",
        json={
            "quantity_on_hand": target_quantity,
            "transaction_type": "CORRECTION",
            "notes": factory.faker.sentence(),
        },
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == target_quantity

    transactions = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        params={"product_id": product["id"]},
        headers=auth_headers(account["token"]),
    )
    correction = next(
        tx for tx in transactions.json() if tx["transaction_type"] == "CORRECTION"
    )
    assert correction["quantity_delta"] == target_quantity - initial_quantity
    assert correction["quantity_after"] == target_quantity


@pytest.mark.asyncio
async def test_set_inventory_to_zero_is_allowed(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=4,
    )

    response = await client.put(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/set",
        json={"quantity_on_hand": 0, "transaction_type": "CORRECTION"},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == 0


@pytest.mark.asyncio
async def test_set_inventory_negative_quantity_returns_422(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )

    response = await client.put(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/set",
        json={"quantity_on_hand": -1, "transaction_type": "CORRECTION"},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_inventory_and_low_stock_filter(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    reorder_point = 5
    low_stock = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=2,
        reorder_point=reorder_point,
    )
    await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=20,
        reorder_point=reorder_point,
    )

    all_inventory = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    assert all_inventory.status_code == 200
    assert len(all_inventory.json()) == 2

    low_only = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        params={"low_stock_only": True},
        headers=auth_headers(account["token"]),
    )
    assert low_only.status_code == 200
    assert len(low_only.json()) == 1
    assert low_only.json()[0]["product_id"] == low_stock["id"]


@pytest.mark.asyncio
async def test_inventory_for_unknown_product_returns_404(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    missing_product_id = uuid.uuid4()

    response = await client.post(
        f"/api/businesses/{account['business_id']}/inventory/{missing_product_id}/adjust",
        json={"quantity_delta": 1, "transaction_type": "RESTOCK"},
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_inventory_cross_business_access_returns_404(
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
        quantity=5,
    )

    response = await client.post(
        f"/api/businesses/{outsider['business_id']}/inventory/{product['id']}/adjust",
        json={"quantity_delta": 1, "transaction_type": "RESTOCK"},
        headers=auth_headers(outsider["token"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_inventory_requires_authentication(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/inventory/{product['id']}/adjust",
        json={"quantity_delta": 1, "transaction_type": "RESTOCK"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_concurrent_adjust_only_one_succeeds_on_last_unit(
    session_factory: async_sessionmaker[AsyncSession],
    factory: DataFactory,
) -> None:
    transport = ASGITransport(app=app)

    async def setup_product() -> dict:
        async with AsyncClient(transport=transport, base_url="http://testserver") as setup_client:
            async with session_factory() as session:
                async def override_get_db():
                    try:
                        yield session
                    except Exception:
                        await session.rollback()
                        raise

                app.dependency_overrides[get_db] = override_get_db
                try:
                    account = await register_user(setup_client, factory)
                    product = await create_product(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                        quantity=1,
                    )
                    await session.commit()
                    return {
                        "token": account["token"],
                        "business_id": account["business_id"],
                        "product_id": product["id"],
                    }
                finally:
                    app.dependency_overrides.clear()

    setup = await setup_product()

    async def adjust_down(client: AsyncClient, _session: AsyncSession) -> int:
        response = await client.post(
            f"/api/businesses/{setup['business_id']}/inventory/{setup['product_id']}/adjust",
            json={"quantity_delta": -1, "transaction_type": "SALE"},
            headers=auth_headers(setup["token"]),
        )
        return response.status_code

    results = await run_concurrent_session_requests(
        session_factory,
        workers=2,
        request_factory=adjust_down,
    )
    assert 400 in results
    assert any(status == 200 for status in results)

    async with session_factory() as session:
        inventory = await session.scalar(
            select(Inventory).where(Inventory.product_id == setup["product_id"])
        )
        assert inventory is not None
        assert inventory.quantity_on_hand == 0

        sale_count = await session.scalar(
            select(func.count())
            .select_from(InventoryTransaction)
            .where(
                InventoryTransaction.inventory_id == inventory.id,
                InventoryTransaction.transaction_type == InventoryTransactionType.SALE,
            )
        )
        assert sale_count == 1


@pytest.mark.asyncio
async def test_concurrent_adjust_after_inventory_row_removed_creates_single_row(
    session_factory: async_sessionmaker[AsyncSession],
    factory: DataFactory,
) -> None:
    transport = ASGITransport(app=app)

    async def setup_product_without_inventory() -> dict:
        async with AsyncClient(transport=transport, base_url="http://testserver") as setup_client:
            async with session_factory() as session:
                async def override_get_db():
                    try:
                        yield session
                    except Exception:
                        await session.rollback()
                        raise

                app.dependency_overrides[get_db] = override_get_db
                try:
                    account = await register_user(setup_client, factory)
                    product = await create_product(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                        quantity=0,
                    )
                    await session.execute(
                        delete(Inventory).where(Inventory.product_id == product["id"])
                    )
                    await session.commit()
                    return {
                        "token": account["token"],
                        "business_id": account["business_id"],
                        "product_id": product["id"],
                    }
                finally:
                    app.dependency_overrides.clear()

    setup = await setup_product_without_inventory()

    async def restock(client: AsyncClient, _session: AsyncSession) -> int:
        response = await client.post(
            f"/api/businesses/{setup['business_id']}/inventory/{setup['product_id']}/adjust",
            json={"quantity_delta": 1, "transaction_type": "RESTOCK"},
            headers=auth_headers(setup["token"]),
        )
        return response.status_code

    results = await run_concurrent_session_requests(
        session_factory,
        workers=2,
        request_factory=restock,
    )
    assert results == [200, 200]

    async with session_factory() as session:
        rows = (
            await session.scalars(
                select(Inventory).where(Inventory.product_id == setup["product_id"])
            )
        ).all()
        assert len(rows) == 1
        assert rows[0].quantity_on_hand == 2
