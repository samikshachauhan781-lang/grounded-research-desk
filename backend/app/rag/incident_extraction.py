"""Structured field extraction from incident-style markdown documents."""

from __future__ import annotations

import re

from backend.app.rag.question_intent import parse_time_range_minutes

_SECTION = re.compile(
    r"(?:^|\n)#{1,3}\s*(?P<title>[^\n]+)\s*\n+(?P<body>.*?)(?=\n#{1,3}\s|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_TIME_EVENT = re.compile(
    r"^\s*[-*]\s*(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[—\-–]\s*(?P<event>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_LABEL_LINE = re.compile(
    r"^\s*(?P<label>[A-Za-z][\w\s]{0,40}?)\s*:\s*(?P<value>.+?)\s*$",
    re.MULTILINE,
)


def _section_body(text: str, title_fragment: str) -> str | None:
    fragment = title_fragment.lower()
    for match in _SECTION.finditer(text):
        title = match.group("title").strip().lower()
        if fragment in title:
            return match.group("body").strip()
    return None


def _first_substantive_line(body: str, min_len: int = 20) -> str | None:
    for raw in body.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        if line.startswith("- ") or line.startswith("* "):
            continue
        if len(line) >= min_len:
            return line
    return None


def extract_root_cause(text: str) -> str | None:
    body = _section_body(text, "root cause")
    if body:
        line = _first_substantive_line(body)
        if line:
            return line

    for match in _LABEL_LINE.finditer(text):
        if match.group("label").strip().lower() == "root cause":
            return match.group("value").strip()
    return None


def extract_resolution(text: str) -> str | None:
    body = _section_body(text, "resolution")
    if body:
        line = _first_substantive_line(body)
        if line:
            return line

    for match in _LABEL_LINE.finditer(text):
        label = match.group("label").strip().lower()
        if label in {"resolution", "remediation", "recovery"}:
            return match.group("value").strip()
    return None


def _parse_event_time_minutes(time_str: str) -> int | None:
    from backend.app.rag.question_intent import _parse_clock_to_minutes

    return _parse_clock_to_minutes(time_str.strip())


def extract_timeline_events(text: str) -> list[tuple[int, str, str]]:
    """Return (sort_key_minutes, display_time, description) sorted chronologically."""
    events: list[tuple[int, str, str]] = []
    body = _section_body(text, "timeline")
    search_text = body if body else text
    for match in _TIME_EVENT.finditer(search_text):
        display_time = match.group("time").strip()
        event = match.group("event").strip()
        minutes = _parse_event_time_minutes(display_time)
        if minutes is None:
            continue
        events.append((minutes, display_time, event))
    events.sort(key=lambda item: item[0])
    return events


def format_timeline_answer(events: list[tuple[int, str, str]]) -> str:
    lines = [f"- {display} — {desc}" for _, display, desc in events]
    return "\n".join(lines)


def timeline_events_for_question(
    text: str,
    question: str,
) -> list[tuple[int, str, str]]:
    """In-range timeline events from one chunk (empty when none match the question)."""
    events = extract_timeline_events(text)
    if not events:
        return []
    start, end = parse_time_range_minutes(question)
    if start is not None and end is not None:
        events = [event for event in events if start <= event[0] <= end]
    return events


def extract_timeline_for_question(text: str, question: str) -> str | None:
    events = timeline_events_for_question(text, question)
    if not events:
        return None
    return format_timeline_answer(events)


def extract_metadata_value(text: str, field: str) -> str | None:
    if field == "sensitive_missing":
        return None

    label_map = {
        "incident_id": ("incident id",),
        "service": ("service",),
        "severity": ("severity",),
        "date": ("date", "incident date"),
    }
    labels = label_map.get(field, ())
    for match in _LABEL_LINE.finditer(text):
        label = match.group("label").strip().lower()
        if any(label == target or label.startswith(target) for target in labels):
            return match.group("value").strip()
    return None


def format_metadata_answer(field: str, value: str) -> str:
    if field == "incident_id":
        return f"The incident ID is {value}."
    if field == "service":
        return f"The service is {value}."
    if field == "severity":
        return f"The severity is {value}."
    if field == "date":
        return f"The date is {value}."
    return value if value.endswith(".") else f"{value}."
