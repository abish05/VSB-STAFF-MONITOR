"""
Direct Sync Service — fetches LeetCode and GitHub data synchronously.
This bypasses Celery so it works even without a running worker.
"""

import logging
import uuid
from datetime import date, datetime, timezone

from app.models.github import GitHubActivity, GitHubStats
from app.models.leetcode import LeetCodeHistory, LeetCodeStats
from app.models.profiles import StaffProfile, StudentProfile
from app.models.sync import SyncLog
from app.services.github_service import github_service
from app.services.leetcode_service import leetcode_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _get_username_for_user(db: AsyncSession, user_uuid: uuid.UUID):
    """Return (lc_username, gh_username) for any user role."""
    # Check student profile
    sp_r = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_uuid))
    sp = sp_r.scalar_one_or_none()
    if sp:
        return sp.leetcode_username, sp.github_username

    # Check staff profile
    st_r = await db.execute(select(StaffProfile).where(StaffProfile.user_id == user_uuid))
    st = st_r.scalar_one_or_none()
    if st:
        return st.leetcode_username, st.github_username

    return None, None


async def sync_leetcode_direct(db: AsyncSession, user_uuid: uuid.UUID) -> dict:
    """Directly fetch and save LeetCode stats for a user. No Celery needed."""
    lc_username, _ = await _get_username_for_user(db, user_uuid)
    if not lc_username:
        return {"status": "skipped", "reason": "No LeetCode username"}

    start = datetime.now(tz=timezone.utc)
    try:
        stats_data = await leetcode_service.fetch_user_stats(lc_username)
        now = datetime.now(tz=timezone.utc)

        # Upsert LeetCodeStats
        existing_r = await db.execute(select(LeetCodeStats).where(LeetCodeStats.user_id == user_uuid))
        lc_stats = existing_r.scalar_one_or_none()

        if lc_stats:
            for key, val in stats_data.items():
                if key != "username" and hasattr(lc_stats, key):
                    setattr(lc_stats, key, val)
            lc_stats.last_synced = now
        else:
            lc_stats = LeetCodeStats(
                user_id=user_uuid,
                **{k: v for k, v in stats_data.items() if k != "username"},
                last_synced=now,
            )
            db.add(lc_stats)

        await db.flush()

        # Daily snapshot
        today = date.today()
        hist_r = await db.execute(
            select(LeetCodeHistory).where(
                LeetCodeHistory.user_id == user_uuid,
                LeetCodeHistory.snapshot_date == today,
            )
        )
        if not hist_r.scalar_one_or_none():
            db.add(LeetCodeHistory(
                user_id=user_uuid,
                stats_id=lc_stats.id,
                snapshot_date=today,
                problems_solved=0,
                total_solved_at_date=stats_data.get("total_solved", 0),
            ))

        duration_ms = int((datetime.now(tz=timezone.utc) - start).total_seconds() * 1000)
        db.add(SyncLog(user_id=user_uuid, platform="leetcode", status="success", duration_ms=duration_ms))
        await db.commit()

        logger.info(f"LeetCode direct sync OK for user {user_uuid}: {stats_data['total_solved']} solved")
        return {"status": "success", "total_solved": stats_data["total_solved"]}

    except Exception as exc:
        logger.error(f"LeetCode direct sync failed for user {user_uuid}: {exc}")
        await db.rollback()
        try:
            db.add(SyncLog(user_id=user_uuid, platform="leetcode", status="failed", error_message=str(exc)[:500]))
            await db.commit()
        except Exception:
            pass
        return {"status": "error", "reason": str(exc)}


async def sync_github_direct(db: AsyncSession, user_uuid: uuid.UUID) -> dict:
    """Directly fetch and save GitHub stats for a user. No Celery needed."""
    _, gh_username = await _get_username_for_user(db, user_uuid)
    if not gh_username:
        return {"status": "skipped", "reason": "No GitHub username"}

    start = datetime.now(tz=timezone.utc)
    try:
        stats_data = await github_service.fetch_all_stats(gh_username)
        now = datetime.now(tz=timezone.utc)

        # Upsert GitHubStats
        existing_r = await db.execute(select(GitHubStats).where(GitHubStats.user_id == user_uuid))
        gh_stats = existing_r.scalar_one_or_none()

        if gh_stats:
            for key, val in stats_data.items():
                if hasattr(gh_stats, key):
                    setattr(gh_stats, key, val)
            gh_stats.last_synced = now
        else:
            gh_stats = GitHubStats(
                user_id=user_uuid,
                **stats_data,
                last_synced=now,
            )
            db.add(gh_stats)

        await db.flush()

        # Daily snapshot
        today = date.today()
        act_r = await db.execute(
            select(GitHubActivity).where(
                GitHubActivity.user_id == user_uuid,
                GitHubActivity.activity_date == today,
            )
        )
        if not act_r.scalar_one_or_none():
            db.add(GitHubActivity(
                user_id=user_uuid,
                stats_id=gh_stats.id,
                activity_date=today,
                commits=stats_data.get("total_commits", 0),
                pull_requests=stats_data.get("pull_requests", 0),
                issues=stats_data.get("issues_opened", stats_data.get("issues", 0)),
            ))

        duration_ms = int((datetime.now(tz=timezone.utc) - start).total_seconds() * 1000)
        db.add(SyncLog(user_id=user_uuid, platform="github", status="success", duration_ms=duration_ms))
        await db.commit()

        logger.info(f"GitHub direct sync OK for user {user_uuid}")
        return {"status": "success", "commits": stats_data["total_commits"]}

    except Exception as exc:
        logger.error(f"GitHub direct sync failed for user {user_uuid}: {exc}")
        await db.rollback()
        try:
            db.add(SyncLog(user_id=user_uuid, platform="github", status="failed", error_message=str(exc)[:500]))
            await db.commit()
        except Exception:
            pass
        return {"status": "error", "reason": str(exc)}


async def recalculate_score_direct(db: AsyncSession, user_uuid: uuid.UUID) -> None:
    """Recalculate performance score immediately after sync."""
    from app.models.github import GitHubStats
    from app.models.leetcode import LeetCodeStats
    from app.models.performance import PerformanceScore
    from app.services.scoring_service import (
        GitHubInput,
        LeetCodeInput,
        calculate_performance_score,
        calculate_placement_score,
    )

    lc_r = await db.execute(select(LeetCodeStats).where(LeetCodeStats.user_id == user_uuid))
    lc = lc_r.scalar_one_or_none()

    gh_r = await db.execute(select(GitHubStats).where(GitHubStats.user_id == user_uuid))
    gh = gh_r.scalar_one_or_none()

    if not lc and not gh:
        return

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

    perf_r = await db.execute(select(PerformanceScore).where(PerformanceScore.user_id == user_uuid))
    perf = perf_r.scalar_one_or_none()

    now = datetime.now(tz=timezone.utc)
    if perf:
        perf.leetcode_score = lc_score
        perf.github_score = gh_score
        perf.total_score = total_score
        perf.placement_score = placement_score
        perf.classification = classification
        perf.placement_classification = placement_class
        perf.calculated_at = now
    else:
        db.add(PerformanceScore(
            user_id=user_uuid,
            leetcode_score=lc_score,
            github_score=gh_score,
            total_score=total_score,
            placement_score=placement_score,
            classification=classification,
            placement_classification=placement_class,
            calculated_at=now,
        ))
    await db.commit()
