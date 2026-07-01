"""AI Router — Gemini AI analysis endpoints"""

import logging
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user, require_admin
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StudentProfile
from app.models.user import Department, User
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from app.services.ai_service import ai_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_user_data_for_ai(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """Load all necessary data for AI analysis."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    lc_result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == user_id)
    )
    lc = lc_result.scalar_one_or_none()

    gh_result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == user_id)
    )
    gh = gh_result.scalar_one_or_none()

    perf_result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == user_id)
    )
    perf = perf_result.scalar_one_or_none()

    dept_name = "N/A"
    if user.department_id:
        dept_result = await db.execute(
            select(Department).where(Department.id == user.department_id)
        )
        dept = dept_result.scalar_one_or_none()
        if dept:
            dept_name = dept.code

    return {
        "user": user,
        "profile": profile,
        "lc": lc,
        "gh": gh,
        "perf": perf,
        "dept_name": dept_name,
    }


@router.post("/analyze/{user_id}", response_model=AIAnalysisResponse)
async def analyze_user(
    user_id: uuid.UUID,
    request: AIAnalysisRequest = AIAnalysisRequest(),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Gemini AI analysis for a user.
    Students can only analyze themselves; staff/admin can analyze any user.
    """
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = await _get_user_data_for_ai(db, user_id)
    lc = data["lc"]
    gh = data["gh"]
    perf = data["perf"]

    if not lc and not gh:
        raise HTTPException(
            status_code=422,
            detail="No LeetCode or GitHub data available. Add usernames and trigger a sync first.",
        )

    try:
        analysis = await ai_service.analyze_user(
            name=data["user"].full_name,
            dept=data["dept_name"],
            year=data["profile"].year if data["profile"] else 1,
            leetcode_stats={
                "total_solved": lc.total_solved if lc else 0,
                "easy_solved": lc.easy_solved if lc else 0,
                "medium_solved": lc.medium_solved if lc else 0,
                "hard_solved": lc.hard_solved if lc else 0,
                "contest_rating": lc.contest_rating if lc else 0,
                "current_streak": lc.current_streak if lc else 0,
            },
            github_stats={
                "total_commits": gh.total_commits if gh else 0,
                "pull_requests": gh.pull_requests if gh else 0,
                "public_repos": gh.public_repos if gh else 0,
                "contribution_streak": gh.contribution_streak if gh else 0,
            },
            perf_score=perf.total_score if perf else 0,
            classification=perf.classification if perf else "Needs Improvement",
            placement_score=perf.placement_score if perf else 0,
            placement_class=perf.placement_classification if perf else "Needs Improvement",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return AIAnalysisResponse(
        user_id=user_id,
        generated_at=datetime.now(tz=timezone.utc),
        **analysis,
    )


@router.post("/department-summary/{dept_id}")
async def department_ai_summary(
    dept_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI summary for a department (admin only)."""
    dept_result = await db.execute(
        select(Department).where(Department.id == dept_id)
    )
    dept = dept_result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    from app.models.user import Role
    from sqlalchemy import func

    # Get stats
    avg_result = await db.execute(
        select(func.avg(PerformanceScore.total_score))
        .join(User, User.id == PerformanceScore.user_id)
        .where(User.department_id == dept_id)
    )
    avg_score = float(avg_result.scalar() or 0)

    count_result = await db.execute(
        select(func.count(User.id))
        .join(User.role)
        .where(User.department_id == dept_id, Role.name == "student")
    )
    student_count = count_result.scalar() or 0

    # Top performers
    top_result = await db.execute(
        select(User.full_name)
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .where(User.department_id == dept_id)
        .order_by(PerformanceScore.total_score.desc())
        .limit(5)
    )
    top_performers = [row[0] for row in top_result.fetchall()]

    try:
        analysis = await ai_service.analyze_department(
            dept_name=dept.name,
            avg_score=avg_score,
            top_performers=top_performers,
            student_count=student_count,
            active_count=student_count,  # Simplified
            avg_problems=0,
            avg_commits=0,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI analysis failed: {exc}")

    return {
        "department_id": str(dept_id),
        "department_name": dept.name,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        **analysis,
    }


@router.post("/global-report")
async def global_ai_summary(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate global AI summary across all users (admin only)."""
    from app.models.user import Role
    from sqlalchemy import func

    # Get overall stats
    avg_result = await db.execute(
        select(func.avg(PerformanceScore.total_score))
        .join(User, User.id == PerformanceScore.user_id)
    )
    avg_score = float(avg_result.scalar() or 0)

    count_result = await db.execute(
        select(func.count(User.id))
        .join(User.role)
        .where(Role.name == "student")
    )
    student_count = count_result.scalar() or 0

    # Total LeetCode and GitHub counts
    lc_sum = await db.execute(select(func.sum(LeetCodeStats.total_solved)))
    total_problems = int(lc_sum.scalar() or 0)

    gh_sum = await db.execute(select(func.sum(GitHubStats.total_commits)))
    total_commits = int(gh_sum.scalar() or 0)

    avg_problems = total_problems / student_count if student_count > 0 else 0
    avg_commits = total_commits / student_count if student_count > 0 else 0

    # Top performers
    top_result = await db.execute(
        select(User.full_name)
        .join(PerformanceScore, PerformanceScore.user_id == User.id)
        .order_by(PerformanceScore.total_score.desc())
        .limit(10)
    )
    top_performers = [row[0] for row in top_result.fetchall()]

    try:
        analysis = await ai_service.analyze_global(
            total_students=student_count,
            avg_score=avg_score,
            top_performers=top_performers,
            avg_problems=avg_problems,
            avg_commits=avg_commits,
            total_problems_solved=total_problems,
            total_github_commits=total_commits,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Global AI analysis failed: {exc}")

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        **analysis,
    }
