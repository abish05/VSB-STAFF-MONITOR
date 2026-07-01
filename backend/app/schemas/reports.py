"""Pydantic schemas for report generation and download"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request to generate a report"""

    report_type: str  # "pdf" | "excel"
    scope: str = "user"  # "user" | "department" | "all"
    department_id: Optional[uuid.UUID] = None


class ReportResponse(BaseModel):
    """Response after report generation"""

    id: uuid.UUID
    report_type: str
    scope: str
    file_name: str
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedReports(BaseModel):
    """Paginated list of generated reports"""

    items: list[ReportResponse]
    total: int
    page: int
    page_size: int


class NotificationResponse(BaseModel):
    """In-app notification"""

    id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    """Paginated notifications list"""

    items: list[NotificationResponse]
    total: int
    unread_count: int


class AchievementResponse(BaseModel):
    """Achievement definition + unlock status"""

    id: uuid.UUID
    code: str
    name: str
    description: str
    icon: str
    points: int
    is_unlocked: bool
    awarded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MentorNoteCreate(BaseModel):
    """Create a mentor note"""

    note: str = Field(min_length=1, max_length=5000)


class MentorNoteResponse(BaseModel):
    """Mentor note response"""

    id: uuid.UUID
    staff_id: uuid.UUID
    student_id: uuid.UUID
    note: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
