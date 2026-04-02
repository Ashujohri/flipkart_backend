from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    type: str
    channel: str
    title: str
    body: str
    data: Optional[Any] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int
    pages: int


class MarkReadRequest(BaseModel):
    notification_ids: Optional[List[str]] = None