"""Pydantic schemas for LeetCode data"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LeetCodeStatsResponse(BaseModel):
    """LeetCode statistics for a user"""

    user_id: uuid.UUID
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    acceptance_rate: float
    contest_rating: float
    contest_global_rank: int
    contests_attended: int
    current_streak: int
    longest_streak: int
    reputation: int
    last_synced: Optional[datetime]

    model_config = {"from_attributes": True}


class HeatmapDataPoint(BaseModel):
    """Single day in a submission heatmap"""

    date: str  # ISO format "YYYY-MM-DD"
    count: int
    level: int  # 0–4 for color intensity


class LeetCodeHeatmapResponse(BaseModel):
    """52-week submission heatmap"""

    user_id: uuid.UUID
    data: list[HeatmapDataPoint]
    total_active_days: int
    max_daily_submissions: int


class MonthlyProgress(BaseModel):
    """Monthly problems solved for trend chart"""

    month: str  # "2024-01"
    problems_solved: int
    cumulative_total: int


class ContestHistory(BaseModel):
    """Single contest performance record"""

    contest_name: str
    rating: float
    rating_change: float
    rank: int
    finished_at: Optional[str]


class LeetCodeFullStats(BaseModel):
    """Complete LeetCode data package for a user"""

    stats: LeetCodeStatsResponse
    heatmap: LeetCodeHeatmapResponse
    monthly_progress: list[MonthlyProgress]
    difficulty_distribution: dict[str, int]  # {"easy": 50, "medium": 30, "hard": 10}


class SyncRequest(BaseModel):
    """Manual sync trigger request"""

    platform: str  # "leetcode" | "github" | "all"


class SyncStatusResponse(BaseModel):
    """Sync operation status"""

    platform: str
    status: str
    last_synced: Optional[datetime]
    error_message: Optional[str] = None
