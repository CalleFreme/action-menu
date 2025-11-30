"""Shared UI constants for Action Menu."""
from __future__ import annotations

from typing import Dict, List

CATEGORY_OPTIONS: List[str] = ["General", "Creative", "Startup", "Learning", "Body", "Recovery"]
CATEGORY_COLORS: Dict[str, str] = {
    "General": "#7a7a7a",
    "Creative": "#ee8130",
    "Startup": "#0078d4",
    "Learning": "#7357ff",
    "Body": "#2e8b57",
    "Recovery": "#c55bff",
}
EMOTIONS: List[str] = [
    "Calm",
    "Curious",
    "Confident",
    "Energized",
    "Bored",
    "Anxious",
    "Tired",
    "Stuck",
    "Excited",
]
DEFAULT_TIMER_CATEGORIES: List[str] = ["Creative", "Learning", "Working", "Body", "Recovery"]
GOAL_FIELD_SAMPLES: Dict[str, str] = {
    "title": "Ship Unreal networking demo",
    "specific": "Implement replication + lag compensation for co-op prototype",
    "measurable": "Playable session with <80ms latency spikes",
    "achievable": "Reuse existing engine scaffolding + Epic docs",
    "relevant": "Supports CTO vision + teaching curriculum",
    "time_bound": "Beta-ready by March 30",
}
HABIT_FIELD_SAMPLES: Dict[str, str] = {
    "name": "Post-lunch bug triage walk",
    "anchor": "Right after standup",
    "frequency": "Weekdays",
    "success_metric": "Close 2 issues / day",
}
ACTION_SAMPLE = "Pitch co-op boss fight concept (ties to Unreal goal)"
TIMER_ACTIVITY_SAMPLE = "Deep work: refactor rendering pipeline"
QUICK_ENTRY_SAMPLE = "Draft lesson on async Rust + plan gym session"
