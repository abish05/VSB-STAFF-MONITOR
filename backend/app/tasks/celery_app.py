"""
Celery Application Configuration with Beat Schedule
"""

from app.config import settings
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "codepulse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.sync_leetcode",
        "app.tasks.sync_github",
        "app.tasks.check_alerts",
        "app.tasks.generate_reports",
    ],
)

# ─── Celery Config ────────────────────────────────────────────────────────────
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.sync_leetcode.*": {"queue": "sync"},
        "app.tasks.sync_github.*": {"queue": "sync"},
        "app.tasks.generate_reports.*": {"queue": "reports"},
        "app.tasks.check_alerts.*": {"queue": "default"},
    },
)

# ─── Beat Schedule (IST-aligned using UTC offsets) ───────────────────────────
celery_app.conf.beat_schedule = {
    # 2 AM IST = 8:30 PM UTC previous day → simplified to 2 AM UTC for clarity
    "sync-all-leetcode": {
        "task": "app.tasks.sync_leetcode.sync_all_users",
        "schedule": crontab(hour=2, minute=0),
    },
    # 3 AM daily
    "sync-all-github": {
        "task": "app.tasks.sync_github.sync_all_users",
        "schedule": crontab(hour=3, minute=0),
    },
    # 4 AM daily — recalculate all performance scores
    "recalculate-scores": {
        "task": "app.tasks.sync_leetcode.recalculate_all_scores",
        "schedule": crontab(hour=4, minute=0),
    },
    # 4:30 AM daily — award achievements
    "check-achievements": {
        "task": "app.tasks.sync_leetcode.check_all_achievements",
        "schedule": crontab(hour=4, minute=30),
    },
    # 8 AM daily — check alert rules
    "check-alerts": {
        "task": "app.tasks.check_alerts.run_alert_checks",
        "schedule": crontab(hour=8, minute=0),
    },
}
