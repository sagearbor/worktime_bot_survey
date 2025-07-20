"""AI-powered solution suggestion and ROI calculation utilities."""

from __future__ import annotations

import os
from typing import List, Iterable


class SolutionEngine:
    """Generate solution suggestions using OpenAI or fallback heuristics."""

    def __init__(
        self, api_key: str | None = None, model: str = "gpt-3.5-turbo"
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def suggest(self, problem_description: str, max_suggestions: int = 3) -> List[str]:
        """Return a list of solution suggestions."""
        if self.api_key:
            try:
                import openai

                openai.api_key = self.api_key
                prompt = (
                    "Provide concise solutions for the following problem:\n"
                    + problem_description
                )
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256,
                )
                text = response.choices[0].message.content
                suggestions = [s.strip("- ") for s in text.split("\n") if s.strip()]
                return suggestions[:max_suggestions]
            except Exception as exc:  # pragma: no cover - network issues
                print(f"OpenAI request failed: {exc}")
        # Fallback heuristic suggestions
        return self._fallback_suggestions(problem_description, max_suggestions)

    @staticmethod
    def _fallback_suggestions(
        problem_description: str, max_suggestions: int
    ) -> List[str]:
        base = [
            "Review logs and error messages",
            "Consult documentation or experts",
            "Consider process automation",
            "Improve user training",
        ]
        return base[:max_suggestions]


def estimate_effort(description: str) -> str:
    """Roughly estimate effort based on description length."""
    word_count = len(description.split())
    if word_count < 10:
        return "Low"
    if word_count < 25:
        return "Medium"
    return "High"


def calculate_roi(
    estimated_savings: float, effort: str, people_affected: int = 1
) -> float:
    """Calculate ROI score given savings, effort level, and people affected."""
    effort_map = {"Low": 1.0, "Medium": 2.0, "High": 3.0}
    effort_cost = effort_map.get(effort, 1.0)
    if effort_cost == 0:
        return 0.0
    return (estimated_savings * people_affected) / effort_cost


def prioritize_solutions(solutions: Iterable) -> List:
    """Return solutions sorted by ROI score descending."""
    return sorted(solutions, key=lambda s: (s.roi_score or 0), reverse=True)
