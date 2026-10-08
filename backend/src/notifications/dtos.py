from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=5000)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None
