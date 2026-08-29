import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: f"NOTIF-{uuid.uuid4().hex[:12].upper()}"
    )
    recipient_user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    application_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("applications.application_id", ondelete="SET NULL"), index=True, nullable=True
    )
    notification_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(String(20), default="IN_APP", nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(20), default="DELIVERED", nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_user_id])
    application = relationship("Application", foreign_keys=[application_id])
