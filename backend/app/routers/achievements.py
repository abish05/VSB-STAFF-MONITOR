"""Achievements Router"""

import uuid

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.services.achievement_service import get_user_achievements
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/")
async def get_achievements(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements with unlock status for authenticated user."""
    achievements = await get_user_achievements(db, current_user.id)
    unlocked = sum(1 for a in achievements if a["is_unlocked"])
    return {
        "achievements": achievements,
        "unlocked_count": unlocked,
        "total_count": len(achievements),
        "total_points": sum(a["points"] for a in achievements if a["is_unlocked"]),
    }


@router.get("/user/{user_id}")
async def get_user_achievements_by_id(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get achievements for a specific user (staff/admin only for other users)."""
    from fastapi import HTTPException
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    achievements = await get_user_achievements(db, user_id)
    return {"achievements": achievements}
