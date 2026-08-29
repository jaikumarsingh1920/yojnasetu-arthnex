from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SavedScheme(Base):
    """
    User bookmark/saved scheme model.
    Enforces server-side ownership and unique (user_id, scheme_id) constraint.
    """
    __tablename__ = "saved_schemes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    scheme_id = Column(String(50), ForeignKey("schemes.scheme_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "scheme_id", name="uq_user_scheme_saved"),
        Index("idx_saved_schemes_user_created", "user_id", "created_at"),
    )

    # Relationships
    user = relationship("User", backref="saved_schemes")
    scheme = relationship("Scheme", backref="saved_by_users")
