"""GitHub Router — stats and sync"""

import uuid

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user, require_admin
from app.models.github import GitHubStats
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/stats/{user_id}")
async def get_github_stats(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get GitHub stats for a user."""
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == user_id)
    )
    gh = result.scalar_one_or_none()

    if not gh:
        return {"has_data": False, "message": "No GitHub data. Add username and sync."}

    return {"has_data": True, "stats": gh}


@router.post("/sync/{user_id}")
async def sync_github(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """Admin: trigger GitHub sync for a specific user."""
    from app.tasks.sync_github import sync_user_github
    sync_user_github.delay(str(user_id))
    return {"message": f"GitHub sync initiated for user {user_id}"}


@router.get("/verify/{username}")
async def verify_github_username(
    username: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Verify if a GitHub username exists."""
    from app.utils.validators import verify_github_username_exists
    exists = await verify_github_username_exists(username)
    return {"username": username, "exists": exists}
