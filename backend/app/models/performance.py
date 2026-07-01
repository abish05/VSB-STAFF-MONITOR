"""SQLAlchemy Models — Performance Scores"""

import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PerformanceScore(Base):
    """Computed performance and placement scores per user"""

    __tablename__ = "performance_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Sub-scores (0–100)
    leetcode_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    github_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    placement_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Classification strings
    classification: Mapped[str] = mapped_column(
        String(50), default="Needs Improvement", nullable=False
    )
    placement_classification: Mapped[str] = mapped_column(
        String(50), default="Needs Improvement", nullable=False
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="performance_score")  # noqa: F821

    __table_args__ = (
        CheckConstraint("total_score >= 0 AND total_score <= 100", name="ck_total_score_range"),
        CheckConstraint("placement_score >= 0 AND placement_score <= 100", name="ck_placement_score_range"),
    )

    def __repr__(self) -> str:
        return f"<PerformanceScore user={self.user_id} score={self.total_score}>"
