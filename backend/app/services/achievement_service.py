"""
Achievement Service
Checks all 10 achievement conditions and awards badges (idempotent).
"""

import logging
import uuid
from datetime import datetime, timezone

from app.models.achievements import Achievement, UserAchievement
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Achievement definitions (matching DB seed data)
ACHIEVEMENT_DEFINITIONS = [
    {
        "code": "first_lc",
        "name": "First Problem",
        "icon": "🎯",
        "description": "Solved your first LeetCode problem",
        "condition": lambda lc, gh: lc.total_solved >= 1,
        "points": 10,
    },
    {
        "code": "lc_100",
        "name": "Problem Solver",
        "icon": "🏆",
        "description": "Solved 100 LeetCode problems",
        "condition": lambda lc, gh: lc.total_solved >= 100,
        "points": 50,
    },
    {
        "code": "lc_500",
        "name": "Code Warrior",
        "icon": "⚔️",
        "description": "Solved 500 LeetCode problems",
        "condition": lambda lc, gh: lc.total_solved >= 500,
        "points": 150,
    },
    {
        "code": "lc_1000",
        "name": "LeetCode Legend",
        "icon": "👑",
        "description": "Solved 1000 LeetCode problems",
        "condition": lambda lc, gh: lc.total_solved >= 1000,
        "points": 500,
    },
    {
        "code": "streak_30",
        "name": "Consistency King",
        "icon": "📅",
        "description": "Maintained a 30-day coding streak",
        "condition": lambda lc, gh: lc.current_streak >= 30,
        "points": 75,
    },
    {
        "code": "streak_100",
        "name": "100-Day Streak",
        "icon": "🔥",
        "description": "Maintained a 100-day coding streak",
        "condition": lambda lc, gh: lc.current_streak >= 100,
        "points": 200,
    },
    {
        "code": "oss",
        "name": "Open Source Hero",
        "icon": "🌐",
        "description": "Opened 10+ pull requests on GitHub",
        "condition": lambda lc, gh: gh.pull_requests >= 10,
        "points": 100,
    },
    {
        "code": "contest",
        "name": "Contest Expert",
        "icon": "🥇",
        "description": "Reached 1800+ contest rating on LeetCode",
        "condition": lambda lc, gh: lc.contest_rating >= 1800,
        "points": 200,
    },
    {
        "code": "gh_star",
        "name": "GitHub Star",
        "icon": "⭐",
        "description": "Received 50+ stars on GitHub repositories",
        "condition": lambda lc, gh: gh.stars_received >= 50,
        "points": 100,
    },
    {
        "code": "hard_solver",
        "name": "Hard Mode",
        "icon": "💎",
        "description": "Solved 50+ hard LeetCode problems",
        "condition": lambda lc, gh: lc.hard_solved >= 50,
        "points": 150,
    },
]


async def check_and_award_achievements(
    db: AsyncSession,
    user_id: uuid.UUID,
    leetcode_stats: LeetCodeStats,
    github_stats: GitHubStats,
) -> list[str]:
    """
    Check all achievements for a user and award any newly earned ones.
    Idempotent — won't duplicate already-awarded achievements.

    Returns list of newly awarded achievement codes.
    """
    newly_awarded = []

    # Get already-awarded achievement codes for this user
    existing_result = await db.execute(
        select(UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id)
    )
    awarded_ids = {str(row[0]) for row in existing_result.fetchall()}

    # Load all achievement records from DB
    all_achievements_result = await db.execute(select(Achievement))
    achievements_by_code = {
        a.code: a for a in all_achievements_result.scalars().all()
    }

    for defn in ACHIEVEMENT_DEFINITIONS:
        code = defn["code"]
        achievement = achievements_by_code.get(code)
        if not achievement:
            logger.warning(f"Achievement '{code}' not found in DB. Run seeds first.")
            continue

        if str(achievement.id) in awarded_ids:
            continue  # Already awarded

        # Check condition
        try:
            if defn["condition"](leetcode_stats, github_stats):
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    awarded_at=datetime.now(tz=timezone.utc),
                )
                db.add(user_achievement)
                newly_awarded.append(code)
                logger.info(f"Awarded achievement '{code}' to user {user_id}")
        except Exception as exc:
            logger.error(f"Error checking achievement '{code}': {exc}")
            continue

    if newly_awarded:
        await db.commit()

    return newly_awarded


async def get_user_achievements(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict]:
    """
    Return all achievement definitions with unlock status for a user.
    """
    # Get awarded achievement IDs and timestamps
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user_id)
    )
    user_achievements = {ua.achievement_id: ua for ua in result.scalars().all()}

    # Load all achievement definitions
    all_achievements_result = await db.execute(select(Achievement))
    all_achievements = all_achievements_result.scalars().all()

    achievements_response = []
    for achievement in all_achievements:
        ua = user_achievements.get(achievement.id)
        achievements_response.append({
            "id": achievement.id,
            "code": achievement.code,
            "name": achievement.name,
            "description": achievement.description,
            "icon": achievement.icon,
            "points": achievement.points,
            "is_unlocked": ua is not None,
            "awarded_at": ua.awarded_at if ua else None,
        })

    return achievements_response
