import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from fastapi import status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.exceptions.base import AppError
from app.idempotency.constants import (
    IDEMPOTENCY_IN_PROGRESS_DETAIL,
    IDEMPOTENCY_KEY_REUSED_DETAIL,
)
from app.idempotency.repository import IdempotencyRecordRepository
from app.idempotency.types import IdempotencyBeginResult
from app.models.idempotency_record import IdempotencyRecord, IdempotencyResourceType

T = TypeVar("T")


class IdempotencyService:
    """Generic idempotency handling for mutating API operations."""

    def __init__(self, repository: IdempotencyRecordRepository) -> None:
        self.repository = repository
        self._settings = get_settings()

    @property
    def db(self):
        return self.repository.db

    @staticmethod
    def normalize_key(key: str | None) -> str | None:
        if key is None:
            return None

        normalized = key.strip()
        if not normalized:
            return None
        if len(normalized) > 255:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key must be at most 255 characters",
            )
        return normalized

    @staticmethod
    def hash_payload(payload: BaseModel | dict[str, Any]) -> str:
        if isinstance(payload, BaseModel):
            body = payload.model_dump(mode="json")
        else:
            body = payload
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def default_expires_at(self, *, now: datetime | None = None) -> datetime:
        current = now or datetime.now(UTC)
        return current + timedelta(hours=self._settings.idempotency_ttl_hours)

    async def begin(
        self,
        *,
        business_id: uuid.UUID,
        resource_type: IdempotencyResourceType,
        key: str,
        request_hash: str,
        expires_at: datetime | None = None,
    ) -> IdempotencyBeginResult:
        expiry = expires_at or self.default_expires_at()

        for _attempt in range(2):
            try:
                async with self.db.begin_nested():
                    record = IdempotencyRecord(
                        business_id=business_id,
                        resource_type=resource_type,
                        key=key,
                        request_hash=request_hash,
                        expires_at=expiry,
                    )
                    await self.repository.create(obj=record)
            except IntegrityError:
                replay = await self._resolve_existing_record(
                    business_id=business_id,
                    resource_type=resource_type,
                    key=key,
                    request_hash=request_hash,
                )
                if replay is not None:
                    return replay
                continue

            locked_record = await self.repository.get_by_resource_and_key_for_update(
                business_id=business_id,
                resource_type=resource_type,
                key=key,
            )
            if locked_record is None:
                raise AppError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not reserve idempotency key",
                )
            return IdempotencyBeginResult(record=locked_record)

        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reserve idempotency key",
        )

    async def _resolve_existing_record(
        self,
        *,
        business_id: uuid.UUID,
        resource_type: IdempotencyResourceType,
        key: str,
        request_hash: str,
    ) -> IdempotencyBeginResult | None:
        record = await self.repository.get_by_resource_and_key_for_update(
            business_id=business_id,
            resource_type=resource_type,
            key=key,
        )
        if record is None:
            raise AppError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not resolve idempotency key",
            ) from None

        if record.is_expired():
            await self.repository.delete(obj=record)
            await self.db.flush()
            return None

        if record.request_hash != request_hash:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                detail=IDEMPOTENCY_KEY_REUSED_DETAIL,
            )
        if not record.is_complete:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                detail=IDEMPOTENCY_IN_PROGRESS_DETAIL,
            )

        assert record.response_status is not None
        return IdempotencyBeginResult(
            replay_status=record.response_status,
            replay_body=record.response_body,
        )

    async def complete(
        self,
        *,
        record: IdempotencyRecord,
        response_status: int,
        response_body: dict[str, Any],
    ) -> None:
        record.response_status = response_status
        record.response_body = response_body

    async def cleanup_expired(self, *, before: datetime | None = None) -> int:
        cutoff = before or datetime.now(UTC)
        return await self.repository.delete_expired_before(cutoff=cutoff)

    async def execute(
        self,
        *,
        business_id: uuid.UUID,
        resource_type: IdempotencyResourceType,
        idempotency_key: str | None,
        request_payload: BaseModel | dict[str, Any],
        response_status: int,
        handler: Callable[[], Awaitable[T]],
        serialize: Callable[[T], dict[str, Any]],
        deserialize: Callable[[dict[str, Any]], T],
        commit: Callable[[], Awaitable[None]],
    ) -> T:
        """Run a write operation with optional idempotent request handling."""
        normalized_key = self.normalize_key(idempotency_key)
        if normalized_key is None:
            return await handler()

        begin_result = await self.begin(
            business_id=business_id,
            resource_type=resource_type,
            key=normalized_key,
            request_hash=self.hash_payload(request_payload),
        )
        if begin_result.is_replay:
            assert begin_result.replay_body is not None
            return deserialize(begin_result.replay_body)

        result = await handler()
        assert begin_result.record is not None
        await self.complete(
            record=begin_result.record,
            response_status=response_status,
            response_body=serialize(result),
        )
        await commit()
        return result
