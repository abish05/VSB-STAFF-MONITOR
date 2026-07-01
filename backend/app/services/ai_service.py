"""
Gemini AI Analysis Service
Builds prompts and parses structured JSON responses from gemini-1.5-flash.
"""

import json
import logging
from typing import Any, Optional

import google.generativeai as genai
from app.config import settings
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

# Configure Gemini API
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# ─── Prompt Templates ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a senior technical mentor analyzing a student's coding profile.
Respond ONLY in valid JSON. No markdown, no explanation outside JSON.

JSON Schema:
{
  "summary": "2-3 sentence performance overview",
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2"],
  "recommendations": ["action1", "action2", "action3"],
  "placement_analysis": "1-2 sentence placement readiness comment",
  "weekly_goal": "One specific, actionable goal for next 7 days"
}
"""

DEPARTMENT_SYSTEM_PROMPT = """
You are an academic analytics expert reviewing a college department's coding performance.
Respond ONLY in valid JSON. No markdown, no explanation outside JSON.

JSON Schema:
{
  "overall_summary": "2-3 sentence department overview",
  "top_performers": ["student_name1", "student_name2", "student_name3"],
  "areas_of_concern": ["concern1", "concern2"],
  "department_recommendations": ["rec1", "rec2", "rec3"]
}
"""

GLOBAL_SYSTEM_PROMPT = """
You are a senior data analyst reviewing the overall coding performance across all students in the institution.
Focus heavily on the LeetCode problems solved and GitHub activity.
Respond ONLY in valid JSON. No markdown, no explanation outside JSON.

JSON Schema:
{
  "platform_summary": "3-4 sentences summarizing overall institution performance and engagement.",
  "top_students": ["student1", "student2", "student3"],
  "leetcode_analysis": "2-3 sentences analyzing LeetCode problem solving trends.",
  "github_analysis": "2-3 sentences analyzing GitHub contribution trends.",
  "strategic_recommendations": ["action1", "action2", "action3"]
}
"""


class AIService:
    """Service for Gemini AI-powered analysis"""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL
        self._model: Optional[Any] = None

    def _get_model(self):
        if self._model is None:
            if not settings.GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config=GenerationConfig(
                    temperature=0.3,  # Low temp for consistent structured output
                    response_mime_type="application/json",
                    max_output_tokens=1024,
                ),
            )
        return self._model

    def _build_user_prompt(
        self,
        name: str,
        dept: str,
        year: int,
        total_solved: int,
        easy: int,
        medium: int,
        hard: int,
        rating: float,
        streak: int,
        commits: int,
        prs: int,
        repos: int,
        contribution_streak: int,
        perf_score: float,
        classification: str,
        placement_score: float,
        placement_class: str,
    ) -> str:
        return f"""
Student: {name}, Dept: {dept}, Year: {year}
LeetCode: {total_solved} solved ({easy}E/{medium}M/{hard}H), Rating: {rating:.0f}, Streak: {streak} days
GitHub: {commits} commits, {prs} PRs, {repos} repos, {contribution_streak} day streak
Performance Score: {perf_score}/100 ({classification})
Placement Score: {placement_score}/100 ({placement_class})
"""

    async def analyze_user(
        self,
        name: str,
        dept: str,
        year: int,
        leetcode_stats: dict,
        github_stats: dict,
        perf_score: float,
        classification: str,
        placement_score: float,
        placement_class: str,
    ) -> dict[str, Any]:
        """
        Generate AI analysis for a single user.
        Returns parsed JSON response or raises RuntimeError.
        """
        model = self._get_model()

        user_prompt = self._build_user_prompt(
            name=name,
            dept=dept,
            year=year,
            total_solved=leetcode_stats.get("total_solved", 0),
            easy=leetcode_stats.get("easy_solved", 0),
            medium=leetcode_stats.get("medium_solved", 0),
            hard=leetcode_stats.get("hard_solved", 0),
            rating=leetcode_stats.get("contest_rating", 0),
            streak=leetcode_stats.get("current_streak", 0),
            commits=github_stats.get("total_commits", 0),
            prs=github_stats.get("pull_requests", 0),
            repos=github_stats.get("public_repos", 0),
            contribution_streak=github_stats.get("contribution_streak", 0),
            perf_score=perf_score,
            classification=classification,
            placement_score=placement_score,
            placement_class=placement_class,
        )

        try:
            response = await model.generate_content_async(user_prompt)
            raw_text = response.text.strip()

            # Parse JSON response
            parsed = json.loads(raw_text)

            # Validate required fields
            required_fields = [
                "summary", "strengths", "weaknesses",
                "recommendations", "placement_analysis", "weekly_goal"
            ]
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = "" if isinstance(parsed.get(field), str) else []

            return parsed

        except json.JSONDecodeError as exc:
            logger.error(f"Gemini returned invalid JSON: {exc}")
            return self._fallback_analysis(perf_score, placement_score, classification)
        except Exception as exc:
            logger.error(f"Gemini API error: {exc}")
            raise RuntimeError(f"AI analysis failed: {exc}") from exc

    async def analyze_department(
        self,
        dept_name: str,
        avg_score: float,
        top_performers: list[str],
        student_count: int,
        active_count: int,
        avg_problems: float,
        avg_commits: float,
    ) -> dict[str, Any]:
        """Generate department-level AI summary."""
        model_dept = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=DEPARTMENT_SYSTEM_PROMPT,
            generation_config=GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
                max_output_tokens=512,
            ),
        )

        prompt = f"""
