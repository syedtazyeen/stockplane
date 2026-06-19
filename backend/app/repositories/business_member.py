import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.business import Business
from app.models.business_member import BusinessMember
from app.repositories.base import BaseRepository


class BusinessMemberRepository(BaseRepository[BusinessMember]):
    """Repository for BusinessMember."""

    model = BusinessMember

    async def get_businesses_for_user(self, user_id: uuid.UUID) -> list[Business]:
        result = await self.db.execute(
            select(Business)
            .join(BusinessMember, BusinessMember.business_id == Business.id)
            .where(BusinessMember.user_id == user_id)
            .order_by(Business.created_at)
        )
        return list(result.scalars().all())

    async def get_memberships_for_user(
        self, user_id: uuid.UUID
    ) -> list[BusinessMember]:
        result = await self.db.execute(
            select(BusinessMember)
            .where(BusinessMember.user_id == user_id)
            .options(selectinload(BusinessMember.business))
            .order_by(BusinessMember.created_at)
        )
        return list(result.scalars().all())

    async def get_membership(
        self, *, user_id: uuid.UUID, business_id: uuid.UUID
    ) -> BusinessMember | None:
        result = await self.db.execute(
            select(BusinessMember).where(
                BusinessMember.user_id == user_id,
                BusinessMember.business_id == business_id,
            )
        )
        return result.scalar_one_or_none()
