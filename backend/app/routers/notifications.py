"""Notifications Router"""

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/")
async def list_notifications(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notifications for authenticated user."""
    from app.services.notification_service import get_user_notifications
    notifications, total, unread_count = await get_user_notifications(
        db, current_user.id, page=1, page_size=20
    )
    return {
        "items": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total": total,
        "unread_count": unread_count,
    }
