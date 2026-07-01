"""Reports Router — PDF and Excel generation"""

import logging
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.middleware.auth_middleware import (
    CurrentUser,
    get_current_user,
    require_staff,
)
from app.models.github import GitHubStats
from app.models.leetcode import LeetCodeStats
from app.models.performance import PerformanceScore
from app.models.profiles import StudentProfile
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pdf/{user_id}")
async def generate_user_pdf(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a PDF report for a user."""
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Load user data
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    lc_result = await db.execute(
        select(LeetCodeStats).where(LeetCodeStats.user_id == user_id)
    )
    lc = lc_result.scalar_one_or_none()

    gh_result = await db.execute(
        select(GitHubStats).where(GitHubStats.user_id == user_id)
    )
    gh = gh_result.scalar_one_or_none()

    perf_result = await db.execute(
        select(PerformanceScore).where(PerformanceScore.user_id == user_id)
    )
    perf = perf_result.scalar_one_or_none()

    # Generate PDF
    from app.services.report_service import generate_user_pdf_report
    try:
        pdf_bytes = await generate_user_pdf_report(
            user=user,
            profile=profile,
            leetcode_stats=lc,
            github_stats=gh,
            performance=perf,
        )
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        raise HTTPException(status_code=500, detail="PDF generation failed")

    filename = f"codepulse_report_{user.full_name.replace(' ', '_')}_{datetime.now(tz=timezone.utc).strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/excel")
async def generate_excel_report(
    current_user: CurrentUser = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Generate Excel report with all users data (admin & staff)."""
    from app.services.report_service import generate_excel_report as _gen_excel
    try:
        excel_bytes = await _gen_excel(db=db)
    except Exception as exc:
        logger.error(f"Excel generation failed: {exc}")
        raise HTTPException(status_code=500, detail="Excel generation failed")

    filename = f"codepulse_report_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
