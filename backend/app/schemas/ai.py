"""Pydantic schemas for AI analysis endpoints"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIAnalysisResponse(BaseModel):
    """Gemini AI analysis result (matches the JSON schema from prompt)"""

    user_id: uuid.UUID
    summary: str
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str]
    recommendations: list[str] = Field(min_length=1)
    placement_analysis: str
    weekly_goal: str
    generated_at: datetime
    model_used: str = "gemini-1.5-flash"


class DepartmentAIReport(BaseModel):
    """Department-level AI analysis"""

    department_id: uuid.UUID
    department_name: str
    overall_summary: str
    top_performers: list[str]
    areas_of_concern: list[str]
    department_recommendations: list[str]
    avg_score: float
    generated_at: datetime


class AIAnalysisRequest(BaseModel):
    """Request body for triggering AI analysis"""

    force_refresh: bool = False  # Force re-generation even if recent cache exists
