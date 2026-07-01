"""SQLAlchemy Models — Users, Roles, Departments"""

import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Role(Base):
    """User roles: student, staff, admin"""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
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
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    __table_args__ = (
        CheckConstraint("name IN ('student', 'staff', 'admin')", name="ck_role_name"),
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Department(Base):
    """College departments"""

    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    hod_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="department", foreign_keys="User.department_id"
    )
    hod: Mapped["User | None"] = relationship(
        "User", foreign_keys=[hod_id], post_update=True
    )

    __table_args__ = (
        CheckConstraint(
            "code IN ('CSE', 'IT', 'AIDS', 'ECE', 'EEE', 'MECH')",
            name="ck_dept_code",
        ),
    )

    def __repr__(self) -> str:
        return f"<Department {self.code}>"


class User(Base):
    """Core user table — all roles share this table"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
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
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="users",
        foreign_keys=[department_id],
    )
    student_profile: Mapped["StudentProfile | None"] = relationship(
        "StudentProfile", back_populates="user", uselist=False,
        foreign_keys="StudentProfile.user_id",
    )
    staff_profile: Mapped["StaffProfile | None"] = relationship(
        "StaffProfile", back_populates="user", uselist=False,
        foreign_keys="StaffProfile.user_id",
    )
    leetcode_stats: Mapped["LeetCodeStats | None"] = relationship(
        "LeetCodeStats", back_populates="user", uselist=False
    )
    github_stats: Mapped["GitHubStats | None"] = relationship(
        "GitHubStats", back_populates="user", uselist=False
    )
    performance_score: Mapped["PerformanceScore | None"] = relationship(
        "PerformanceScore", back_populates="user", uselist=False
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    sync_logs: Mapped[list["SyncLog"]] = relationship(
        "SyncLog", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def leetcode_username(self) -> str | None:
        if self.student_profile:
            return self.student_profile.leetcode_username
        if self.staff_profile:
            return self.staff_profile.leetcode_username
        return None

    @property
    def github_username(self) -> str | None:
        if self.student_profile:
            return self.student_profile.github_username
        if self.staff_profile:
            return self.staff_profile.github_username
        return None

    @property
    def reg_no(self) -> str | None:
        if self.student_profile:
            return self.student_profile.reg_no
        return None

    @property
    def employee_id(self) -> str | None:
        if self.staff_profile:
            return self.staff_profile.employee_id
        return None

    @property
    def year(self) -> int | None:
        if self.student_profile:
            return self.student_profile.year
        return None

    @property
    def section(self) -> str | None:
        if self.student_profile:
            return self.student_profile.section
        return None

    @property
    def designation(self) -> str | None:
        if self.staff_profile:
            return self.staff_profile.designation
        return None

    def __repr__(self) -> str:
        return f"<User {self.email}>"
