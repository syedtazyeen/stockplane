import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.services.order import CANCELLATION_NOT_ALLOWED_DETAIL
from tests.concurrency import run_concurrent_session_requests, run_mixed_concurrent_session_requests
from tests.factories import DataFactory
from tests.helpers import (
    advance_order_to_confirmed,
    auth_headers,
    confirm_order,
    create_customer,
    create_order,
    create_product,
    deliver_order,
    register_user,
    ship_order,
)


@pytest.mark.asyncio
async def test_create_order_places_order_and_deducts_stock(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )

    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
    )

    assert order["status"] == "PENDING"

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory = inventory_response.json()[0]
    assert inventory["quantity_on_hand"] == 7
    assert inventory["reserved_quantity"] == 0
    assert inventory["available_quantity"] == 7


@pytest.mark.asyncio
async def test_create_order_save_as_draft_skips_inventory_deduction(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )

    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
        save_as_draft=True,
    )

    assert order["status"] == "DRAFT"

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory = inventory_response.json()[0]
    assert inventory["quantity_on_hand"] == 10


@pytest.mark.asyncio
async def test_create_order_insufficient_stock_returns_400(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=2,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 5}],
        },
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient available stock"


@pytest.mark.asyncio
async def test_create_order_requires_existing_customer(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=5,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": str(uuid.uuid4()),
            "lines": [{"product_id": product["id"], "quantity": 1}],
        },
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


@pytest.mark.asyncio
async def test_create_order_inactive_customer_returns_400(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        status="INACTIVE",
    )
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=5,
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 1}],
        },
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Customer must be active to place an order"


@pytest.mark.asyncio
async def test_ship_order_does_not_change_already_deducted_stock(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 4}],
    )
    await advance_order_to_confirmed(
        client,
        token=account["token"],
        business_id=account["business_id"],
        order_id=order["id"],
    )

    ship_response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/ship",
        headers=auth_headers(account["token"]),
    )

    assert ship_response.status_code == 200
    assert ship_response.json()["status"] == "SHIPPED"

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory = inventory_response.json()[0]
    assert inventory["quantity_on_hand"] == 6
    assert inventory["reserved_quantity"] == 0
    assert inventory["available_quantity"] == 6


@pytest.mark.asyncio
async def test_second_order_respects_deducted_stock(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=5,
    )
    await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 4}],
    )

    response = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 2}],
        },
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient available stock"


@pytest.mark.asyncio
@pytest.mark.parametrize("advance_to", ["PENDING", "CONFIRMED"])
async def test_cancel_order_in_cancellable_statuses_restores_inventory(
    client: AsyncClient,
    factory: DataFactory,
    advance_to: str,
) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
    )

    if advance_to == "CONFIRMED":
        await confirm_order(
            client,
            token=account["token"],
            business_id=account["business_id"],
            order_id=order["id"],
        )

    cancel_response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory = inventory_response.json()[0]
    assert inventory["quantity_on_hand"] == 10
    assert inventory["reserved_quantity"] == 0
    assert inventory["available_quantity"] == 10

    transactions_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        headers=auth_headers(account["token"]),
    )
    cancellation_txns = [
        txn
        for txn in transactions_response.json()
        if txn["transaction_type"] == "ORDER_CANCELLATION"
    ]
    assert len(cancellation_txns) == 1
    assert cancellation_txns[0]["quantity_delta"] == 3


@pytest.mark.asyncio
async def test_cancel_order_restores_deducted_inventory_when_not_reserved(
    client: AsyncClient,
    factory: DataFactory,
    db_session: AsyncSession,
) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
    )
    await confirm_order(
        client,
        token=account["token"],
        business_id=account["business_id"],
        order_id=order["id"],
    )

    result = await db_session.execute(
        select(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .where(Product.id == uuid.UUID(product["id"]))
    )
    inventory = result.scalar_one()
    inventory.reserved_quantity = 0
    inventory.quantity_on_hand = 7
    await db_session.flush()

    cancel_response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory_data = inventory_response.json()[0]
    assert inventory_data["quantity_on_hand"] == 10
    assert inventory_data["reserved_quantity"] == 0

    transactions_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory/transactions",
        headers=auth_headers(account["token"]),
    )
    cancellation_txns = [
        txn
        for txn in transactions_response.json()
        if txn["transaction_type"] == "ORDER_CANCELLATION"
    ]
    assert cancellation_txns[0]["quantity_delta"] == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("target_status", ["SHIPPED", "DELIVERED"])
