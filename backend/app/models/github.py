"""SQLAlchemy Models — GitHub Stats and Activity"""

import uuid
from datetime import date, datetime

from app.database import Base
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GitHubStats(Base):
    """Current GitHub statistics per user (latest snapshot)"""

    __tablename__ = "github_stats"

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
    public_repos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_commits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pull_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues_opened: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stars_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    followers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    following: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contribution_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_contribution_streak: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    # Top languages as JSON (e.g. {"Python": 60, "JavaScript": 30})
    top_languages: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Contribution calendar as JSON (date -> count)
    contribution_calendar: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="github_stats")  # noqa: F821
    activity: Mapped[list["GitHubActivity"]] = relationship(
        "GitHubActivity", back_populates="stats", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GitHubStats user={self.user_id} commits={self.total_commits}>"


class GitHubActivity(Base):
    """Daily GitHub activity snapshots for trend analysis"""

    __tablename__ = "github_activity"

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
        ForeignKey("github_stats.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    commits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pull_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    stats: Mapped["GitHubStats"] = relationship("GitHubStats", back_populates="activity")

    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_gh_activity_user_date"),
    )

    def __repr__(self) -> str:
        return f"<GitHubActivity user={self.user_id} date={self.activity_date}>"
