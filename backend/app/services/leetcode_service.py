"""
LeetCode Service
Fetches data from LeetCode's unofficial GraphQL API with retry logic.
"""

import json
from datetime import date
from typing import Any, Optional

import httpx
from app.utils.helpers import calculate_streak

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "Origin": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (compatible; CodePulse/1.0)",
}

# GraphQL Queries
QUERY_USER_PROFILE = """
query userPublicProfile($username: String!) {
    matchedUser(username: $username) {
        username
        githubUrl
        profile {
            reputation
            ranking
        }
        submitStats: submitStatsGlobal {
            acSubmissionNum {
                difficulty
                count
                submissions
            }
        }
    }
    userContestRanking(username: $username) {
        attendedContestsCount
        rating
        globalRanking
        badge {
            name
        }
    }
}
"""

QUERY_SUBMISSION_CALENDAR = """
query userProfileCalendar($username: String!, $year: Int) {
    matchedUser(username: $username) {
        userCalendar(year: $year) {
            activeYears
            streak
            totalActiveDays
            dccBadges {
                timestamp
            }
            submissionCalendar
        }
    }
}
"""

QUERY_RECENT_SUBMISSIONS = """
query recentAcSubmissions($username: String!, $limit: Int!) {
    recentAcSubmissionList(username: $username, limit: $limit) {
        id
        title
        titleSlug
        timestamp
        statusDisplay
        lang
    }
}
"""


class LeetCodeService:
    """Service for fetching LeetCode data via GraphQL API"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=LEETCODE_HEADERS,
                follow_redirects=True,
            )
        return self._client

    async def _execute_query(
        self,
        query: str,
        variables: dict[str, Any],
        retries: int = 3,
    ) -> dict[str, Any]:
        """Execute a GraphQL query with retry logic."""
        client = await self._get_client()
        last_exc: Exception = RuntimeError("No attempts made")

        for attempt in range(retries):
            try:
                response = await client.post(
                    LEETCODE_GRAPHQL_URL,
                    json={"query": query, "variables": variables},
                )

                if response.status_code == 429:
                    # Rate limited — wait exponentially
                    wait = 2 ** attempt
                    await __import__("asyncio").sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    raise ValueError(f"GraphQL errors: {data['errors']}")

                return data.get("data", {})

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    await __import__("asyncio").sleep(2 ** attempt)
                continue
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                break

        raise RuntimeError(f"LeetCode API failed after {retries} attempts: {last_exc}")

    async def fetch_user_stats(self, username: str) -> dict[str, Any]:
        """
        Fetch complete LeetCode stats for a user.
        Returns parsed stats dict or raises RuntimeError.
        """
        # Fetch profile + contest ranking
        data = await self._execute_query(
            QUERY_USER_PROFILE, {"username": username}
        )

        matched_user = data.get("matchedUser")
        if not matched_user:
            raise ValueError(f"LeetCode user '{username}' not found")

        # Parse problem counts
        submit_stats = matched_user.get("submitStats", {}).get("acSubmissionNum", [])
        counts = {item["difficulty"]: item["count"] for item in submit_stats}

        # Contest data
        contest = data.get("userContestRanking") or {}

        # Fetch submission calendar (current year)
        current_year = date.today().year
        cal_data = await self._execute_query(
            QUERY_SUBMISSION_CALENDAR,
            {"username": username, "year": current_year},
        )
        calendar_info = (
            cal_data.get("matchedUser", {}).get("userCalendar", {}) or {}
        )
        submission_calendar_raw = calendar_info.get("submissionCalendar", "{}")

        # Also fetch previous year for streak accuracy
        prev_cal_data = await self._execute_query(
            QUERY_SUBMISSION_CALENDAR,
            {"username": username, "year": current_year - 1},
        )
        prev_calendar_info = (
            prev_cal_data.get("matchedUser", {}).get("userCalendar", {}) or {}
        )
        prev_cal_raw = prev_calendar_info.get("submissionCalendar", "{}")

        # Merge calendars
        merged_calendar = {
            **json.loads(prev_cal_raw or "{}"),
            **json.loads(submission_calendar_raw or "{}"),
        }

        # Calculate streaks from submission dates
        submission_dates = [
            date.fromtimestamp(int(ts))
            for ts in merged_calendar
            if merged_calendar[ts] > 0
        ]
        current_streak, longest_streak = calculate_streak(submission_dates)

        return {
            "username": matched_user["username"],
            "total_solved": counts.get("All", 0),
            "easy_solved": counts.get("Easy", 0),
            "medium_solved": counts.get("Medium", 0),
            "hard_solved": counts.get("Hard", 0),
            "reputation": matched_user.get("profile", {}).get("reputation", 0),
            "contest_rating": float(contest.get("rating", 0) or 0),
            "contest_global_rank": int(contest.get("globalRanking", 0) or 0),
            "contests_attended": int(contest.get("attendedContestsCount", 0) or 0),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "submission_calendar": json.dumps(merged_calendar),
        }

    async def fetch_recent_submissions(self, username: str, limit: int = 20) -> list[dict]:
        """Fetch recent accepted submissions."""
        data = await self._execute_query(
            QUERY_RECENT_SUBMISSIONS,
            {"username": username, "limit": limit},
        )
        return data.get("recentAcSubmissionList", []) or []

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
leetcode_service = LeetCodeService()