Department: {dept_name}
Total Students: {student_count} (Active: {active_count})
Average Score: {avg_score:.1f}/100
Average Problems Solved: {avg_problems:.0f}
Average Commits: {avg_commits:.0f}
Top Performers: {', '.join(top_performers[:5]) if top_performers else 'None yet'}
"""
        try:
            response = await model_dept.generate_content_async(prompt)
            return json.loads(response.text.strip())
        except Exception as exc:
            logger.error(f"Department AI analysis failed: {exc}")
            return {
                "overall_summary": f"{dept_name} department performance analysis unavailable.",
                "top_performers": top_performers[:3],
                "areas_of_concern": ["Detailed analysis unavailable"],
                "department_recommendations": ["Continue monitoring student progress"],
            }

    async def analyze_global(
        self,
        total_students: int,
        avg_score: float,
        top_performers: list[str],
        avg_problems: float,
        avg_commits: float,
        total_problems_solved: int,
        total_github_commits: int,
    ) -> dict[str, Any]:
        """Generate institution-level global AI summary."""
        model_global = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=GLOBAL_SYSTEM_PROMPT,
            generation_config=GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
                max_output_tokens=700,
            ),
        )

        prompt = f"""
Institution Overview:
Total Students Tracked: {total_students}
Overall Average Performance Score: {avg_score:.1f}/100
Total LeetCode Problems Solved: {total_problems_solved} (Avg: {avg_problems:.1f} per student)
Total GitHub Commits: {total_github_commits} (Avg: {avg_commits:.1f} per student)
Top Performers: {', '.join(top_performers[:10]) if top_performers else 'None yet'}
"""
        try:
            response = await model_global.generate_content_async(prompt)
            return json.loads(response.text.strip())
        except Exception as exc:
            logger.error(f"Global AI analysis failed: {exc}")
            return {
                "platform_summary": "Institution global performance analysis unavailable.",
                "top_students": top_performers[:3],
                "leetcode_analysis": "Detailed analysis unavailable",
                "github_analysis": "Detailed analysis unavailable",
                "strategic_recommendations": ["Continue monitoring student progress"],
            }

    def _fallback_analysis(
        self, perf_score: float, placement_score: float, classification: str
    ) -> dict[str, Any]:
        """Return a basic analysis when Gemini is unavailable."""
        return {
            "summary": f"Student performance is classified as '{classification}' with a score of {perf_score:.1f}/100.",
            "strengths": ["Regular coding activity detected"],
            "weaknesses": ["Detailed analysis currently unavailable"],
            "recommendations": [
                "Continue solving LeetCode problems daily",
                "Contribute to open-source projects on GitHub",
                "Practice contest problems to improve rating",
            ],
            "placement_analysis": f"Placement readiness score: {placement_score:.1f}/100.",
            "weekly_goal": "Solve at least 7 LeetCode problems this week (1 per day).",
        }


# Singleton
ai_service = AIService()
