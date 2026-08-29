from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    notification_id: str
    recipient_user_id: str
    application_id: Optional[str] = None
    notification_type: str
    title: str
    message: str
    priority: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    metadata_json: Optional[str] = None
    channel: str
    delivery_status: str

    class Config:
        from_attributes = True


class PaginatedNotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    in_app_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool
    push_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdateRequest(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
