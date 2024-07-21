import json
from typing import Any, Dict

import requests
from fastapi import APIRouter, HTTPException, Path
from fastapi.params import Depends

from app.models import StatsResponse

router = APIRouter()


class StatsService:
    GRAPHQL_URL = "https://leetcode.com/graphql/"

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def get_stats(self, username: str) -> StatsResponse:
        query = self._build_query(username)
        try:
            response = requests.post(self.GRAPHQL_URL, headers=self.headers, json=query)
            response.raise_for_status()
            return self._process_response(response.json())
        except requests.RequestException as e:
            return StatsResponse.error(f"Request failed: {str(e)}")
        except json.JSONDecodeError:
            return StatsResponse.error("Failed to decode JSON response")
        except Exception as e:
            return StatsResponse.error(f"An unexpected error occurred: {str(e)}")

    def _build_query(self, username: str) -> Dict[str, Any]:
        return {
            "query": """
                query getUserProfile($username: String!) {
                    allQuestionsCount { difficulty count }
                    matchedUser(username: $username) {
                        contributions { points }
                        profile { reputation ranking }
                        submissionCalendar
                        submitStats {
                            acSubmissionNum { difficulty count submissions }
                            totalSubmissionNum { difficulty count submissions }
                        }
                    }
                }
            """,
            "variables": {"username": username},
        }

    def _process_response(self, response_data: Dict[str, Any]) -> StatsResponse:
        try:
            data = response_data.get("data", {})
            all_questions = data.get("allQuestionsCount", [])
            matched_user = data.get("matchedUser", {})
            submit_stats = matched_user.get("submitStats", {})
            actual_submissions = submit_stats.get("acSubmissionNum", [])
            total_submissions = submit_stats.get("totalSubmissionNum", [])

            total_questions = self._sum_question_counts(all_questions)
            total_easy = self._get_question_count(all_questions, "Easy")
            total_medium = self._get_question_count(all_questions, "Medium")
            total_hard = self._get_question_count(all_questions, "Hard")

            easy_solved = self._get_submission_count(actual_submissions, "Easy")
            medium_solved = self._get_submission_count(actual_submissions, "Medium")
            hard_solved = self._get_submission_count(actual_submissions, "Hard")
            total_solved = easy_solved + medium_solved + hard_solved

            total_accept_count = self._get_submission_stat(
                actual_submissions, "Easy", "submissions"
            )
            total_sub_count = self._get_submission_stat(
                total_submissions, "Easy", "submissions"
            )
            acceptance_rate = self._calculate_acceptance_rate(
                total_accept_count, total_sub_count
            )

            contribution_points = matched_user.get("contributions", {}).get("points", 0)
            reputation = matched_user.get("profile", {}).get("reputation", 0)
            ranking = matched_user.get("profile", {}).get("ranking", 0)

            submission_calendar = self._parse_submission_calendar(
                matched_user.get("submissionCalendar", "{}")
            )

            return StatsResponse.success(
                "retrieved",
                total_solved=total_solved,
                total_questions=total_questions,
                easy_solved=easy_solved,
                total_easy=total_easy,
                medium_solved=medium_solved,
                total_medium=total_medium,
                hard_solved=hard_solved,
                total_hard=total_hard,
                acceptance_rate=acceptance_rate,
                ranking=ranking,
                contribution_points=contribution_points,
                reputation=reputation,
                submission_calendar=submission_calendar,
            )
        except KeyError as e:
            return StatsResponse.error(f"Missing key in response: {str(e)}")
        except (TypeError, ValueError) as e:
            return StatsResponse.error(f"Data processing error: {str(e)}")

    def _sum_question_counts(self, questions: list) -> int:
        return sum(q.get("count", 0) for q in questions)

    def _sum_submission_counts(self, submissions: list) -> int:
        return sum(sub.get("count", 0) for sub in submissions)

    def _get_question_count(self, questions: list, difficulty: str) -> int:
        return next(
            (q.get("count", 0) for q in questions if q.get("difficulty") == difficulty),
            0,
        )

    def _get_submission_count(self, submissions: list, difficulty: str) -> int:
        return next(
            (
                sub.get("count", 0)
                for sub in submissions
                if sub.get("difficulty") == difficulty
            ),
            0,
        )

    def _get_submission_stat(
        self, submissions: list, difficulty: str, stat: str
    ) -> int:
        return next(
            (
                sub.get(stat, 0)
                for sub in submissions
                if sub.get("difficulty") == difficulty
            ),
            0,
        )

    def _calculate_acceptance_rate(self, accept_count: int, total_count: int) -> float:
        return (
            self._round((accept_count / total_count) * 100, 2)
            if total_count != 0
            else 0
        )

    def _parse_submission_calendar(self, calendar_str: str) -> Dict[str, int]:
        try:
            calendar = json.loads(calendar_str)
            return dict(sorted(calendar.items()))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _round(value: float, decimal_place: int) -> float:
        return round(value, decimal_place)


@router.get("/{username}")
def get_statistic(
    username: str = Path(
        ..., description="The username of the user whose statistics are to be retrieved"
    ),
    stats_service: StatsService = Depends(StatsService),
):
    if not username:
        raise HTTPException(status_code=400, detail="Username parameter is required")

    stats = stats_service.get_stats(username)

    if stats.status == "success":
        return stats
    else:
        raise HTTPException(status_code=500, detail=stats.message)
