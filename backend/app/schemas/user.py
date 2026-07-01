"""Pydantic schemas for user endpoints"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str

    model_config = {"from_attributes": True}


from app.schemas.github import GitHubStatsResponse
from app.schemas.leetcode import LeetCodeStatsResponse


class UserResponse(BaseModel):
    """Full user profile response"""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: RoleResponse
    department: Optional[DepartmentResponse] = None
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    leetcode_stats: Optional[LeetCodeStatsResponse] = None
    github_stats: Optional[GitHubStatsResponse] = None
    leetcode_username: Optional[str] = None
    github_username: Optional[str] = None
    reg_no: Optional[str] = None
    employee_id: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    designation: Optional[str] = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Fields a user can update in their own profile"""

    model_config = {"str_strip_whitespace": True}

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UpdateLeetCodeUsername(BaseModel):
    model_config = {"str_strip_whitespace": True}

    leetcode_username: str = Field(min_length=3, max_length=100)


class UpdateGitHubUsername(BaseModel):
    model_config = {"str_strip_whitespace": True}

    github_username: str = Field(min_length=1, max_length=100)


class AdminUserUpdate(BaseModel):
    """Fields only an admin can update"""

    model_config = {"str_strip_whitespace": True}

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    role_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class AdminCreateUser(BaseModel):
    """Admin creates a user with full details"""

    model_config = {"str_strip_whitespace": True}

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(pattern="^(student|staff|admin)$")
    department_code: Optional[str] = None
    reg_no: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1, le=4)
    section: Optional[str] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    leetcode_username: Optional[str] = None
    github_username: Optional[str] = None


class PaginatedUsers(BaseModel):
    """Paginated user list response"""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
