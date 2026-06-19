from datetime import datetime

from pydantic import BaseModel


class TimestampRead(BaseModel):
    """Timestamp fields for read schemas that need audit metadata."""

    created_at: datetime
    updated_at: datetime
