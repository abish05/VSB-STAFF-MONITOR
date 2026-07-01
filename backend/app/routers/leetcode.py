"""LeetCode Router — fetch stats and trigger sync"""

import uuid

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user, require_admin
from app.models.leetcode import LeetCodeStats
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/stats/{user_id}")
async def get_leetcode_stats(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get LeetCode stats for a user."""
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == user_id)
    )
    lc = result.scalar_one_or_none()

    if not lc:
        return {"has_data": False, "message": "No LeetCode data. Add username and sync."}

    return {"has_data": True, "stats": lc}


@router.post("/sync/{user_id}")
async def sync_leetcode(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """Admin: trigger LeetCode sync for a specific user."""
    from app.tasks.sync_leetcode import sync_user_leetcode
    sync_user_leetcode.delay(str(user_id))
    return {"message": f"LeetCode sync initiated for user {user_id}"}


@router.get("/verify/{username}")
async def verify_username(
    username: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Verify if a LeetCode username exists."""
    from app.utils.validators import verify_leetcode_username_exists
    exists = await verify_leetcode_username_exists(username)
    return {"username": username, "exists": exists}
