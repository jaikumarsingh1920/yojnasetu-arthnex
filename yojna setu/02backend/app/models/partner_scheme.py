import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PartnerSchemeMapping(Base):
    __tablename__ = "partner_scheme_mappings"

    mapping_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    partner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("partners.partner_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scheme_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("schemes.scheme_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    authorized_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    authorization_level: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="SCHEME_ROUTE_VERIFIED"
    )
    last_verified_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VERIFIED_OFFICIAL",
        server_default="VERIFIED_OFFICIAL"
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    source_document: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    partner = relationship("Partner", back_populates="scheme_mappings")
    scheme = relationship("Scheme", back_populates="partner_mappings")

    __table_args__ = (
        UniqueConstraint("partner_id", "scheme_id", name="uq_partner_scheme"),
    )

    def __repr__(self) -> str:
        return f"<PartnerSchemeMapping partner_id='{self.partner_id}' scheme_id='{self.scheme_id}'>"
