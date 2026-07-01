"""Input validators for usernames, reg numbers, and other fields"""

import re

import httpx
from app.config import settings


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, ""


def validate_leetcode_username(username: str) -> bool:
    """Validate LeetCode username format."""
    # LeetCode usernames: 3-25 chars, letters, numbers, underscores, hyphens
    pattern = r"^[a-zA-Z0-9_\-]{3,25}$"
    return bool(re.match(pattern, username.strip()))


def validate_github_username(username: str) -> bool:
    """Validate GitHub username format."""
    # GitHub usernames: 1-39 chars, alphanumeric + hyphens, no leading/trailing hyphens
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?$"
    return bool(re.match(pattern, username.strip()))


def validate_reg_no(reg_no: str) -> bool:
    """Validate student registration number format."""
    # Format: 7-digit number (e.g., 7376223)
    pattern = r"^\d{7,15}$"
    return bool(re.match(pattern, reg_no.strip()))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and limit length."""
    return value.strip()[:max_length]


async def verify_leetcode_username_exists(username: str) -> bool:
    """
    Verify a LeetCode username actually exists by querying the GraphQL API.
    Returns True if user exists, False otherwise.
    """
    query = """
    query userProfile($username: String!) {
        matchedUser(username: $username) {
            username
        }
    }
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://leetcode.com/graphql",
                json={"query": query, "variables": {"username": username}},
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://leetcode.com",
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("matchedUser") is not None
    except Exception:
        pass
    return False


async def verify_github_username_exists(username: str) -> bool:
    """
    Verify a GitHub username actually exists via REST API.
    Returns True if user exists, False otherwise.
    """
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.GITHUB_API_URL}/users/{username}",
                headers=headers,
            )
            return response.status_code == 200
    except Exception:
        pass
    return False
