"""Analytics Router — performance scores, leaderboards, department stats"""

import logging
import uuid
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user, require_admin
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StudentProfile
from app.models.user import Department, User
from app.schemas.analytics import (
    LeaderboardEntry,
    PaginatedLeaderboard,
    PerformanceScoreResponse,
)
from app.services.scoring_service import (
    GitHubInput,
    LeetCodeInput,
    calculate_performance_score,
    calculate_placement_score,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/score/{user_id}", response_model=PerformanceScoreResponse)
async def get_user_score(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get computed performance score for a user."""
    # Students can only view their own score; staff/admin can view any
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == user_id)
    )
    perf = result.scalar_one_or_none()

    if not perf:
        raise HTTPException(status_code=404, detail="Score not yet calculated. Trigger a sync first.")

    return perf


@router.post("/score/{user_id}/recalculate")
async def recalculate_score(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Recalculate performance score for a user (admin only)."""
    from datetime import datetime, timezone

    lc_result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == user_id)
    )
    lc = lc_result.scalar_one_or_none()

    gh_result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == user_id)
    )
    gh = gh_result.scalar_one_or_none()

    if not lc and not gh:
        raise HTTPException(status_code=422, detail="No LeetCode or GitHub data available for this user")

    lc_input = LeetCodeInput(
        total_solved=lc.total_solved if lc else 0,
        easy_solved=lc.easy_solved if lc else 0,
        medium_solved=lc.medium_solved if lc else 0,
        hard_solved=lc.hard_solved if lc else 0,
        contest_rating=lc.contest_rating if lc else 0,
        current_streak=lc.current_streak if lc else 0,
    )
    gh_input = GitHubInput(
        total_commits=gh.total_commits if gh else 0,
        pull_requests=gh.pull_requests if gh else 0,
        public_repos=gh.public_repos if gh else 0,
        stars_received=gh.stars_received if gh else 0,
        contribution_streak=gh.contribution_streak if gh else 0,
        issues_opened=gh.issues_opened if gh else 0,
    )

    lc_score, gh_score, total_score, classification = calculate_performance_score(lc_input, gh_input)
    placement_score, placement_class = calculate_placement_score(lc_input, gh_input)

    # Upsert performance score
    perf_result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == user_id)
    )
    perf = perf_result.scalar_one_or_none()

    if perf:
        perf.leetcode_score = lc_score
        perf.github_score = gh_score
        perf.total_score = total_score
        perf.placement_score = placement_score
        perf.classification = classification
        perf.placement_classification = placement_class
        perf.calculated_at = datetime.now(tz=timezone.utc)
    else:
        perf = PerformanceScore(
            user_id=user_id,
            leetcode_score=lc_score,
            github_score=gh_score,
            total_score=total_score,
            placement_score=placement_score,
            classification=classification,
            placement_classification=placement_class,
            calculated_at=datetime.now(tz=timezone.utc),
        )
        db.add(perf)

    await db.commit()
    return {
        "message": "Score recalculated",
        "total_score": total_score,
        "classification": classification,
        "placement_score": placement_score,
        "placement_classification": placement_class,
    }


@router.get("/leaderboard/students", response_model=PaginatedLeaderboard)
async def student_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    dept_code: Optional[str] = Query(None),
    year: Optional[int] = Query(None, ge=1, le=4),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student leaderboard ranked by total score."""
    from app.models.user import Role

    query = (
        select(
            User,
            PerformanceScore,
            LeetCodeStats,
            StudentProfile,
            Department.code.label("dept_code"),
        )
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .join(User.role)
        .outerjoin(LeetCodeStats, LeetCodeStats.user_id == User.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .outerjoin(Department, Department.id == User.department_id)
        .where(Role.name == "student", User.is_active == True)  # noqa
    )

    # Lightweight count query
    count_query = (
        select(func.count(User.id))
        .join(Role, Role.id == User.role_id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .outerjoin(Department, Department.id == User.department_id)
        .where(Role.name == "student", User.is_active == True)
    )

    if dept_code:
        query = query.where(Department.code == dept_code)
        count_query = count_query.where(Department.code == dept_code)
    if year:
        query = query.where(StudentProfile.year == year)
        count_query = count_query.where(StudentProfile.year == year)

    # Count total
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(PerformanceScore.total_score)).offset(offset).limit(page_size)
    )
    rows = result.fetchall()

    items = []
    for i, row in enumerate(rows):
        user, perf, lc, sp, dcode = row
        items.append(LeaderboardEntry(
            rank=offset + i + 1,
            user_id=user.id,
            full_name=user.full_name,
            department_code=dcode,
            year=sp.year if sp else None,
            total_score=perf.total_score,
            leetcode_score=perf.leetcode_score,
            github_score=perf.github_score,
            problems_solved=lc.total_solved if lc else 0,
            streak=lc.current_streak if lc else 0,
            classification=perf.classification,
        ))

    return PaginatedLeaderboard(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
