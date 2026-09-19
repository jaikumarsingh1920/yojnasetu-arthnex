import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InstitutionEntity(Base):
    """
    Authoritative canonical registry for statutory financial and implementing institutions.
    Separates legal banking/agency entities from local branch or partner points of presence.
    """
    __tablename__ = "institution_entities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    canonical_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    institution_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    rbi_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    nabard_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    sponsor_bank: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    headquarters_state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    headquarters_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    official_website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1"
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
    aliases = relationship("InstitutionAlias", back_populates="institution", cascade="all, delete-orphan")
    observations = relationship("PartnerFinancialObservation", back_populates="institution")

    def __repr__(self) -> str:
        return f"<InstitutionEntity id='{self.id}' canonical_name='{self.canonical_name}'>"


class InstitutionAlias(Base):
    """
    Mapping table for historical names, pre-merger constituent names, and acronyms.
    Handles RRB amalgamation lineage (e.g. Baroda UP Bank -> Uttar Pradesh Gramin Bank).
    """
    __tablename__ = "institution_aliases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    institution_entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institution_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    alias_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    normalized_alias: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    alias_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="HISTORICAL_NAME"
    )
    source_authority: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    confidence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="HIGH"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    institution = relationship("InstitutionEntity", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<InstitutionAlias alias='{self.alias_name}' -> institution='{self.institution_entity_id}'>"


class PartnerFinancialObservation(Base):
    """
    Multi-dimensional, evidence-backed financial observation with full provenance.
    Strictly forbids pseudo-aggregate scores and stores statutory observations individually.
    """
    __tablename__ = "partner_financial_observations"

    id: Mapped[str] = mapped_column(
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
    institution_entity_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("institution_entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    metric_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    metric_status_value: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    metric_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PERCENT"
    )
    source_authority: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )
    source_document: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    source_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    period_start: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    period_end: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    data_as_of: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    publication_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VERIFIED_OFFICIAL",
        server_default="VERIFIED_OFFICIAL"
    )
    match_confidence: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="EXACT"
    )
    financial_scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="INSTITUTION_LEVEL",
        server_default="INSTITUTION_LEVEL",
        index=True
    )
    raw_snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        index=True
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
    partner = relationship("Partner", backref="financial_observations")
    institution = relationship("InstitutionEntity", back_populates="observations")

    def __repr__(self) -> str:
        return f"<FinancialObservation partner='{self.partner_id}' metric='{self.metric_name}' value='{self.metric_value or self.metric_status_value}'>"


class PrudentialRule(Base):
    """
    Versioned machine-readable prudential rules grounded in official NSFDC guidelines.
    """
    __tablename__ = "prudential_rules"

    rule_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    institution_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    applicable_institution_types: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="ALL",
        server_default="ALL"
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    operator: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    threshold_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    threshold_status: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    authority: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="NSFDC"
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )
    source_document: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    source_section: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    wording: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CRITICAL_EXCLUSION"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1"
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

    def __repr__(self) -> str:
        return f"<PrudentialRule id='{self.rule_id}' metric='{self.metric_name}' op='{self.operator}' threshold='{self.threshold_value or self.threshold_status}'>"
