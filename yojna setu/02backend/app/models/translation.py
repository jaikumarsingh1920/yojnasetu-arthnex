import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeTranslation(Base):
    """
    Persistent translation cache for government scheme dynamic content.
    Guarantees deterministic, content-hashed localization with provider provenance.
    If the canonical scheme source text changes, source_hash differs, ensuring
    stale translations are never returned.
    """
    __tablename__ = "scheme_translations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("schemes.scheme_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    scheme = relationship("Scheme", back_populates="translations")

    __table_args__ = (
        Index("ix_scheme_translations_lookup", "scheme_id", "language_code", "field_name", "source_hash"),
        Index("ix_scheme_translations_scheme_lang", "scheme_id", "language_code"),
    )
