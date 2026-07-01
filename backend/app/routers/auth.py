"""Auth Router — register, login, refresh, logout, forgot/reset password"""

import logging
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_current_user
from app.models.profiles import StaffProfile, StudentProfile
from app.models.user import Department, Role, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.utils.security import (
    blacklist_token,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_token,
    hash_password,
    is_token_blacklisted,
    store_refresh_token,
    verify_password,
)
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)

# Auth-specific rate limiter (stricter)
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user (student, staff, or admin)."""
    # Check email uniqueness
    existing = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Look up role
    role_result = await db.execute(
        select(Role).where(Role.name == request.role)
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{request.role}' not found. Run database seeds first.",
        )

    # Look up department if provided
    department_id = None
    if request.department_code:
        dept_result = await db.execute(
            select(Department).where(Department.code == request.department_code)
        )
        dept = dept_result.scalar_one_or_none()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department '{request.department_code}' not found",
            )
        department_id = dept.id

    # Create user
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role_id=role.id,
        department_id=department_id,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create role-specific profile
    if request.role == "student":
        # Validate reg_no uniqueness
        existing_reg = await db.execute(
            select(StudentProfile).where(StudentProfile.reg_no == request.reg_no)
        )
        if existing_reg.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Registration number '{request.reg_no}' is already registered",
            )
        profile = StudentProfile(
            user_id=user.id,
            reg_no=request.reg_no,
            year=request.year,
            section=request.section,
            leetcode_username=request.leetcode_username,
            github_username=request.github_username,
        )
        db.add(profile)

    elif request.role == "staff":
        existing_emp = await db.execute(
            select(StaffProfile).where(StaffProfile.employee_id == request.employee_id)
        )
        if existing_emp.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee ID '{request.employee_id}' is already registered",
            )
        profile = StaffProfile(
            user_id=user.id,
            employee_id=request.employee_id,
            designation=request.designation,
            leetcode_username=request.leetcode_username,
            github_username=request.github_username,
        )
        db.add(profile)

    await db.commit()
    logger.info(f"New user registered: {user.email} (role={request.role})")

    # Issue tokens
    access_token = create_access_token(subject=str(user.id), role=request.role)
    refresh_token, jti = create_refresh_token(subject=str(user.id))
    await store_refresh_token(str(user.id), jti)

    # Auto-sync platform data if usernames were provided
    lc_username = request.leetcode_username if hasattr(request, 'leetcode_username') else None
    gh_username = request.github_username if hasattr(request, 'github_username') else None

    if lc_username or gh_username:
        try:
            from app.services.sync_service import (
                recalculate_score_direct,
                sync_github_direct,
                sync_leetcode_direct,
            )
            # Refresh db session to see new profile
            await db.refresh(user)
            if lc_username:
                await sync_leetcode_direct(db, user.id)
            if gh_username:
                await sync_github_direct(db, user.id)
            await recalculate_score_direct(db, user.id)
            logger.info(f"Auto-synced platform data for new user {user.email}")
        except Exception as sync_exc:
            logger.warning(f"Auto-sync failed for {user.email}: {sync_exc} (non-fatal)")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a user and return JWT pair."""
    from sqlalchemy.orm import joinedload

    login_id = request.email.lower().strip()
    # Resolve username format if not containing @
    if "@" not in login_id:
        if login_id in ["admin1", "admin2", "admin3"]:
            login_id = f"{login_id}@vsb.edu.in"
        elif login_id.startswith("student") or login_id.startswith("staff"):
            login_id = f"{login_id}@vsb.edu.in"

    result = await db.execute(
        select(User)
        .options(joinedload(User.role))
        .where(User.email == login_id)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Contact your administrator.",
        )

    # Restrict Admin login from regular portals
    if user.role.name == "admin" and not request.is_admin_portal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin login is not allowed from this portal. Please use the administrative portal.",
        )

    # Update last login
    user.last_login_at = datetime.now(tz=timezone.utc)
    await db.commit()

    access_token = create_access_token(subject=str(user.id), role=user.role.name)
    refresh_token, jti = create_refresh_token(subject=str(user.id))
    await store_refresh_token(str(user.id), jti)

    # Log action to ActivityLog
    from app.models.activity import ActivityLog
    db.add(ActivityLog(
        user_id=user.id,
        action="user.login",
        resource_type="auth",
        resource_id=str(user.id),
        metadata={"email": user.email, "is_admin_portal": request.is_admin_portal}
    ))

    # Add token Session entry
    from app.models.session import Session
    session_expiry = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    db.add(Session(
        user_id=user.id,
        token=access_token,
        expires_at=session_expiry
    ))
    await db.commit()

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token using a valid refresh token."""
    from jose import JWTError
    from sqlalchemy.orm import joinedload

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = decode_token(request.refresh_token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise credentials_exception

    jti = payload.get("jti", "")
    if await is_token_blacklisted(jti):
        raise credentials_exception

    import uuid
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(User).options(joinedload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    # Blacklist old refresh token
    await blacklist_token(jti, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    # Issue new pair
    new_access = create_access_token(subject=str(user.id), role=user.role.name)
    new_refresh, new_jti = create_refresh_token(subject=str(user.id))
    await store_refresh_token(str(user.id), new_jti)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: LogoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Logout: blacklist the refresh token."""
    from jose import JWTError

    try:
        payload = decode_token(request.refresh_token)
        jti = payload.get("jti", "")
        if jti:
            await blacklist_token(jti, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    except JWTError:
        pass  # Already invalid — that's fine

    return None


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send password reset email (always returns 200 to prevent user enumeration)."""
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()

    if user:
        token = create_password_reset_token(user.email)
        # In production: send via SMTP/SendGrid
        # For now, log the token (remove in production!)
        logger.info(f"Password reset token for {user.email}: {token}")
        # TODO: email_service.send_reset_email(user.email, token)

    return {"message": "If this email is registered, you will receive a password reset link shortly."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    try:
        email = decode_password_reset_token(request.token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.password_hash = hash_password(request.new_password)
    await db.commit()

    return {"message": "Password has been reset successfully. Please log in with your new password."}
