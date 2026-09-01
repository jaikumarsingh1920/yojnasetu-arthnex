import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Partner(Base):
    __tablename__ = "partners"

    partner_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    partner_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CHANNELIZING_AGENCY"
    )
    partner_sub_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    institution_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    partner_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="AUTHORIZED_SCHEME_PARTNER",
        server_default="AUTHORIZED_SCHEME_PARTNER"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    last_verified_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    scheme_authorization_level: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    coordinates_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VERIFIED",
        server_default="VERIFIED"
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    npa_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    overdue_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    is_accepting_applications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )
    source_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UNVERIFIED",
        server_default="UNVERIFIED"
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    verified_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    source_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    source_document: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    coordinates_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    coordinates_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0"
    )
    scheme_specific_mapping_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0"
    )
    geocoding_provider: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    geocoding_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    geocoding_confidence: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    geocoded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    geocoding_query: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    geocoding_display_name: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
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
    users = relationship("User", back_populates="partner")
    assigned_applications = relationship("Application", back_populates="assigned_partner")
    scheme_mappings = relationship("PartnerSchemeMapping", back_populates="partner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Partner partner_id='{self.partner_id}' name='{self.name}' code='{self.code}'>"
