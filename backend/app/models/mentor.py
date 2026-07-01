"""SQLAlchemy Models — Mentor Notes"""

import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MentorNote(Base):
    """Notes written by staff mentors about their mentees"""

    __tablename__ = "mentor_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    staff: Mapped["StaffProfile"] = relationship(  # noqa: F821
        "StaffProfile", back_populates="mentor_notes", foreign_keys=[staff_id]
    )
    student: Mapped["StudentProfile"] = relationship(  # noqa: F821
        "StudentProfile", back_populates="mentor_notes", foreign_keys=[student_id]
    )

    def __repr__(self) -> str:
        return f"<MentorNote staff={self.staff_id} student={self.student_id}>"
