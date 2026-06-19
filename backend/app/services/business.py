import uuid

from app.models.business import Business
from app.models.business_member import BusinessMember, BusinessMemberRole
from app.repositories.business import BusinessRepository
from app.repositories.business_member import BusinessMemberRepository


class BusinessService:
    """Business and membership workflows."""

    def __init__(
        self,
        business_repository: BusinessRepository,
        business_member_repository: BusinessMemberRepository,
    ) -> None:
        self.business_repository = business_repository
        self.business_member_repository = business_member_repository

    @property
    def db(self):
        return self.business_repository.db

    async def create_business_for_owner(
        self, *, user_id: uuid.UUID, name: str
    ) -> BusinessMember:
        business = Business(name=name)
        await self.business_repository.create(obj=business)

        membership = BusinessMember(
            user_id=user_id,
            business_id=business.id,
            role=BusinessMemberRole.OWNER,
        )
        await self.business_member_repository.create(obj=membership)
        membership.business = business

        await self.db.flush()
        return membership

    async def get_memberships_for_user(
        self, user_id: uuid.UUID
    ) -> list[BusinessMember]:
        return await self.business_member_repository.get_memberships_for_user(user_id)
