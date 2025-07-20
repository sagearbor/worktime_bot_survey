"""Simple NLP utilities for parsing chatbot text input."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from ..app import load_config


class NLPProcessor:
    """Lightweight NLP processor for chatbot text."""

    def __init__(self, config_path: Path | str | None = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[3] / "config" / "dcri_config.json.example"
        self.config_path = Path(config_path)
        self.config = load_config(self.config_path)
        self.category_map = {
            a["category"].lower(): a["category"] for a in self.config.get("activities", [])
        }
        # Basic synonym map for common user terms
        self.synonyms = {
            "meetings": "Meeting",
            "meeting": "Meeting",
            "research": "Research",
            "analysis": "Analysis",
            "admin": "Administration",
            "administration": "Administration",
            "development": "Development",
            "project management": "Project Management",
            "project": "Project Management",
            "other": "Other",
        }

    def map_activity(self, name: str) -> str | None:
        name_lower = name.strip().lower()
        if name_lower in self.category_map:
            return self.category_map[name_lower]
        return self.synonyms.get(name_lower)

    def parse_time_allocation(self, text: str) -> Dict[str, float]:
        """Parse phrases like '60% meetings, 30% research' into a dict."""
        allocations: Dict[str, float] = {}
        pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%?\s*(?:of\s+)?([a-zA-Z ]+?)(?=,|and|$)", re.IGNORECASE)
        for value, activity_name in pattern.findall(text):
            category = self.map_activity(activity_name.strip())
            if category:
                allocations[category] = float(value)
        return allocations
