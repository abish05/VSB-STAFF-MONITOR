"""
Scoring Service
Implements the exact performance + placement score formulas from spec.
"""

from dataclasses import dataclass


# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class LeetCodeInput:
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    contest_rating: float
    current_streak: int


@dataclass
class GitHubInput:
    total_commits: int
    pull_requests: int
    public_repos: int
    stars_received: int
    contribution_streak: int
    issues_opened: int


# ─── Performance Score ────────────────────────────────────────────────────────
def calculate_performance_score(
    leetcode: LeetCodeInput,
    github: GitHubInput,
) -> tuple[float, float, float, str]:
    """
    Calculate performance score using the exact spec formula.

    Returns:
        (leetcode_score, github_score, total_score, classification)
    """
    # Normalize each dimension to 0-100
    problems_norm = min(leetcode.total_solved / 500 * 100, 100)
    rating_norm = max(
        min((leetcode.contest_rating - 1200) / 1400 * 100, 100), 0
    )
    commits_norm = min(github.total_commits / 365 * 100, 100)
    pr_norm = min(github.pull_requests / 50 * 100, 100)
    streak_norm = min(leetcode.current_streak / 100 * 100, 100)

    # Weighted score
    total_score = (
        problems_norm * 0.40
        + rating_norm * 0.20
        + commits_norm * 0.20
        + pr_norm * 0.10
        + streak_norm * 0.10
    )
    total_score = round(min(max(total_score, 0), 100), 2)

    # Sub-scores for reporting
    leetcode_score = round(
        (problems_norm * 0.60 + rating_norm * 0.20 + streak_norm * 0.20), 2
    )
    github_score = round(
        (commits_norm * 0.60 + pr_norm * 0.40), 2
    )

    classification = classify_performance(total_score)
    return leetcode_score, github_score, total_score, classification


def classify_performance(score: float) -> str:
    """Return performance classification string."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    else:
        return "Needs Improvement"


# ─── Placement Score ──────────────────────────────────────────────────────────
def calculate_placement_score(
    leetcode: LeetCodeInput,
    github: GitHubInput,
) -> tuple[float, str]:
    """
    Calculate placement readiness score using exact spec formula.

    Returns:
        (placement_score, placement_classification)
    """
    # Coding skills (LC problems with difficulty weighting)
    weighted_problems = (
        leetcode.easy_solved * 1
        + leetcode.medium_solved * 2
        + leetcode.hard_solved * 4
    )
    coding_skills = min(weighted_problems / 800 * 100, 100)

    # Open source contribution
    open_source = min(
        (github.pull_requests / 20 * 50 + github.issues_opened / 30 * 30 + min(github.public_repos, 10) / 10 * 20),
        100,
    )

    # Contest rating
    contest_rating = max(
        min((leetcode.contest_rating - 1200) / 1400 * 100, 100), 0
    )

    # Consistency (streak + activity days)
    consistency = min(
        leetcode.current_streak / 60 * 60 + github.contribution_streak / 30 * 40,
        100,
    )

    # Project quality (stars + repos)
    project_quality = min(
        github.stars_received / 30 * 70 + min(github.public_repos, 10) / 10 * 30,
        100,
    )

    # Weighted placement score
    placement_score = (
        coding_skills * 0.35
        + open_source * 0.20
        + contest_rating * 0.20
        + consistency * 0.15
        + project_quality * 0.10
    )
    placement_score = round(min(max(placement_score, 0), 100), 2)
    classification = classify_placement(placement_score)

    return placement_score, classification


def classify_placement(score: float) -> str:
    """Return placement readiness classification string."""
    if score >= 75:
        return "Placement Ready"
    elif score >= 50:
        return "Industry Ready"
    else:
        return "Needs Improvement"


# ─── Score Breakdown ──────────────────────────────────────────────────────────
def get_score_breakdown(
    leetcode: LeetCodeInput,
    github: GitHubInput,
) -> dict:
    """Return detailed breakdown of score components for UI display."""
    problems_norm = min(leetcode.total_solved / 500 * 100, 100)
    rating_norm = max(min((leetcode.contest_rating - 1200) / 1400 * 100, 100), 0)
    commits_norm = min(github.total_commits / 365 * 100, 100)
    pr_norm = min(github.pull_requests / 50 * 100, 100)
    streak_norm = min(leetcode.current_streak / 100 * 100, 100)

    return {
        "problems_normalized": round(problems_norm, 1),
        "rating_normalized": round(rating_norm, 1),
        "commits_normalized": round(commits_norm, 1),
        "pr_normalized": round(pr_norm, 1),
        "streak_normalized": round(streak_norm, 1),
    }
