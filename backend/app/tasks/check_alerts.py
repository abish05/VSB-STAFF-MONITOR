"""
Celery Tasks — Alert Checks
Runs daily at 8 AM. Implements all 5 alert rules from spec.
"""

import asyncio
import logging
from datetime import date, timedelta

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_db_session():
    from app.database import AsyncSessionLocal
    return AsyncSessionLocal()


@celery_app.task(name="app.tasks.check_alerts.run_alert_checks", queue="default")
def run_alert_checks():
    """Run all 5 alert rules for all active users."""
    asyncio.run(_run_all_checks())


async def _run_all_checks():
    from app.models.github import GitHubStats
    from app.models.leetcode import LeetCodeStats
    from app.models.performance import PerformanceScore
    from app.models.user import User
    from app.services.notification_service import (
        create_notification,
        send_inactivity_notification,
        send_streak_broken_notification,
    )
    from sqlalchemy import select

    async with _get_db_session() as db:
        # Load all active users with their stats
        users_result = await db.execute(
            select(User).where(User.is_active == True)  # noqa
        )
        users = users_result.scalars().all()

        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        fourteen_days_ago = today - timedelta(days=14)

        for user in users:
            lc_result = await db.execute(
                select(LeetCodeStats).where(LeetCodeStats.user_id == user.id)
            )
            lc = lc_result.scalar_one_or_none()

            gh_result = await db.execute(
                select(GitHubStats).where(GitHubStats.user_id == user.id)
            )
            gh = gh_result.scalar_one_or_none()

            perf_result = await db.execute(
                select(PerformanceScore).where(PerformanceScore.user_id == user.id)
            )
            perf = perf_result.scalar_one_or_none()

            # ── Rule 1: No LeetCode submission in 7 days ──────────────────────
            if lc and lc.last_synced:
                last_lc_date = lc.last_synced.date()
                if last_lc_date <= seven_days_ago and lc.current_streak == 0:
                    await send_inactivity_notification(
                        db=db,
                        user_id=user.id,
                        days_inactive=7,
                        platform="LeetCode",
                    )

            # ── Rule 2: Streak broken (was > 5, now 0) ────────────────────────
            if lc and lc.current_streak == 0 and lc.longest_streak > 5:
                await send_streak_broken_notification(
                    db=db,
                    user_id=user.id,
                    streak_length=lc.longest_streak,
                )

            # ── Rule 3: No GitHub commits in 14 days ──────────────────────────
            if gh and gh.last_synced:
                last_gh_date = gh.last_synced.date()
                if last_gh_date <= fourteen_days_ago and gh.contribution_streak == 0:
                    await send_inactivity_notification(
                        db=db,
                        user_id=user.id,
                        days_inactive=14,
                        platform="GitHub",
                    )

            # ── Rule 4: No LeetCode activity in 14 days ───────────────────────
            if lc and lc.last_synced:
                if lc.last_synced.date() <= fourteen_days_ago:
                    await create_notification(
                        db=db,
                        user_id=user.id,
                        notification_type="no_leetcode",
                        title="📉 Extended LeetCode Inactivity",
                        message="You haven't solved any LeetCode problems in 14+ days. Your mentor has been notified.",
                        metadata={"days_inactive": 14},
                    )

            # ── Rule 5: Low performance score < 30 ────────────────────────────
            if perf and perf.total_score < 30:
                await create_notification(
                    db=db,
                    user_id=user.id,
                    notification_type="low_performance",
                    title="⚠️ Low Performance Score",
                    message=f"Your performance score is {perf.total_score:.1f}/100. Check your dashboard for recommendations.",
                    metadata={"score": perf.total_score},
                )

        await db.commit()
        logger.info(f"Alert checks completed for {len(users)} users")
