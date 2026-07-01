"""Pydantic schemas for analytics: performance scores, placement, trends"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PerformanceScoreResponse(BaseModel):
    """User's computed performance score"""

    user_id: uuid.UUID
    leetcode_score: float
    github_score: float
    total_score: float
    placement_score: float
    classification: str
    placement_classification: str
    calculated_at: datetime

    model_config = {"from_attributes": True}


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of how the score was calculated"""

    problems_normalized: float = Field(description="0-100 score for total problems solved")
    rating_normalized: float = Field(description="0-100 score for contest rating")
    commits_normalized: float = Field(description="0-100 score for GitHub commits")
    pr_normalized: float = Field(description="0-100 score for pull requests")
    streak_normalized: float = Field(description="0-100 score for streak")
    total_score: float
    classification: str


class PlacementBreakdown(BaseModel):
    """Breakdown of placement readiness score"""

    coding_skills: float
    open_source: float
    contest_rating: float
    consistency: float
    project_quality: float
    placement_score: float
    placement_classification: str


class ScoreTrendPoint(BaseModel):
    """Single data point in a score trend over time"""

    date: str
    total_score: float
    leetcode_score: float
    github_score: float


class DepartmentStats(BaseModel):
    """Aggregated stats for a department"""

    department_id: uuid.UUID
    department_name: str
    department_code: str
    total_students: int
    active_students: int
    avg_total_score: float
    avg_leetcode_score: float
    avg_github_score: float
    avg_placement_score: float
    avg_problems_solved: float
    avg_commits: float
    top_performer: Optional[str] = None


class LeaderboardEntry(BaseModel):
    """Single entry in a leaderboard"""

    rank: int
    user_id: uuid.UUID
    full_name: str
    department_code: Optional[str] = None
    year: Optional[int] = None
    total_score: float
    leetcode_score: float
    github_score: float
    problems_solved: int
    streak: int
    classification: str


class DepartmentLeaderboardEntry(BaseModel):
    """Department leaderboard entry"""

    rank: int
    department_id: uuid.UUID
    department_name: str
    department_code: str
    avg_score: float
    total_students: int
    avg_problems_solved: float


class PaginatedLeaderboard(BaseModel):
    """Paginated leaderboard response"""

    items: list[LeaderboardEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
