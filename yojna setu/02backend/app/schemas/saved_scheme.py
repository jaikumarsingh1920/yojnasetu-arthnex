from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.scheme import SchemeListItemResponse


class SavedSchemeResponse(BaseModel):
    id: str
    user_id: str
    scheme_id: str
    created_at: datetime
    scheme: SchemeListItemResponse

    class Config:
        from_attributes = True


class SavedSchemeStatusResponse(BaseModel):
    scheme_id: str
    is_saved: bool


class SavedSchemeListResponse(BaseModel):
    items: List[SavedSchemeResponse]
    total: int


class EmailSchemeResponse(BaseModel):
    sent: bool
    message: str
    recipient_email: Optional[str] = None
