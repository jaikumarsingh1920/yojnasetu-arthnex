import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PartnerChangelog(Base):
    __tablename__ = "partner_changelogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("partners.partner_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), default="UPDATE", index=True)
    field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_identifier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    partner = relationship("Partner", backref="changelogs")
