from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class SchemeVerification(Base):
    __tablename__ = "scheme_verifications"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    scheme_id: Mapped[str] = mapped_column(String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), index=True, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED", index=True, nullable=False)
    last_verified_date: Mapped[Optional[str]] = mapped_column(String(50))
    data_confidence: Mapped[str] = mapped_column(String(20), default="HIGH")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    normalization_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="verifications")
