"""Pydantic schemas for GitHub data"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GitHubStatsResponse(BaseModel):
    """GitHub statistics for a user"""

    user_id: uuid.UUID
    public_repos: int
    total_commits: int
    pull_requests: int
    issues_opened: int
    stars_received: int
    forks: int
    followers: int
    following: int
    contribution_streak: int
    longest_contribution_streak: int
    top_languages: dict[str, int]  # {"Python": 60, "JS": 30}
    last_synced: Optional[datetime]

    model_config = {"from_attributes": True}


class ContributionDataPoint(BaseModel):
    """Single day in a GitHub contribution graph"""

    date: str  # ISO "YYYY-MM-DD"
    count: int
    level: int  # 0–4


class GitHubContributionGraph(BaseModel):
    """52-week GitHub contribution graph"""

    user_id: uuid.UUID
    data: list[ContributionDataPoint]
    total_contributions: int
    longest_streak: int
    current_streak: int


class WeeklyCommits(BaseModel):
    """Weekly commit counts for bar chart"""

    week: str  # "2024-W01"
    commits: int
    pull_requests: int
    issues: int


class RepoSummary(BaseModel):
    """Summary of a single repository"""

    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int
    forks: int
    is_fork: bool
    commits_count: int
    url: str


class GitHubFullStats(BaseModel):
    """Complete GitHub data package for a user"""

    stats: GitHubStatsResponse
    contribution_graph: GitHubContributionGraph
    weekly_commits: list[WeeklyCommits]
    top_repos: list[RepoSummary]
    language_distribution: dict[str, int]
