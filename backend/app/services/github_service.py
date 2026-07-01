"""
GitHub Service
Fetches data from GitHub REST API v3 with PAT auth and rate limit handling.
"""

import json
from datetime import date, timedelta
from typing import Any

import httpx
from app.config import settings
from app.utils.helpers import calculate_streak

GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

CONTRIBUTION_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        date
                        contributionCount
                    }
                }
            }
        }
    }
}
"""


class GitHubService:
    """Service for fetching GitHub data via REST and GraphQL APIs"""

    def __init__(self):
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodePulse-AI/1.0",
        }
        if settings.GITHUB_TOKEN:
            self._headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    async def _check_rate_limit(self, response: httpx.Response) -> None:
        """Check GitHub rate limit headers and wait if necessary."""
        remaining = int(response.headers.get("X-RateLimit-Remaining", 100))
        if remaining < 10:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            import time
            wait = max(0, reset_time - time.time()) + 1
            if wait < 60:  # Only wait if < 1 minute
                await __import__("asyncio").sleep(wait)

    async def fetch_user_profile(self, username: str) -> dict[str, Any]:
        """Fetch GitHub user profile."""
        async with self._make_client() as client:
            response = await client.get(f"{GITHUB_API_URL}/users/{username}")
            await self._check_rate_limit(response)

            if response.status_code == 404:
                raise ValueError(f"GitHub user '{username}' not found")
            response.raise_for_status()
            return response.json()

    async def fetch_repos(self, username: str) -> list[dict[str, Any]]:
        """Fetch all public repos for a user."""
        repos = []
        page = 1
        async with self._make_client() as client:
            while True:
                response = await client.get(
                    f"{GITHUB_API_URL}/users/{username}/repos",
                    params={"per_page": 100, "page": page, "sort": "pushed"},
                )
                await self._check_rate_limit(response)
                response.raise_for_status()
                batch = response.json()
                if not batch:
                    break
                repos.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
        return repos

    async def fetch_events(self, username: str, pages: int = 3) -> list[dict[str, Any]]:
        """Fetch recent public events for activity analysis."""
        events = []
        async with self._make_client() as client:
            for page in range(1, pages + 1):
                try:
                    response = await client.get(
                        f"{GITHUB_API_URL}/users/{username}/events/public",
                        params={"per_page": 100, "page": page},
                    )
                    await self._check_rate_limit(response)
                    if response.status_code == 422:
                        break  # GitHub only keeps ~90 days of events
                    response.raise_for_status()
                    batch = response.json()
                    if not batch:
                        break
                    events.extend(batch)
                except httpx.HTTPStatusError:
                    break
        return events

    async def fetch_contribution_calendar(self, username: str) -> dict[str, int]:
        """
        Fetch 52-week contribution calendar via GitHub GraphQL.
        Returns dict: {"2024-01-01": 3, ...}
        """
        from datetime import datetime, timezone
        to_dt = datetime.now(tz=timezone.utc)
        from_dt = to_dt - timedelta(days=365)

        headers = {**self._headers, "Content-Type": "application/json"}
        # Remove REST-specific auth header if present; GraphQL needs Bearer
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        payload = {
            "query": CONTRIBUTION_QUERY,
            "variables": {
                "username": username,
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat(),
            },
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
                response = await client.post(GITHUB_GRAPHQL_URL, json=payload)
                response.raise_for_status()
                data = response.json()

            weeks = (
                data.get("data", {})
                .get("user", {})
                .get("contributionsCollection", {})
                .get("contributionCalendar", {})
                .get("weeks", [])
            )
            calendar: dict[str, int] = {}
            for week in weeks:
                for day in week.get("contributionDays", []):
                    calendar[day["date"]] = day["contributionCount"]
            return calendar
        except Exception:
            return {}  # Fall back to event-based calculation

    async def fetch_all_stats(self, username: str) -> dict[str, Any]:
        """
        Fetch complete GitHub statistics for a user.
        Combines profile, repos, events, and contribution calendar.
        """
        # Fetch concurrently
        import asyncio
        profile, repos, events, calendar = await asyncio.gather(
            self.fetch_user_profile(username),
            self.fetch_repos(username),
            self.fetch_events(username),
            self.fetch_contribution_calendar(username),
            return_exceptions=True,
        )

        # Handle partial failures gracefully
        if isinstance(profile, Exception):
            raise profile
        repos = repos if not isinstance(repos, Exception) else []
        events = events if not isinstance(events, Exception) else []
        calendar = calendar if not isinstance(calendar, Exception) else {}

        # Count commits, PRs, issues from events
        total_commits = 0
        pull_requests = 0
        issues_opened = 0

        for event in events:
            event_type = event.get("type", "")
            if event_type == "PushEvent":
                total_commits += len(event.get("payload", {}).get("commits", []))
            elif event_type == "PullRequestEvent":
                if event.get("payload", {}).get("action") == "opened":
                    pull_requests += 1
            elif event_type == "IssuesEvent":
                if event.get("payload", {}).get("action") == "opened":
                    issues_opened += 1

        # Calculate language distribution
        language_counts: dict[str, int] = {}
        stars_received = 0
        for repo in repos:
            if not repo.get("fork"):
                lang = repo.get("language")
                if lang:
                    language_counts[lang] = language_counts.get(lang, 0) + 1
            stars_received += repo.get("stargazers_count", 0)

        # Sort languages by count
        top_languages = dict(
            sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Calculate contribution streak
        contribution_dates = [
            date.fromisoformat(d)
            for d, count in calendar.items()
            if count > 0
        ]
        current_streak, longest_streak = calculate_streak(contribution_dates)

        return {
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "total_commits": total_commits,
            "pull_requests": pull_requests,
            "issues_opened": issues_opened,
            "stars_received": stars_received,
            "forks": sum(r.get("forks_count", 0) for r in repos),
            "contribution_streak": current_streak,
            "longest_contribution_streak": longest_streak,
            "top_languages": json.dumps(top_languages),
            "contribution_calendar": json.dumps(calendar),
        }


# Singleton instance
github_service = GitHubService()
