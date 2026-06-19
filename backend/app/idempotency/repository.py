import uuid
from datetime import datetime

from sqlalchemy import delete, select

from app.models.idempotency_record import IdempotencyRecord, IdempotencyResourceType
from app.repositories.base import BaseRepository


class IdempotencyRecordRepository(BaseRepository[IdempotencyRecord]):
    """Persistence layer for generic idempotency records."""

    model = IdempotencyRecord

    async def get_by_resource_and_key_for_update(
        self,
        *,
        business_id: uuid.UUID,
        resource_type: IdempotencyResourceType,
        key: str,
    ) -> IdempotencyRecord | None:
        result = await self.db.execute(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.business_id == business_id,
                IdempotencyRecord.resource_type == resource_type,
                IdempotencyRecord.key == key,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def delete_expired_before(self, *, cutoff: datetime) -> int:
        result = await self.db.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.expires_at <= cutoff)
        )
        return result.rowcount or 0
