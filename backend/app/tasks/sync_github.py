"""
Celery Tasks — GitHub Sync
Runs daily at 3 AM for all users with a GitHub username.
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_db_session():
    from app.database import AsyncSessionLocal
    return AsyncSessionLocal()


@celery_app.task(
    name="app.tasks.sync_github.sync_user_github",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="sync",
)
def sync_user_github(self, user_id: str):
    """Sync GitHub stats for a single user."""
    asyncio.run(_sync_user_github_async(user_id, task=self))


async def _sync_user_github_async(user_id: str, task=None):
    from app.models.github import GitHubActivity, GitHubStats
    from app.models.profiles import StaffProfile, StudentProfile
    from app.models.sync import SyncLog
    from app.services.github_service import github_service
    from sqlalchemy import select

    start_time = datetime.now(tz=timezone.utc)
    user_uuid = uuid.UUID(user_id)

    async with _get_db_session() as db:
        gh_username = None

        student_result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_uuid)
        )
        student = student_result.scalar_one_or_none()
        if student and student.github_username:
            gh_username = student.github_username

        if not gh_username:
            staff_result = await db.execute(
                select(StaffProfile).where(StaffProfile.user_id == user_uuid)
            )
            staff = staff_result.scalar_one_or_none()
            if staff and staff.github_username:
                gh_username = staff.github_username

        if not gh_username:
            return

        try:
            stats_data = await github_service.fetch_all_stats(gh_username)
            now = datetime.now(tz=timezone.utc)

            existing_result = await db.execute(
                select(GitHubStats).where(GitHubStats.user_id == user_uuid)
            )
            gh_stats = existing_result.scalar_one_or_none()

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
            existing_activity = await db.execute(
                select(GitHubActivity).where(
                    GitHubActivity.user_id == user_uuid,
                    GitHubActivity.activity_date == today,
                )
            )
            if not existing_activity.scalar_one_or_none():
                activity = GitHubActivity(
                    user_id=user_uuid,
                    stats_id=gh_stats.id,
                    activity_date=today,
                    commits=0,
                    pull_requests=0,
                    issues=0,
                )
                db.add(activity)

            duration_ms = int((datetime.now(tz=timezone.utc) - start_time).total_seconds() * 1000)
            sync_log = SyncLog(
                user_id=user_uuid,
                platform="github",
                status="success",
                duration_ms=duration_ms,
            )
            db.add(sync_log)
            await db.commit()

            logger.info(f"GitHub sync success for user {user_id}")

        except Exception as exc:
            logger.error(f"GitHub sync failed for user {user_id}: {exc}")
            sync_log = SyncLog(
                user_id=user_uuid,
                platform="github",
                status="failed",
                error_message=str(exc)[:500],
            )
            db.add(sync_log)
            await db.commit()
            if task:
                raise task.retry(exc=exc)


@celery_app.task(name="app.tasks.sync_github.sync_all_users", queue="sync")
def sync_all_users():
    """Sync GitHub for ALL users with a username."""
    asyncio.run(_sync_all_async())


async def _sync_all_async():
    from app.models.profiles import StaffProfile, StudentProfile
    from sqlalchemy import select

    async with _get_db_session() as db:
        student_result = await db.execute(
            select(StudentProfile.user_id).where(StudentProfile.github_username.isnot(None))
        )
        student_ids = [str(row[0]) for row in student_result.fetchall()]

        staff_result = await db.execute(
            select(StaffProfile.user_id).where(StaffProfile.github_username.isnot(None))
        )
        staff_ids = [str(row[0]) for row in staff_result.fetchall()]

    all_ids = student_ids + staff_ids
    logger.info(f"Scheduling GitHub sync for {len(all_ids)} users")

    for i, user_id in enumerate(all_ids):
        sync_user_github.apply_async(args=[user_id], countdown=i * 3)
