"""Users Router — profile CRUD, username updates, notifications"""

import logging
import uuid

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.profiles import StaffProfile, StudentProfile
from app.models.user import User
from app.schemas.reports import PaginatedNotifications
from app.schemas.user import (
    UpdateGitHubUsername,
    UpdateLeetCodeUsername,
    UserProfileUpdate,
    UserResponse,
)
from app.services.notification_service import (
    get_user_notifications,
    mark_all_read,
    mark_notification_read,
)
from app.utils.validators import (
    verify_github_username_exists,
    verify_leetcode_username_exists,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

router = APIRouter()
logger = logging.getLogger(__name__)


async def _load_user_full(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Load user with role and department eagerly."""
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.role),
            joinedload(User.department),
            joinedload(User.leetcode_stats),
            joinedload(User.github_stats),
            joinedload(User.student_profile),
            joinedload(User.staff_profile)
        )
        .where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    user = await _load_user_full(db, current_user.id)
    return user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    user = await _load_user_full(db, current_user.id)

    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.phone is not None:
        user.phone = update_data.phone
    if update_data.avatar_url is not None:
        user.avatar_url = update_data.avatar_url

    await db.commit()
    await db.refresh(user)
    return user


@router.put("/me/leetcode-username", status_code=status.HTTP_200_OK)
async def update_leetcode_username(
    data: UpdateLeetCodeUsername,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update LeetCode username after verifying it exists."""
    username = data.leetcode_username.strip()

    # Verify the username actually exists on LeetCode
    exists = await verify_leetcode_username_exists(username)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"LeetCode username '{username}' was not found. Please check the username and try again.",
        )

    # Update the appropriate profile
    if current_user.role == "student":
        result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.leetcode_username = username
    elif current_user.role in ("staff", "admin"):
        result = await db.execute(
            select(StaffProfile).where(StaffProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.leetcode_username = username

    await db.commit()
    return {"message": f"LeetCode username updated to '{username}'", "username": username}


@router.put("/me/github-username", status_code=status.HTTP_200_OK)
async def update_github_username(
    data: UpdateGitHubUsername,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update GitHub username after verifying it exists."""
    username = data.github_username.strip()

    exists = await verify_github_username_exists(username)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"GitHub username '{username}' was not found. Please check the username and try again.",
        )

    if current_user.role == "student":
        result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.github_username = username
    elif current_user.role in ("staff", "admin"):
        result = await db.execute(
            select(StaffProfile).where(StaffProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.github_username = username

    await db.commit()
    return {"message": f"GitHub username updated to '{username}'", "username": username}


@router.get("/me/notifications", response_model=PaginatedNotifications)
async def get_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated notifications for the authenticated user."""
    notifications, total, unread_count = await get_user_notifications(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return PaginatedNotifications(
        items=notifications,
        total=total,
        unread_count=unread_count,
    )


@router.patch("/me/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    success = await mark_notification_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.post("/me/notifications/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    count = await mark_all_read(db, current_user.id)
    return {"message": f"{count} notifications marked as read"}
