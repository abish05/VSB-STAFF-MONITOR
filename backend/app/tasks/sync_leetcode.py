"""
Celery Tasks — LeetCode Sync
Runs daily at 2 AM for all users with a LeetCode username.
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone

from app.tasks.celery_app import celery_app
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _get_db_session():
    """Create a synchronous-compatible async DB session for Celery."""
    from app.database import AsyncSessionLocal
    return AsyncSessionLocal()


@celery_app.task(
    name="app.tasks.sync_leetcode.sync_user_leetcode",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="sync",
)
def sync_user_leetcode(self, user_id: str):
    """Sync LeetCode stats for a single user."""
    asyncio.run(_sync_user_leetcode_async(user_id, task=self))


async def _sync_user_leetcode_async(user_id: str, task=None):
    """Async implementation of LeetCode sync for one user."""
    from app.models.leetcode import LeetCodeHistory, LeetCodeStats
    from app.models.profiles import StaffProfile, StudentProfile
    from app.models.sync import SyncLog
    from app.services.leetcode_service import leetcode_service

    start_time = datetime.now(tz=timezone.utc)
    user_uuid = uuid.UUID(user_id)

    async with _get_db_session() as db:
        # Find LeetCode username from profile
        lc_username = None

        student_result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_uuid)
        )
        student = student_result.scalar_one_or_none()
        if student and student.leetcode_username:
            lc_username = student.leetcode_username

        if not lc_username:
            staff_result = await db.execute(
                select(StaffProfile).where(StaffProfile.user_id == user_uuid)
            )
            staff = staff_result.scalar_one_or_none()
            if staff and staff.leetcode_username:
                lc_username = staff.leetcode_username

        if not lc_username:
            logger.debug(f"User {user_id} has no LeetCode username, skipping")
            return

        try:
            stats_data = await leetcode_service.fetch_user_stats(lc_username)
            now = datetime.now(tz=timezone.utc)

            # Upsert LeetCodeStats
            existing_result = await db.execute(
                select(LeetCodeStats).where(LeetCodeStats.user_id == user_uuid)
            )
            lc_stats = existing_result.scalar_one_or_none()

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

            # Insert daily snapshot
            today = date.today()
            history = LeetCodeHistory(
                user_id=user_uuid,
                stats_id=lc_stats.id,
                snapshot_date=today,
                problems_solved=0,  # Would need delta calculation
                total_solved_at_date=stats_data.get("total_solved", 0),
            )
            # Only insert if no entry for today yet
            existing_history = await db.execute(
                select(LeetCodeHistory).where(
                    LeetCodeHistory.user_id == user_uuid,
                    LeetCodeHistory.snapshot_date == today,
                )
            )
            if not existing_history.scalar_one_or_none():
                db.add(history)

            # Log success
            duration_ms = int((datetime.now(tz=timezone.utc) - start_time).total_seconds() * 1000)
            sync_log = SyncLog(
                user_id=user_uuid,
                platform="leetcode",
                status="success",
                duration_ms=duration_ms,
            )
            db.add(sync_log)
            await db.commit()

            # Trigger score recalculation
            _recalculate_user_score.delay(user_id)

            logger.info(f"LeetCode sync success for user {user_id}: {stats_data['total_solved']} solved")

        except Exception as exc:
            logger.error(f"LeetCode sync failed for user {user_id}: {exc}")
            sync_log = SyncLog(
                user_id=user_uuid,
                platform="leetcode",
                status="failed",
                error_message=str(exc)[:500],
            )
            db.add(sync_log)
            await db.commit()
            if task:
                raise task.retry(exc=exc)


@celery_app.task(
    name="app.tasks.sync_leetcode.sync_all_users",
    queue="sync",
)
def sync_all_users():
    """Sync LeetCode for ALL users with a username. Runs in batches."""
    asyncio.run(_sync_all_async())


async def _sync_all_async():
    """Chunk all users and dispatch individual sync tasks."""
    from app.models.profiles import StaffProfile, StudentProfile

    async with _get_db_session() as db:
        # Students
        student_result = await db.execute(
            select(StudentProfile.user_id)
            .where(StudentProfile.leetcode_username.isnot(None))
        )
        student_ids = [str(row[0]) for row in student_result.fetchall()]

        # Staff
        staff_result = await db.execute(
            select(StaffProfile.user_id)
            .where(StaffProfile.leetcode_username.isnot(None))
        )
        staff_ids = [str(row[0]) for row in staff_result.fetchall()]

    all_ids = student_ids + staff_ids
    logger.info(f"Scheduling LeetCode sync for {len(all_ids)} users")

    # Dispatch with 0.5s delay between each to avoid rate limits
    for i, user_id in enumerate(all_ids):
        sync_user_leetcode.apply_async(args=[user_id], countdown=i * 2)


@celery_app.task(name="app.tasks.sync_leetcode.recalculate_all_scores", queue="default")
def recalculate_all_scores():
    """Recalculate performance scores for all users."""
    asyncio.run(_recalculate_all_async())


async def _recalculate_all_async():
    from app.models.user import User
    async with _get_db_session() as db:
        result = await db.execute(select(User.id).where(User.is_active == True))  # noqa
        user_ids = [str(row[0]) for row in result.fetchall()]
    for uid in user_ids:
        _recalculate_user_score.delay(uid)


@celery_app.task(name="app.tasks.sync_leetcode.recalculate_user_score", queue="default")
def _recalculate_user_score(user_id: str):
    asyncio.run(_recalculate_score_async(user_id))


async def _recalculate_score_async(user_id: str):
    from datetime import timezone

    from app.models.github import GitHubStats
    from app.models.leetcode import LeetCodeStats
    from app.models.performance import PerformanceScore
    from app.services.scoring_service import (
        GitHubInput,
        LeetCodeInput,
        calculate_performance_score,
        calculate_placement_score,
    )

    user_uuid = uuid.UUID(user_id)
    async with _get_db_session() as db:
        lc_result = await db.execute(select(LeetCodeStats).where(LeetCodeStats.user_id == user_uuid))
        lc = lc_result.scalar_one_or_none()

        gh_result = await db.execute(select(GitHubStats).where(GitHubStats.user_id == user_uuid))
        gh = gh_result.scalar_one_or_none()

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

        perf_result = await db.execute(select(PerformanceScore).where(PerformanceScore.user_id == user_uuid))
        perf = perf_result.scalar_one_or_none()

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
                leetcode_score=lc_score, github_score=gh_score,
                total_score=total_score, placement_score=placement_score,
                classification=classification, placement_classification=placement_class,
                calculated_at=now,
            ))
        await db.commit()


@celery_app.task(name="app.tasks.sync_leetcode.check_all_achievements", queue="default")
def check_all_achievements():
    """Run achievement checks for all users after sync."""
    asyncio.run(_check_achievements_async())


async def _check_achievements_async():
    from app.models.github import GitHubStats
    from app.models.leetcode import LeetCodeStats
    from app.models.user import User
    from app.services.achievement_service import (
        ACHIEVEMENT_DEFINITIONS,
        check_and_award_achievements,
    )
    from app.services.notification_service import send_achievement_notification

    async with _get_db_session() as db:
        result = await db.execute(select(User.id).where(User.is_active == True))  # noqa
        user_ids = [row[0] for row in result.fetchall()]

    for uid in user_ids:
        async with _get_db_session() as db:
            lc_r = await db.execute(select(LeetCodeStats).where(LeetCodeStats.user_id == uid))
            lc = lc_r.scalar_one_or_none()
            gh_r = await db.execute(select(GitHubStats).where(GitHubStats.user_id == uid))
            gh = gh_r.scalar_one_or_none()

            if not lc and not gh:
                continue

            # Use dummy objects if one is missing
            class _Dummy:
                def __getattr__(self, _): return 0

            awarded = await check_and_award_achievements(
                db, uid,
                lc or _Dummy(),
                gh or _Dummy(),
            )
            for code in awarded:
                defn = next((d for d in ACHIEVEMENT_DEFINITIONS if d["code"] == code), None)
                if defn:
                    await send_achievement_notification(
                        db, uid, defn["name"], defn["icon"]
                    )
