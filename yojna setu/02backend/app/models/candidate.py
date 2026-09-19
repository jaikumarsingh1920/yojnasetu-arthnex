from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class CandidateScheme(Base):
    """
    Staging representation for discovered and candidate government welfare schemes.
    Isolates external discoveries from the canonical Scheme database until explicit
    human-in-the-loop review and approval.
    """
    __tablename__ = "candidate_schemes"

    candidate_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)

    # Naming & Identifiers
    discovered_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scheme_code: Mapped[str] = mapped_column(String(50), default="UNKNOWN")

    # Provenance & Source Hierarchy
    discovery_source: Mapped[str] = mapped_column(String(100), default="CENTRAL_MINISTRY", nullable=False)
    discovery_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    official_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_document: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="HTML", nullable=False)  # HTML, PDF

    # Authority & Governance Level
    ministry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    implementing_agency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    level: Mapped[str] = mapped_column(String(50), default="CENTRAL_SECTOR", nullable=False)  # CENTRAL_SECTOR, CENTRALLY_SPONSORED, STATE, UT, IMPLEMENTING_AGENCY
    state_coverage: Mapped[Optional[str]] = mapped_column(Text, default="All India")
    district_coverage: Mapped[Optional[str]] = mapped_column(Text, default="All Districts")

    # Domain & Priorities
    sector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheme_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_beneficiaries: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stated_benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relevance Classification (7 Priorities)
    relevance_status: Mapped[str] = mapped_column(String(50), default="RELEVANT", index=True, nullable=False)  # HIGH_PRIORITY, RELEVANT, LOW_PRIORITY, IRRELEVANT, NEEDS_REVIEW
    relevance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status & Audit Flags
    extraction_status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, EXTRACTED, FAILED
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", index=True, nullable=False)  # OFFICIALLY_VERIFIED, NEEDS_REVIEW, UNVERIFIED, REJECTED
    duplicate_status: Mapped[str] = mapped_column(String(50), default="UNIQUE", index=True, nullable=False)  # UNIQUE, DUPLICATE_CANDIDATE, MERGED
    duplicate_of_scheme_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_confidence: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW

    # Structured Payloads (JSON strings)
    extracted_data: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    missing_fields: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    evidence: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    # Validation
    validation_status: Mapped[str] = mapped_column(String(50), default="NEEDS_REVIEW", index=True, nullable=False)  # VALID, NEEDS_REVIEW, INVALID
    validation_errors: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Candidate Lifecycle & Administrative Governance
    candidate_status: Mapped[str] = mapped_column(String(50), default="DISCOVERED", index=True, nullable=False)  # DISCOVERED, STAGED, APPROVED, REJECTED, ARCHIVED
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_candidate_schemes_created_at", "created_at"),
        Index("ix_candidate_schemes_status_relevance", "candidate_status", "relevance_status"),
    )