async def test_cancel_order_rejected_for_shipped_and_delivered(
    client: AsyncClient,
    factory: DataFactory,
    target_status: str,
) -> None:
    account = await register_user(client, factory)
    customer = await create_customer(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
    )
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
    )
    await advance_order_to_confirmed(
        client,
        token=account["token"],
        business_id=account["business_id"],
        order_id=order["id"],
    )
    await ship_order(
        client,
        token=account["token"],
        business_id=account["business_id"],
        order_id=order["id"],
    )
    if target_status == "DELIVERED":
        await deliver_order(
            client,
            token=account["token"],
            business_id=account["business_id"],
            order_id=order["id"],
        )

    before_inventory = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    before_order = await client.get(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )

    cancel_response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    assert cancel_response.status_code == 400
    assert cancel_response.json()["detail"] == CANCELLATION_NOT_ALLOWED_DETAIL

    after_inventory = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    after_order = await client.get(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )
    assert after_order.json() == before_order.json()
    assert after_inventory.json() == before_inventory.json()


@pytest.mark.asyncio
async def test_cancel_already_cancelled_order_is_rejected(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=10,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
        lines=[{"product_id": product["id"], "quantity": 3}],
    )
    await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    before_order = await client.get(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )

    cancel_response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    assert cancel_response.status_code == 400
    assert cancel_response.json()["detail"] == CANCELLATION_NOT_ALLOWED_DETAIL

    after_order = await client.get(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )
    assert after_order.json() == before_order.json()


