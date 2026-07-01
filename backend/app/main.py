"""
FastAPI Application Entry Point
"""

try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        class DummyAbout:
            __version__ = getattr(bcrypt, "__version__", "4.0.0")
        bcrypt.__about__ = DummyAbout()
except ImportError:
    pass

import logging
import time
from contextlib import asynccontextmanager

from app.config import settings
from app.database import close_db
from app.routers import (
    achievements,
    admin,
    ai,
    analytics,
    auth,
    github,
    leaderboard,
    leetcode,
    notifications,
    reports,
    staff,
    students,
    users,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"🚀 {settings.APP_NAME} starting up ({settings.APP_ENV})")

    # Run Database Migrations & Seeds
    import asyncio
    import os

    if os.environ.get("TESTING") == "true":
        await _safe_seed()  # Synchronous for tests
    else:
        asyncio.create_task(_safe_seed())  # Background for production

    yield
    logger.info("Shutting down — closing DB connections...")
    await close_db()
    logger.info("✅ Shutdown complete")


async def _safe_seed():
    """Background-safe wrapper for seed_db."""
    from app.utils.seed import seed_db
    try:
        await seed_db()
    except Exception as e:
        logger.error(f"Failed to seed database: {e}", exc_info=True)


# ─── App Instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Coding Activity Monitoring & Analytics Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=r"https://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router,          prefix=f"{PREFIX}/auth",          tags=["Authentication"])
app.include_router(users.router,         prefix=f"{PREFIX}/users",         tags=["Users"])
app.include_router(students.router,      prefix=f"{PREFIX}/student",       tags=["Student"])
app.include_router(staff.router,         prefix=f"{PREFIX}/staff",         tags=["Staff"])
app.include_router(admin.router,         prefix=f"{PREFIX}/admin",         tags=["Admin"])
app.include_router(leetcode.router,      prefix=f"{PREFIX}/leetcode",      tags=["LeetCode"])
app.include_router(github.router,        prefix=f"{PREFIX}/github",        tags=["GitHub"])
app.include_router(analytics.router,     prefix=f"{PREFIX}/analytics",     tags=["Analytics"])
app.include_router(leaderboard.router,   prefix=f"{PREFIX}/leaderboard",   tags=["Leaderboard"])
app.include_router(achievements.router,  prefix=f"{PREFIX}/achievements",  tags=["Achievements"])
app.include_router(reports.router,       prefix=f"{PREFIX}/reports",       tags=["Reports"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications", tags=["Notifications"])
app.include_router(ai.router,            prefix=f"{PREFIX}/ai",            tags=["AI"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }

@app.get("/seed", tags=["Seed"])
async def trigger_seed():
    from app.utils.seed import seed_db
    try:
        await seed_db()
        return {"status": "success", "message": "Database seeded successfully!"}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.get("/warm", tags=["Health"])
async def warm_up():
    """Lightweight endpoint for frontend to pre-trigger cold starts."""
    return {"status": "warm", "ready": True}

