"""Domain models for the Action Menu prototype."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List
import uuid


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _dt_to_str(value: datetime) -> str:
    return value.strftime(ISO_FORMAT)


def _dt_from_str(value: str) -> datetime:
    return datetime.strptime(value, ISO_FORMAT)


def _uuid() -> str:
    return uuid.uuid4().hex


@dataclass
class SmartGoal:
    id: str
    title: str
    specific: str = ""
    measurable: str = ""
    achievable: str = ""
    relevant: str = ""
    time_bound: str = ""
    horizon: str = "Long Term"
    category: str = "General"
    calendar_color: str = "default"

    @classmethod
    def new(
        cls,
        title: str,
        *,
        specific: str = "",
        measurable: str = "",
        achievable: str = "",
        relevant: str = "",
        time_bound: str = "",
        horizon: str = "Long Term",
        category: str = "General",
        calendar_color: str = "default",
    ) -> "SmartGoal":
        return cls(
            id=_uuid(),
            title=title,
            specific=specific,
            measurable=measurable,
            achievable=achievable,
            relevant=relevant,
            time_bound=time_bound,
            horizon=horizon,
            category=category,
            calendar_color=calendar_color,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmartGoal":
        return cls(**data)


@dataclass
class HabitPlan:
    id: str
    name: str
    anchor: str
    frequency: str
    success_metric: str
    linked_goal: str

    @classmethod
    def new(
        cls,
        name: str,
        *,
        anchor: str = "",
        frequency: str = "",
        success_metric: str = "",
        linked_goal: str = "",
    ) -> "HabitPlan":
        return cls(
            id=_uuid(),
            name=name,
            anchor=anchor,
            frequency=frequency,
            success_metric=success_metric,
            linked_goal=linked_goal,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HabitPlan":
        return cls(**data)


@dataclass
class TimeEntry:
    id: str
    activity: str
    category: str
    start: datetime
    end: datetime
    calendar_color: str = "default"

    @property
    def duration_hours(self) -> float:
        return round((self.end - self.start).total_seconds() / 3600, 2)

    @classmethod
    def new(
        cls,
        activity: str,
        *,
        category: str,
        start: datetime,
        end: datetime,
        calendar_color: str = "default",
    ) -> "TimeEntry":
        return cls(
            id=_uuid(),
            activity=activity,
            category=category,
            start=start,
            end=end,
            calendar_color=calendar_color,
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["start"] = _dt_to_str(self.start)
        data["end"] = _dt_to_str(self.end)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeEntry":
        data = dict(data)
        data["start"] = _dt_from_str(data["start"])
        data["end"] = _dt_from_str(data["end"])
        return cls(**data)


@dataclass
class FlowLog:
    id: str
    time_entry_id: str
    flow_before: int
    flow_after: int
    emotion_before: str
    emotion_after: str
    feeling_message: str
    feeling_motivation: str
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        time_entry_id: str,
        flow_before: int,
        flow_after: int,
        emotion_before: str,
        emotion_after: str,
        feeling_message: str,
        feeling_motivation: str,
    ) -> "FlowLog":
        return cls(
            id=_uuid(),
            time_entry_id=time_entry_id,
            flow_before=flow_before,
            flow_after=flow_after,
            emotion_before=emotion_before,
            emotion_after=emotion_after,
            feeling_message=feeling_message,
            feeling_motivation=feeling_motivation,
            created_at=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = _dt_to_str(self.created_at)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowLog":
        data = dict(data)
        data["created_at"] = _dt_from_str(data["created_at"])
        return cls(**data)


@dataclass
class JournalSuggestion:
    text: str
    kind: str  # goal | habit | action | blockage

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalSuggestion":
        return cls(**data)


@dataclass
class JournalEntry:
    id: str
    created_at: datetime
    text: str
    tags: List[str] = field(default_factory=list)
    suggestions: List[JournalSuggestion] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        text: str,
        *,
        tags: List[str],
        suggestions: List[JournalSuggestion],
    ) -> "JournalEntry":
        return cls(
            id=_uuid(),
            created_at=datetime.utcnow(),
            text=text,
            tags=tags,
            suggestions=suggestions,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": _dt_to_str(self.created_at),
            "text": self.text,
            "tags": self.tags,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalEntry":
        return cls(
            id=data["id"],
            created_at=_dt_from_str(data["created_at"]),
            text=data["text"],
            tags=data.get("tags", []),
            suggestions=[JournalSuggestion.from_dict(s) for s in data.get("suggestions", [])],
        )


@dataclass
class QuickCaptureItem:
    id: str
    text: str
    status: str  # Inbox | Today | Later | Archived
    created_at: datetime

    @classmethod
    def new(cls, text: str, status: str = "Inbox") -> "QuickCaptureItem":
        return cls(id=_uuid(), text=text, status=status, created_at=datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "status": self.status,
            "created_at": _dt_to_str(self.created_at),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuickCaptureItem":
        return cls(
            id=data["id"],
            text=data["text"],
            status=data["status"],
            created_at=_dt_from_str(data["created_at"]),
        )


@dataclass
class Reflections:
    values: str = ""
    milestones: str = ""
    energy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reflections":
        return cls(**data)


@dataclass
class AppState:
    reflections: Reflections = field(default_factory=Reflections)
    goals: List[SmartGoal] = field(default_factory=list)
    habits: List[HabitPlan] = field(default_factory=list)
    weekly_actions: Dict[str, List[str]] = field(
        default_factory=lambda: {"Today": [], "This Week": [], "This Month": []}
    )
    timer_categories: List[str] = field(
        default_factory=lambda: ["Creative", "Learning", "Working", "Body", "Recovery"]
    )
    time_entries: List[TimeEntry] = field(default_factory=list)
    flow_logs: List[FlowLog] = field(default_factory=list)
    journal_entries: List[JournalEntry] = field(default_factory=list)
    quick_capture: List[QuickCaptureItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflections": self.reflections.to_dict(),
            "goals": [g.to_dict() for g in self.goals],
            "habits": [h.to_dict() for h in self.habits],
            "weekly_actions": self.weekly_actions,
            "timer_categories": self.timer_categories,
            "time_entries": [t.to_dict() for t in self.time_entries],
            "flow_logs": [f.to_dict() for f in self.flow_logs],
            "journal_entries": [j.to_dict() for j in self.journal_entries],
            "quick_capture": [q.to_dict() for q in self.quick_capture],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppState":
        return cls(
            reflections=Reflections.from_dict(data.get("reflections", {})),
            goals=[SmartGoal.from_dict(item) for item in data.get("goals", [])],
            habits=[HabitPlan.from_dict(item) for item in data.get("habits", [])],
            weekly_actions=data.get(
                "weekly_actions", {"Today": [], "This Week": [], "This Month": []}
            ),
            timer_categories=data.get(
                "timer_categories", ["Creative", "Learning", "Working", "Body", "Recovery"]
            ),
            time_entries=[TimeEntry.from_dict(item) for item in data.get("time_entries", [])],
            flow_logs=[FlowLog.from_dict(item) for item in data.get("flow_logs", [])],
            journal_entries=[JournalEntry.from_dict(item) for item in data.get("journal_entries", [])],
            quick_capture=[QuickCaptureItem.from_dict(item) for item in data.get("quick_capture", [])],
        )