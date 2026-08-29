import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class UserRole(str, Enum):
    BENEFICIARY = "BENEFICIARY"
    PARTNER_USER = "PARTNER_USER"
    PARTNER_ADMIN = "PARTNER_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.BENEFICIARY.value,
        index=True
    )
    partner_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("partners.partner_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    # Relationships
    partner = relationship("Partner", back_populates="users")

    def __repr__(self) -> str:
        identifier = self.email or self.phone or self.user_id
        return f"<User user_id='{self.user_id}' identifier='{identifier}' role='{self.role}'>"
