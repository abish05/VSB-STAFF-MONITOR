"""SQLAlchemy Models — Sync Logs"""

import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class SyncLog(Base):
    """Tracks every LeetCode/GitHub sync attempt per user"""

    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "leetcode" | "github"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "success" | "failed" | "partial"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sync_logs")  # noqa: F821

    __table_args__ = (
        CheckConstraint(
            "platform IN ('leetcode', 'github')", name="ck_sync_platform"
        ),
        CheckConstraint(
            "status IN ('success', 'failed', 'partial')", name="ck_sync_status"
        ),
    )

    def __repr__(self) -> str:
        return f"<SyncLog user={self.user_id} platform={self.platform} status={self.status}>"
