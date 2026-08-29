from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeRule(Base):
    __tablename__ = "scheme_rules"

    rule_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    scheme_id: Mapped[str] = mapped_column(String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), index=True, nullable=False)
    parent_product_id: Mapped[Optional[str]] = mapped_column(String(50), default="NOT_APPLICABLE")
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="HIGH")
    condition_group: Mapped[str] = mapped_column(String(100), nullable=False, default="BASE")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    source_document: Mapped[Optional[str]] = mapped_column(Text)
    source_page: Mapped[Optional[str]] = mapped_column(String(100))
    source_section: Mapped[Optional[str]] = mapped_column(String(255))
    effective_from: Mapped[Optional[str]] = mapped_column(String(50))
    effective_to: Mapped[Optional[str]] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="rules")
