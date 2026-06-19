from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.business_member import BusinessMemberRole
from app.schemas.business import BusinessRead


class BusinessMemberRead(BaseModel):
    """User membership with nested business."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: BusinessMemberRole
    business: BusinessRead
