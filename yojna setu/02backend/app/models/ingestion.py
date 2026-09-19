from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeSource(Base):
    """
    Registry for external authoritative government scheme sources.
    Tracks official URLs, authority ministry, fetch cadence, and execution status.
    """
    __tablename__ = "scheme_sources"

    source_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    scheme_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("schemes.scheme_id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="HTML", nullable=False)  # HTML, PDF, JSON_API, mixed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fetch_frequency_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    fetch_priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expected_content_type: Mapped[Optional[str]] = mapped_column(String(100), default="text/html", nullable=True)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_snapshot_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health_status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)  # HEALTHY, DEGRADED, FAILED
    retry_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def last_checked_at(self) -> Optional[datetime]:
        return self.last_fetched_at

    @last_checked_at.setter
    def last_checked_at(self, value: Optional[datetime]):
        self.last_fetched_at = value

    @property
    def failure_count(self) -> int:
        return self.consecutive_failures

    @failure_count.setter
    def failure_count(self, value: int):
        self.consecutive_failures = value

    # Relationships
    scheme = relationship("Scheme", backref="sources")
    snapshots = relationship("SourceSnapshot", back_populates="source", cascade="all, delete-orphan")
    pending_updates = relationship("PendingSchemeUpdate", back_populates="source", cascade="all, delete-orphan")
    health_logs = relationship("SourceHealthLog", back_populates="source", cascade="all, delete-orphan")


class SourceSnapshot(Base):
    """
    Immutable raw snapshot capturing exactly what content was fetched from an authoritative
    source at a given timestamp, along with deterministic SHA-256 hashing.
    """
    __tablename__ = "source_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scheme_sources.source_id", ondelete="CASCADE"), nullable=False, index=True
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    content_type: Mapped[str] = mapped_column(String(100), default="text/html", nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetch_status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, FAILED
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    source = relationship("SchemeSource", back_populates="snapshots")
    pending_updates = relationship("PendingSchemeUpdate", back_populates="snapshot")


class PendingSchemeUpdate(Base):
    """
    Change proposal representing extracted and normalized scheme modifications
    detected by the ingestion pipeline. Requires explicit administrative approval
    before modifying canonical scheme records.
    """
    __tablename__ = "pending_scheme_updates"

    update_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    scheme_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scheme_sources.source_id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("source_snapshots.snapshot_id", ondelete="SET NULL"), nullable=True, index=True
    )
    proposal_type: Mapped[str] = mapped_column(String(50), default="MODIFICATION", nullable=False)  # MODIFICATION, NEW_SCHEME, DEACTIVATION
    change_classification: Mapped[str] = mapped_column(String(50), default="MODIFIED", nullable=False)  # MODIFIED, NEW_SCHEME, POSSIBLY_WITHDRAWN
    old_version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    extracted_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of extracted fields
    detected_changes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string: list of {field, old_value, new_value}
    validation_status: Mapped[str] = mapped_column(String(50), default="VALID", nullable=False)  # VALID, NEEDS_REVIEW, INVALID
    validation_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of error strings
    governance_category: Mapped[str] = mapped_column(String(50), default="NEEDS_REVIEW", nullable=False)  # AUTO_SAFE, NEEDS_REVIEW, REJECTED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, APPROVED, REJECTED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    scheme = relationship("Scheme", backref="pending_updates")
    source = relationship("SchemeSource", back_populates="pending_updates")
    snapshot = relationship("SourceSnapshot", back_populates="pending_updates")


class IngestionRun(Base):
    """
    Ingestion Run Tracking Model.
    Provides resumability, observability, execution metrics, and checkpoint data.
    """
    __tablename__ = "ingestion_runs"

    run_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED, PAUSED
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_changed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_staged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_promoted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_needing_review: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Extended metrics for weekly monitoring telemetry
    sources_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_succeeded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unchanged_sources: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    changed_sources: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_schemes_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    modified_schemes_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deactivation_candidates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_admin_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checkpoint_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON checkpoint
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON summary

    # Relationships
    health_logs = relationship("SourceHealthLog", back_populates="run")


class SourceHealthLog(Base):
    """
    Source Health Event Log.
    Tracks HTTP failures, timeouts, changed URLs, unparseable HTML, and malformed documents per source.
    """
    __tablename__ = "source_health_logs"

    log_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("scheme_sources.source_id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("ingestion_runs.run_id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # HEALTHY, DEGRADED, FAILED
    error_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # HTTP_ERROR, TIMEOUT, CHANGED_URL, UNAVAILABLE_SOURCE, PARSING_FAILURE, MALFORMED_DOCUMENT
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    source = relationship("SchemeSource", back_populates="health_logs")
    run = relationship("IngestionRun", back_populates="health_logs")


