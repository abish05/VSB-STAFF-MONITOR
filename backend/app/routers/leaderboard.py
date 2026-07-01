"""Leaderboard Router"""

import logging
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StudentProfile
from app.models.user import Department, Role, User
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/students")
async def student_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    dept_code: Optional[str] = Query(None),
    year: Optional[int] = Query(None, ge=1, le=4),
    metric: Optional[str] = Query("overall"),  # overall, solved, commits, streak, contest, repos
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student leaderboard ranked by selected metric."""
    query = (
        select(User, PerformanceScore, LeetCodeStats, StudentProfile, GitHubStats)
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .join(User.role)
        .outerjoin(LeetCodeStats, LeetCodeStats.user_id == User.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .outerjoin(GitHubStats, GitHubStats.user_id == User.id)
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

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    if metric == "solved":
        order_col = desc(func.coalesce(LeetCodeStats.total_solved, 0))
    elif metric == "commits":
        order_col = desc(func.coalesce(GitHubStats.total_commits, 0))
    elif metric == "streak":
        order_col = desc(func.coalesce(LeetCodeStats.longest_streak, 0))
    elif metric == "contest":
        order_col = desc(func.coalesce(LeetCodeStats.contest_rating, 0.0))
    elif metric == "repos":
        order_col = desc(func.coalesce(GitHubStats.public_repos, 0))
    else:
        order_col = desc(PerformanceScore.total_score)

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(order_col).offset(offset).limit(page_size)
    )
    rows = result.fetchall()

    items = []
    for i, row in enumerate(rows):
        user, perf, lc, sp, gh = row
        items.append({
            "rank": offset + i + 1,
            "user_id": str(user.id),
            "full_name": user.full_name,
            "year": sp.year if sp else None,
            "total_score": perf.total_score,
            "leetcode_score": perf.leetcode_score,
            "github_score": perf.github_score,
            "problems_solved": lc.total_solved if lc else 0,
            "streak": lc.longest_streak if lc else 0,
            "contest_rating": lc.contest_rating if lc else 0.0,
            "commits": gh.total_commits if gh else 0,
            "repos": gh.public_repos if gh else 0,
            "classification": perf.classification,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/staff")
async def staff_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff leaderboard ranked by total score."""
    query = (
        select(User, PerformanceScore, LeetCodeStats)
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .join(Role, Role.id == User.role_id)
        .outerjoin(LeetCodeStats, LeetCodeStats.user_id == User.id)
        .where(Role.name == "staff", User.is_active == True)
    )

    count_query = (
        select(func.count(User.id))
        .join(Role, Role.id == User.role_id)
        .where(Role.name == "staff", User.is_active == True)
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(PerformanceScore.total_score)).offset(offset).limit(page_size)
    )
    rows = result.fetchall()

    items = []
    for i, row in enumerate(rows):
        user, perf, lc = row
        items.append({
            "rank": offset + i + 1,
            "user_id": str(user.id),
            "full_name": user.full_name,
            "total_score": perf.total_score,
            "problems_solved": lc.total_solved if lc else 0,
            "classification": perf.classification,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/departments")
async def department_leaderboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Department leaderboard ranked by average student score."""
    result = await db.execute(
        select(
            Department.id,
            Department.name,
            Department.code,
            func.avg(PerformanceScore.total_score).label("avg_score"),
            func.count(User.id).label("student_count"),
        )
        .join(User, User.department_id == Department.id)
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .join(User.role)
        .where(Role.name == "student")
        .group_by(Department.id, Department.name, Department.code)
        .order_by(desc("avg_score"))
    )
    rows = result.fetchall()

    items = []
    for i, row in enumerate(rows):
        items.append({
            "rank": i + 1,
            "department_id": str(row.id),
            "department_name": row.name,
            "department_code": row.code,
            "avg_score": round(float(row.avg_score or 0), 2),
            "student_count": row.student_count,
        })

    return {"items": items}
