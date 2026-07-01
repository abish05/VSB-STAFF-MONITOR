"""SQLAlchemy Models — LeetCode Stats and History"""

import uuid
from datetime import date, datetime

from app.database import Base
from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class LeetCodeStats(Base):
    """Current LeetCode statistics per user (latest snapshot)"""

    __tablename__ = "leetcode_stats"

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
    total_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    easy_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hard_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contest_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    contest_global_rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contests_attended: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reputation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Submission calendar as JSON string (date -> count)
    submission_calendar: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    user: Mapped["User"] = relationship("User", back_populates="leetcode_stats")  # noqa: F821
    history: Mapped[list["LeetCodeHistory"]] = relationship(
        "LeetCodeHistory", back_populates="stats", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LeetCodeStats user={self.user_id} solved={self.total_solved}>"


class LeetCodeHistory(Base):
    """Daily LeetCode snapshots for trend analysis"""

    __tablename__ = "leetcode_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stats_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leetcode_stats.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_change: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_solved_at_date: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    stats: Mapped["LeetCodeStats"] = relationship(
        "LeetCodeStats", back_populates="history"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_lc_history_user_date"),
    )

    def __repr__(self) -> str:
        return f"<LeetCodeHistory user={self.user_id} date={self.snapshot_date}>"
