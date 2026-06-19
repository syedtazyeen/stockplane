from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BusinessRead(BaseModel):
    """Business data returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
