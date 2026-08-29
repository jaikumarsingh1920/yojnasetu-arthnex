from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeDocument(Base):
    __tablename__ = "scheme_documents"

    document_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    scheme_id: Mapped[str] = mapped_column(String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), index=True, nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[Optional[str]] = mapped_column(Text)
    applicant_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_document: Mapped[Optional[str]] = mapped_column(Text)
    source_page: Mapped[Optional[str]] = mapped_column(String(100))
    source_section: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="documents")
