"""Student Router — student-specific dashboard and data endpoints"""

import logging

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, require_staff_or_student
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StudentProfile
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def student_dashboard(
    current_user: CurrentUser = Depends(require_staff_or_student),
    db: AsyncSession = Depends(get_db),
):
    """Student personal dashboard with all stats."""
    user_id = current_user.id

    # Load profile
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Load LeetCode stats
    lc_result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == user_id)
    )
    lc_stats = lc_result.scalar_one_or_none()

    # Load GitHub stats
    gh_result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == user_id)
    )
    gh_stats = gh_result.scalar_one_or_none()

    # Load performance score
    perf_result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == user_id)
    )
    perf = perf_result.scalar_one_or_none()

    return {
        "user_id": str(user_id),
        "profile": {
            "reg_no": profile.reg_no if profile else None,
            "year": profile.year if profile else None,
            "section": profile.section if profile else None,
            "leetcode_username": profile.leetcode_username if profile else None,
            "github_username": profile.github_username if profile else None,
        },
        "leetcode": {
            "total_solved": lc_stats.total_solved if lc_stats else 0,
            "easy": lc_stats.easy_solved if lc_stats else 0,
            "medium": lc_stats.medium_solved if lc_stats else 0,
            "hard": lc_stats.hard_solved if lc_stats else 0,
            "contest_rating": lc_stats.contest_rating if lc_stats else 0,
            "current_streak": lc_stats.current_streak if lc_stats else 0,
            "longest_streak": lc_stats.longest_streak if lc_stats else 0,
            "has_data": lc_stats is not None,
        },
        "github": {
            "total_commits": gh_stats.total_commits if gh_stats else 0,
            "pull_requests": gh_stats.pull_requests if gh_stats else 0,
            "public_repos": gh_stats.public_repos if gh_stats else 0,
            "stars_received": gh_stats.stars_received if gh_stats else 0,
            "contribution_streak": gh_stats.contribution_streak if gh_stats else 0,
            "has_data": gh_stats is not None,
        },
        "performance": {
            "total_score": perf.total_score if perf else 0,
            "leetcode_score": perf.leetcode_score if perf else 0,
            "github_score": perf.github_score if perf else 0,
            "placement_score": perf.placement_score if perf else 0,
            "classification": perf.classification if perf else "Needs Improvement",
            "placement_classification": perf.placement_classification if perf else "Needs Improvement",
        },
    }


@router.get("/leetcode")
async def get_student_leetcode(
    current_user: CurrentUser = Depends(require_staff_or_student),
    db: AsyncSession = Depends(get_db),
):
    """Get LeetCode stats + heatmap data for the authenticated student."""
    from app.utils.helpers import parse_submission_calendar

    lc_result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == current_user.id)
    )
    lc = lc_result.scalar_one_or_none()

    if not lc:
        return {"has_data": False, "message": "Add your LeetCode username to start tracking"}

    # Parse submission calendar for heatmap
    calendar_raw = lc.submission_calendar or "{}"
    calendar = parse_submission_calendar(calendar_raw)

    # Build heatmap data (last 365 days)
    from datetime import date, timedelta
    heatmap = []
    today = date.today()
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        count = calendar.get(d.isoformat(), 0)
        level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 4 else 3 if count <= 6 else 4
        heatmap.append({"date": d.isoformat(), "count": count, "level": level})

    return {
        "has_data": True,
        "stats": {
            "total_solved": lc.total_solved,
            "easy_solved": lc.easy_solved,
            "medium_solved": lc.medium_solved,
            "hard_solved": lc.hard_solved,
            "contest_rating": lc.contest_rating,
            "contest_global_rank": lc.contest_global_rank,
            "contests_attended": lc.contests_attended,
            "current_streak": lc.current_streak,
            "longest_streak": lc.longest_streak,
            "acceptance_rate": lc.acceptance_rate,
            "last_synced": lc.last_synced.isoformat() if lc.last_synced else None,
        },
        "heatmap": heatmap,
        "difficulty_distribution": {
            "Easy": lc.easy_solved,
            "Medium": lc.medium_solved,
            "Hard": lc.hard_solved,
        },
    }


@router.get("/github")
async def get_student_github(
    current_user: CurrentUser = Depends(require_staff_or_student),
    db: AsyncSession = Depends(get_db),
):
    """Get GitHub stats + contribution graph for the authenticated student."""
    import json
    from datetime import date, timedelta

    gh_result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == current_user.id)
    )
    gh = gh_result.scalar_one_or_none()

    if not gh:
        return {"has_data": False, "message": "Add your GitHub username to start tracking"}

    # Parse contribution calendar
    cal_raw = gh.contribution_calendar or "{}"
    try:
        calendar = json.loads(cal_raw)
    except Exception:
        calendar = {}

    # Build 52-week contribution graph
    today = date.today()
    contribution_graph = []
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        count = calendar.get(d.isoformat(), 0)
        level = 0 if count == 0 else 1 if count <= 3 else 2 if count <= 6 else 3 if count <= 9 else 4
        contribution_graph.append({"date": d.isoformat(), "count": count, "level": level})

    # Parse top languages
    try:
        top_languages = json.loads(gh.top_languages or "{}")
    except Exception:
        top_languages = {}

    return {
        "has_data": True,
        "stats": {
            "public_repos": gh.public_repos,
            "total_commits": gh.total_commits,
            "pull_requests": gh.pull_requests,
            "issues_opened": gh.issues_opened,
            "stars_received": gh.stars_received,
            "followers": gh.followers,
            "following": gh.following,
            "contribution_streak": gh.contribution_streak,
            "longest_contribution_streak": gh.longest_contribution_streak,
            "last_synced": gh.last_synced.isoformat() if gh.last_synced else None,
        },
        "contribution_graph": contribution_graph,
        "top_languages": top_languages,
    }


@router.get("/score")
async def get_student_score(
    current_user: CurrentUser = Depends(require_staff_or_student),
    db: AsyncSession = Depends(get_db),
):
    """Get performance and placement scores."""
    result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == current_user.id)
    )
    perf = result.scalar_one_or_none()

    if not perf:
        return {
            "has_data": False,
            "message": "Scores will be calculated after your first LeetCode/GitHub sync",
        }

    return {
        "has_data": True,
        "total_score": perf.total_score,
        "leetcode_score": perf.leetcode_score,
        "github_score": perf.github_score,
        "placement_score": perf.placement_score,
        "classification": perf.classification,
        "placement_classification": perf.placement_classification,
        "calculated_at": perf.calculated_at.isoformat(),
    }


@router.post("/sync")
async def trigger_sync(
    current_user: CurrentUser = Depends(require_staff_or_student),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger LeetCode + GitHub sync for the authenticated user.
    Uses direct async sync (no Celery required).
    """
    from app.services.sync_service import (
        recalculate_score_direct,
        sync_github_direct,
        sync_leetcode_direct,
    )

    user_uuid = current_user.id

    lc_result = await sync_leetcode_direct(db, user_uuid)
    gh_result = await sync_github_direct(db, user_uuid)

    # Always recalculate score even if one platform failed
    await recalculate_score_direct(db, user_uuid)

    return {
        "message": "Sync complete!",
        "leetcode": lc_result,
        "github": gh_result,
    }
