from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeFAQ(Base):
    """
    Grounded Frequently Asked Questions (FAQ) repository derived from authoritative official sources.
    Provides direct, high-relevance conversational answers for citizen queries across all key dimensions:
    eligibility, loan/grant quantum, subsidy availability, required documents, application process, and tenure.
    """
    __tablename__ = "scheme_faqs"

    faq_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    scheme_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)  # ELIGIBILITY, FINANCIAL, APPLICATION, DOCUMENTS, BENEFITS, GENERAL
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    scheme = relationship("Scheme", back_populates="faqs")

    __table_args__ = (
        Index("ix_scheme_faqs_scheme_category", "scheme_id", "category"),
    )


class SchemeKnowledgeProfile(Base):
    """
    Comprehensive structured knowledge representation and quality assessment profile for each scheme.
    Synthesizes identity, purpose, beneficiaries, granular eligibility, distinct financials,
    application journey, geographic scope, exclusions, and multi-dimensional quality metrics.
    """
    __tablename__ = "scheme_knowledge_profiles"

    profile_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    scheme_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    aliases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of abbreviations / alternate names
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    problem_addressed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intended_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geographic_level: Mapped[str] = mapped_column(String(50), default="NATIONAL", nullable=False)  # NATIONAL, STATE, UT, REGION, DISTRICT
    applicant_category_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    financial_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exclusions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_stages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of stages
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 to 100
    quality_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON breakdown
    source_provenance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON metadata
    enriched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    scheme = relationship("Scheme", back_populates="knowledge_profile")
