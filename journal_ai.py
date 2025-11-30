"""Lightweight NLP helpers for journal suggestion extraction."""
from __future__ import annotations

import re
from typing import List

from models import JournalSuggestion

_KEYWORD_PATTERNS = {
    "goal": re.compile(
        r"\b(want to|goal|aspire|dream|become|vision|plan to|aim to|objective|target|would love)\b",
        re.IGNORECASE,
    ),
    "habit": re.compile(
        r"\b(habit|every day|routine|ritual|each morning|before bed|after I|whenever I)\b",
        re.IGNORECASE,
    ),
    "action": re.compile(
        r"\b(today|this week|tonight|right now|start|finish|send|draft|schedule|call|ship|email|publish)\b",
        re.IGNORECASE,
    ),
    "blockage": re.compile(
        r"\b(stuck|blocked|fear|worried|can't|overwhelmed|tired|burned out|anxious|procrastinat)\w*\b",
        re.IGNORECASE,
    ),
}


def extract_suggestions(entry_text: str) -> List[JournalSuggestion]:
    suggestions: List[JournalSuggestion] = []
    sentences = [chunk.strip() for chunk in re.split(r"[.!?]\s+", entry_text) if chunk.strip()]
    for sentence in sentences:
        matched_kind = _match_kind(sentence)
        if matched_kind:
            suggestions.append(JournalSuggestion(text=sentence, kind=matched_kind))
    return suggestions


def _match_kind(sentence: str) -> str | None:
    for kind, pattern in _KEYWORD_PATTERNS.items():
        if pattern.search(sentence):
            return kind
    return None
