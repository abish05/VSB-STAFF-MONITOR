"""SQLAlchemy Models — StudentProfile and StaffProfile"""

import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class StudentProfile(Base):
    """Extended profile for students"""

    __tablename__ = "student_profiles"

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
    reg_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=True)
    leetcode_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mentor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="student_profile", foreign_keys=[user_id]
    )
    mentor: Mapped["StaffProfile | None"] = relationship(
        "StaffProfile",
        back_populates="mentees",
        foreign_keys=[mentor_id],
    )
    mentor_notes: Mapped[list["MentorNote"]] = relationship(  # noqa: F821
        "MentorNote", back_populates="student", cascade="all, delete-orphan",
        foreign_keys="MentorNote.student_id",
    )

    __table_args__ = (
        CheckConstraint("year IN (1, 2, 3, 4)", name="ck_student_year"),
    )

    def __repr__(self) -> str:
        return f"<StudentProfile {self.reg_no}>"


class StaffProfile(Base):
    """Extended profile for staff members"""

    __tablename__ = "staff_profiles"

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
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    designation: Mapped[str] = mapped_column(String(100), nullable=True)
    leetcode_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
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
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="staff_profile", foreign_keys=[user_id]
    )
    mentees: Mapped[list["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="mentor",
        foreign_keys="StudentProfile.mentor_id",
    )
    mentor_notes: Mapped[list["MentorNote"]] = relationship(  # noqa: F821
        "MentorNote", back_populates="staff", cascade="all, delete-orphan",
        foreign_keys="MentorNote.staff_id",
    )

    def __repr__(self) -> str:
        return f"<StaffProfile {self.employee_id}>"
