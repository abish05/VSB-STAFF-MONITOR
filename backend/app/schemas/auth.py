"""Pydantic schemas for authentication endpoints"""

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    """Schema for user registration"""

    model_config = {"str_strip_whitespace": True}

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(pattern="^(student|staff|admin)$")
    department_code: Optional[str] = Field(
        default=None,
        pattern="^(CSE|IT|AIDS|ECE|EEE|MECH)$",
    )

    # Student-specific
    reg_no: Optional[str] = Field(default=None, max_length=50)
    year: Optional[int] = Field(default=None, ge=1, le=4)
    section: Optional[str] = Field(default=None, max_length=10)

    # Staff-specific
    employee_id: Optional[str] = Field(default=None, max_length=50)
    designation: Optional[str] = Field(default=None, max_length=100)

    # Platform IDs
    leetcode_username: Optional[str] = Field(default=None, max_length=100)
    github_username: Optional[str] = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @model_validator(mode="after")
    def validate_role_fields(self) -> "RegisterRequest":
        if self.role == "student" and not self.reg_no:
            raise ValueError("reg_no is required for students")
        if self.role == "student" and not self.year:
            raise ValueError("year is required for students")
        if self.role == "staff" and not self.employee_id:
            raise ValueError("employee_id is required for staff")
        return self


class LoginRequest(BaseModel):
    """Schema for user login"""

    model_config = {"str_strip_whitespace": True}

    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=100)
    is_admin_portal: Optional[bool] = False


class TokenResponse(BaseModel):
    """JWT token pair response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request to logout and invalidate refresh token"""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Request password reset email"""

    model_config = {"str_strip_whitespace": True}

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token"""

    token: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    """Change password for authenticated user"""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)
