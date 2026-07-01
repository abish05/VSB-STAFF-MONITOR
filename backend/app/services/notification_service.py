"""
Notification Service
Creates in-app notifications and evaluates alert rules.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.notifications import Notification
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    message: str,
    metadata: Optional[dict] = None,
) -> Notification:
    """Create a single in-app notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        metadata_=metadata,
        created_at=datetime.now(tz=timezone.utc),
    )
    db.add(notification)
    await db.flush()
    return notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> tuple[list[Notification], int, int]:
    """
    Get paginated notifications for a user.
    Returns (notifications, total, unread_count)
    """
    # Base query
    query = select(Notification).where(Notification.user_id == user_id)

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(
            select(Notification)
            .where(Notification.user_id == user_id)
            .subquery()
        )
    )
    total = count_result.scalar() or 0

    # Count unread
    unread_result = await db.execute(
        select(func.count()).select_from(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa
            .subquery()
        )
    )
    unread_count = unread_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = (
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    notifications = result.scalars().all()

    return list(notifications), total, unread_count


async def mark_notification_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Mark a specific notification as read. Returns True if found."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        return False

    notification.is_read = True
    notification.read_at = datetime.now(tz=timezone.utc)
    await db.flush()
    return True


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Mark all notifications as read for a user. Returns count updated."""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa
        )
    )
    notifications = result.scalars().all()
    now = datetime.now(tz=timezone.utc)
    for n in notifications:
        n.is_read = True
        n.read_at = now
    await db.flush()
    return len(notifications)


async def send_achievement_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    achievement_name: str,
    achievement_icon: str,
) -> None:
    """Send notification when a badge is awarded."""
    await create_notification(
        db=db,
        user_id=user_id,
        notification_type="achievement",
        title=f"🎉 Achievement Unlocked: {achievement_icon} {achievement_name}",
        message=f"Congratulations! You've earned the '{achievement_name}' badge. Keep up the great work!",
        metadata={"achievement_name": achievement_name, "icon": achievement_icon},
    )


async def send_streak_broken_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    streak_length: int,
) -> None:
    """Send notification when a coding streak is broken."""
    await create_notification(
        db=db,
        user_id=user_id,
        notification_type="streak_broken",
        title="🔴 Streak Broken",
        message=(
            f"Your {streak_length}-day coding streak has ended. "
            "Don't worry — start a new one today!"
        ),
        metadata={"broken_streak": streak_length},
    )


async def send_inactivity_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    days_inactive: int,
    platform: str,
) -> None:
    """Send inactivity alert notification."""
    await create_notification(
        db=db,
        user_id=user_id,
        notification_type="inactivity",
        title=f"⚠️ No {platform} Activity",
        message=(
            f"You haven't had any {platform} activity in {days_inactive} days. "
            "Stay consistent to maintain your progress!"
        ),
        metadata={"days_inactive": days_inactive, "platform": platform},
    )
