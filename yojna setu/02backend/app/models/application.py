import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class ApplicationStatus(str, Enum):
    DRAFT = "DRAFT"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    READY_FOR_SUBMISSION = "READY_FOR_SUBMISSION"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    COMPLETED = "COMPLETED"


class DocumentVerificationStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    NEEDS_CORRECTION = "NEEDS_CORRECTION"


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scheme_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("schemes.scheme_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ApplicationStatus.DRAFT.value,
        index=True
    )
    assigned_partner_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("partners.partner_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assigned_reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    profile_snapshot: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string snapshot of beneficiary profile at application/submission time"
    )
    eligibility_snapshot: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string snapshot of eligibility evaluation result"
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correction_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
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
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="applications")
    scheme = relationship("Scheme", backref="applications")
    assigned_partner = relationship("Partner", back_populates="assigned_applications")
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    documents = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    status_history = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")
    review_notes = relationship("ApplicationReviewNote", back_populates="application", cascade="all, delete-orphan")


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    app_document_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("scheme_documents.document_id", ondelete="SET NULL"),
        nullable=True
    )
    document_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="REQUIRED"
    )
    condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_uploaded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DocumentVerificationStatus.PENDING.value
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    application = relationship("Application", back_populates="documents")
    master_document = relationship("SchemeDocument")
    verifier = relationship("User", foreign_keys=[verified_by])


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    history_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    application = relationship("Application", back_populates="status_history")
    user = relationship("User")


class ApplicationReviewNote(Base):
    __tablename__ = "application_review_notes"

    note_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    author_role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    application = relationship("Application", back_populates="review_notes")
    author = relationship("User")
