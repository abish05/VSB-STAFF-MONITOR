"""Models package — import all models for Alembic auto-detection"""

from app.models.achievements import Achievement, UserAchievement
from app.models.activity import ActivityLog
from app.models.github import GitHubActivity, GitHubStats
from app.models.leetcode import LeetCodeHistory, LeetCodeStats
from app.models.mentor import MentorNote
from app.models.notifications import AlertRule, Notification
from app.models.performance import PerformanceScore
from app.models.profiles import StaffProfile, StudentProfile
from app.models.reports import Report
from app.models.session import Session
from app.models.sync import SyncLog
from app.models.user import Department, Role, User

__all__ = [
    "User",
    "Role",
    "Department",
    "StudentProfile",
    "StaffProfile",
    "LeetCodeStats",
    "LeetCodeHistory",
    "GitHubStats",
    "GitHubActivity",
    "PerformanceScore",
    "Achievement",
    "UserAchievement",
    "Notification",
    "AlertRule",
    "Report",
    "MentorNote",
    "SyncLog",
    "ActivityLog",
    "Session",
]
