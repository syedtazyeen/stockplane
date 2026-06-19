import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.exceptions.base import AppError
from app.idempotency import (
    IDEMPOTENCY_IN_PROGRESS_DETAIL,
    IDEMPOTENCY_KEY_REUSED_DETAIL,
    IdempotencyResourceType,
)
from app.idempotency.service import IdempotencyService
from app.idempotency.repository import IdempotencyRecordRepository
from app.models.idempotency_record import IdempotencyRecord
from tests.factories import DataFactory
from tests.helpers import (
    auth_headers,
    create_customer,
    create_product,
    persist_business,
    register_user,
)


@pytest.mark.asyncio
async def test_idempotency_service_replays_completed_response(
    db_session,
    factory: DataFactory,
) -> None:
    business_id = await persist_business(db_session, factory)
    repository = IdempotencyRecordRepository(db_session)
    service = IdempotencyService(repository)
    payload = {"value": "ok"}
    request_hash = IdempotencyService.hash_payload(payload)

    begin_result = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="replay-key",
        request_hash=request_hash,
    )
    assert begin_result.record is not None
    await service.complete(
        record=begin_result.record,
        response_status=201,
        response_body={"id": str(uuid.uuid4()), "value": "ok"},
    )
    await db_session.flush()

    replay = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="replay-key",
        request_hash=request_hash,
    )
    assert replay.is_replay
    assert replay.replay_status == 201
    assert replay.replay_body["value"] == "ok"


@pytest.mark.asyncio
async def test_idempotency_service_rejects_request_while_in_progress(
    db_session,
    factory: DataFactory,
) -> None:
    business_id = await persist_business(db_session, factory)
    service = IdempotencyService(IdempotencyRecordRepository(db_session))
    payload = {"value": "in-flight"}
    request_hash = IdempotencyService.hash_payload(payload)

    begin_result = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="in-flight-key",
        request_hash=request_hash,
    )
    assert begin_result.record is not None
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await service.begin(
            business_id=business_id,
            resource_type=IdempotencyResourceType.ORDER,
            key="in-flight-key",
            request_hash=request_hash,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == IDEMPOTENCY_IN_PROGRESS_DETAIL


@pytest.mark.asyncio
async def test_idempotency_service_rejects_conflicting_payload(
    db_session,
    factory: DataFactory,
) -> None:
    business_id = await persist_business(db_session, factory)
    service = IdempotencyService(IdempotencyRecordRepository(db_session))

    first = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="conflict-key",
        request_hash=IdempotencyService.hash_payload({"quantity": 1}),
    )
    await service.complete(
        record=first.record,
        response_status=201,
        response_body={"quantity": 1},
    )
    await db_session.flush()

    with pytest.raises(AppError) as exc_info:
        await service.begin(
            business_id=business_id,
            resource_type=IdempotencyResourceType.ORDER,
            key="conflict-key",
            request_hash=IdempotencyService.hash_payload({"quantity": 2}),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == IDEMPOTENCY_KEY_REUSED_DETAIL


@pytest.mark.asyncio
async def test_idempotency_service_allows_reuse_after_expiry(
    db_session,
    factory: DataFactory,
) -> None:
    business_id = await persist_business(db_session, factory)
    service = IdempotencyService(IdempotencyRecordRepository(db_session))
    expired_at = datetime.now(UTC) - timedelta(hours=1)

    begin_result = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="expired-key",
        request_hash=IdempotencyService.hash_payload({"value": "old"}),
        expires_at=expired_at,
    )
    await service.complete(
        record=begin_result.record,
        response_status=201,
        response_body={"value": "old"},
    )
    await db_session.flush()

    reserved = await service.begin(
        business_id=business_id,
        resource_type=IdempotencyResourceType.ORDER,
        key="expired-key",
        request_hash=IdempotencyService.hash_payload({"value": "new"}),
    )
    assert reserved.record is not None
    assert not reserved.is_replay


@pytest.mark.asyncio
async def test_idempotency_cleanup_expired(
    db_session,
    factory: DataFactory,
) -> None:
    service = IdempotencyService(IdempotencyRecordRepository(db_session))
    repository = IdempotencyRecordRepository(db_session)
    business_id = await persist_business(db_session, factory)

    record = IdempotencyRecord(
        business_id=business_id,
        resource_type=IdempotencyResourceType.PRODUCT,
        key="cleanup-key",
        request_hash="abc",
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        response_status=201,
        response_body={"sku": "OLD"},
    )
    await repository.create(obj=record)
    await db_session.flush()

    deleted = await service.cleanup_expired()
    assert deleted >= 1


@pytest.mark.asyncio
async def test_create_order_idempotency_key_replays_same_order(
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
    payload = {
        "customer_id": customer["id"],
        "lines": [{"product_id": product["id"], "quantity": 2}],
    }
    headers = {
        **auth_headers(account["token"]),
        "Idempotency-Key": "order-create-1",
    }

    first = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json=payload,
        headers=headers,
    )
    second = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json=payload,
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    inventory_response = await client.get(
        f"/api/businesses/{account['business_id']}/inventory",
        headers=auth_headers(account["token"]),
    )
    assert inventory_response.json()[0]["quantity_on_hand"] == 8


@pytest.mark.asyncio
async def test_create_order_idempotency_key_conflict_on_different_body(
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
    headers = {
        **auth_headers(account["token"]),
        "Idempotency-Key": "order-create-conflict",
    }

    first = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 1}],
        },
        headers=headers,
    )
    second = await client.post(
        f"/api/businesses/{account['business_id']}/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 2}],
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == IDEMPOTENCY_KEY_REUSED_DETAIL
