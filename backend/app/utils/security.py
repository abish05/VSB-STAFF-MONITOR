"""
Security Utilities
- bcrypt password hashing
- JWT access + refresh token creation/verification
- Token blacklist via Redis (graceful fallback if Redis is unavailable)
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

# Patch bcrypt before passlib context is imported to silence version reading errors
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        class DummyAbout:
            __version__ = getattr(bcrypt, "__version__", "4.0.0")
        bcrypt.__about__ = DummyAbout()
except ImportError:
    pass

from app.config import settings
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# ─── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)

# Fast context for seed/demo data only — NOT for real user passwords
_seed_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt (rounds=10)."""
    return pwd_context.hash(password)


def hash_password_fast(password: str) -> str:
    """Hash with bcrypt rounds=4. ONLY for seed/demo data — much faster."""
    return _seed_pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT ──────────────────────────────────────────────────────────────────────
def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID string)
        role: User role name ('student', 'staff', 'admin')
        extra_claims: Optional additional claims to include
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    claims: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str]:
    """
    Create a long-lived JWT refresh token.

    Returns:
        (token_string, jti) — the jti is stored in Redis for blacklisting
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())

    claims: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": jti,
    }
    token = jwt.encode(
        claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload


def create_password_reset_token(email: str) -> str:
    """Create a short-lived token for password reset (15 minutes)."""
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=15)
    claims = {
        "sub": email,
        "type": "password_reset",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> str:
    """
    Decode a password reset token and return the email.

    Raises:
        ValueError: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "password_reset":
            raise ValueError("Invalid token type")
        email: str = payload.get("sub", "")
        if not email:
            raise ValueError("Invalid token subject")
        return email
    except JWTError as exc:
        raise ValueError(f"Invalid or expired token: {exc}") from exc


# ─── Token Blacklist (Redis — optional) ───────────────────────────────────────
_redis_client = None
_redis_available = None  # None = untested, True/False = tested


async def _get_redis():
    """Get or create the Redis client singleton. Returns None if Redis unavailable."""
    global _redis_client, _redis_available

    # If we already know Redis is unavailable, skip immediately
    if _redis_available is False:
        return None

    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
            # Test the connection
            await _redis_client.ping()
            _redis_available = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}). Token blacklisting disabled — JWT expiry only.")
            _redis_client = None
            _redis_available = False
            return None

    return _redis_client


async def blacklist_token(jti: str, expire_seconds: int) -> None:
    """Add a token JTI to Redis blacklist. No-op if Redis is unavailable."""
    redis = await _get_redis()
    if redis is None:
        return
    try:
        await redis.setex(f"blacklist:{jti}", expire_seconds, "1")
    except Exception as e:
        logger.warning(f"Failed to blacklist token: {e}")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a token JTI is in the blacklist. Returns False if Redis unavailable."""
    redis = await _get_redis()
    if redis is None:
        return False
    try:
        result = await redis.get(f"blacklist:{jti}")
        return result is not None
    except Exception as e:
        logger.warning(f"Failed to check token blacklist: {e}")
        return False


async def store_refresh_token(user_id: str, jti: str) -> None:
    """Store refresh token JTI for a user in Redis. No-op if Redis unavailable."""
    redis = await _get_redis()
    if redis is None:
        return
    try:
        expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis.setex(f"refresh:{user_id}:{jti}", expire, "1")
    except Exception as e:
        logger.warning(f"Failed to store refresh token: {e}")


async def revoke_all_refresh_tokens(user_id: str) -> None:
    """Revoke all refresh tokens for a user (e.g., on password change)."""
    redis = await _get_redis()
    if redis is None:
        return
    try:
        pattern = f"refresh:{user_id}:*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.warning(f"Failed to revoke refresh tokens: {e}")