@pytest.mark.asyncio
async def test_cancel_nonexistent_order_returns_404(
    client: AsyncClient,
    factory: DataFactory,
) -> None:
    account = await register_user(client, factory)

    response = await client.post(
        f"/api/businesses/{account['business_id']}/orders/{uuid.uuid4()}/cancel",
        headers=auth_headers(account["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_delete_pending_order_restores_stock(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=5,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
    )

    delete_response = await client.delete(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )
    assert delete_response.status_code == 204

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    inventory = inventory_response.json()[0]
    assert inventory["quantity_on_hand"] == 5
    assert inventory["reserved_quantity"] == 0


@pytest.mark.asyncio
async def test_delete_cancelled_order_returns_400(
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
    product = await create_product(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        quantity=5,
    )
    order = await create_order(
        client,
        factory,
        token=account["token"],
        business_id=account["business_id"],
        customer_id=customer["id"],
        product_id=product["id"],
    )
    await client.post(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}/cancel",
        headers=auth_headers(account["token"]),
    )

    delete_response = await client.delete(
        f"/api/businesses/{account['business_id']}/orders/{order['id']}",
        headers=auth_headers(account["token"]),
    )
    assert delete_response.status_code == 400
    assert delete_response.json()["detail"] == "Only draft or pending orders can be deleted"


@pytest.mark.asyncio
async def test_concurrent_create_only_one_succeeds_on_last_unit(
    session_factory: async_sessionmaker[AsyncSession],
    factory: DataFactory,
) -> None:
    transport = ASGITransport(app=app)

    async def setup_account() -> dict:
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
                    customer = await create_customer(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                    )
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
                        "customer_id": customer["id"],
                        "product_id": product["id"],
                    }
                finally:
                    app.dependency_overrides.clear()

    setup = await setup_account()

    async def place_order() -> int:
        async with AsyncClient(transport=transport, base_url="http://testserver") as order_client:
            async with session_factory() as session:
                async def override_get_db():
                    try:
                        yield session
                    except Exception:
                        await session.rollback()
                        raise

                app.dependency_overrides[get_db] = override_get_db
                try:
                    response = await order_client.post(
                        f"/api/businesses/{setup['business_id']}/orders",
                        json={
                            "customer_id": setup["customer_id"],
                            "lines": [{"product_id": setup["product_id"], "quantity": 1}],
                        },
                        headers=auth_headers(setup["token"]),
                    )
                    if response.status_code == 201:
                        await session.commit()
                    else:
                        await session.rollback()
                    return response.status_code
                finally:
                    app.dependency_overrides.clear()

    results = await asyncio.gather(
        place_order(),
        place_order(),
    )
    assert sorted(results) == [201, 400]


@pytest.mark.asyncio
async def test_concurrent_multi_product_orders_only_one_succeeds(
    session_factory: async_sessionmaker[AsyncSession],
    factory: DataFactory,
) -> None:
    transport = ASGITransport(app=app)

    async def setup_account() -> dict:
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
                    customer = await create_customer(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                    )
                    product_a = await create_product(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                        quantity=1,
                    )
                    product_b = await create_product(
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
                        "customer_id": customer["id"],
                        "product_a_id": product_a["id"],
                        "product_b_id": product_b["id"],
                    }
                finally:
                    app.dependency_overrides.clear()

    setup = await setup_account()

    async def place_multi_line_order(client: AsyncClient, _session: AsyncSession) -> int:
        response = await client.post(
            f"/api/businesses/{setup['business_id']}/orders",
            json={
                "customer_id": setup["customer_id"],
                "lines": [
                    {"product_id": setup["product_a_id"], "quantity": 1},
                    {"product_id": setup["product_b_id"], "quantity": 1},
                ],
            },
            headers=auth_headers(setup["token"]),
        )
        return response.status_code

    results = await run_concurrent_session_requests(
        session_factory,
        workers=2,
        request_factory=place_multi_line_order,
    )
    assert 400 in results
    assert any(status == 201 for status in results)

    async with session_factory() as session:
        inventories = (
            await session.scalars(
                select(Inventory)
                .join(Product, Product.id == Inventory.product_id)
                .where(Product.business_id == setup["business_id"])
                .order_by(Inventory.product_id)
            )
        ).all()
        assert len(inventories) == 2
        assert all(inventory.quantity_on_hand == 0 for inventory in inventories)

        order_count = await session.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.business_id == setup["business_id"],
                Order.status == OrderStatus.PENDING,
            )
        )
        assert order_count == 1


@pytest.mark.asyncio
async def test_concurrent_order_and_adjust_only_one_succeeds_on_last_unit(
    session_factory: async_sessionmaker[AsyncSession],
    factory: DataFactory,
) -> None:
    transport = ASGITransport(app=app)

    async def setup_account() -> dict:
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
                    customer = await create_customer(
                        setup_client,
                        factory,
                        token=account["token"],
                        business_id=account["business_id"],
                    )
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
                        "customer_id": customer["id"],
                        "product_id": product["id"],
                    }
                finally:
                    app.dependency_overrides.clear()

    setup = await setup_account()

    async def place_order(client: AsyncClient, _session: AsyncSession) -> int:
        response = await client.post(
            f"/api/businesses/{setup['business_id']}/orders",
            json={
                "customer_id": setup["customer_id"],
                "lines": [{"product_id": setup["product_id"], "quantity": 1}],
            },
            headers=auth_headers(setup["token"]),
        )
        return response.status_code

    async def adjust_down(client: AsyncClient, _session: AsyncSession) -> int:
        response = await client.post(
            f"/api/businesses/{setup['business_id']}/inventory/{setup['product_id']}/adjust",
            json={"quantity_delta": -1, "transaction_type": "SALE"},
            headers=auth_headers(setup["token"]),
        )
        return response.status_code

    results = await run_mixed_concurrent_session_requests(
        session_factory,
        request_factories=[place_order, adjust_down],
    )
    assert 400 in results
    assert any(status < 400 for status in results)

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
