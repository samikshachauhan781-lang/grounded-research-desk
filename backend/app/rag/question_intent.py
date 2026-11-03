"""Question intent detection for deterministic answer synthesis."""

from __future__ import annotations

import re
from enum import Enum


class QuestionIntent(str, Enum):
    FILE = "file"
    COMMAND = "command"
    ROOT_CAUSE = "root_cause"
    RESOLUTION = "resolution"
    TIMELINE = "timeline"
    METADATA = "metadata"
    GENERAL = "general"


def _q_lower(question: str) -> str:
    return question.lower().strip()


def asks_for_file(question: str) -> bool:
    q = _q_lower(question)
    return any(
        phrase in q
        for phrase in (
            "which file",
            "what file",
            "file contains",
            "file has",
            "filename",
        )
    )


def asks_for_multiple_files(question: str) -> bool:
    q = _q_lower(question)
    if "which files" in q or "what files" in q:
        return True
    if re.search(r"\bfiles\b", q) and re.search(r"\b(both|all|list|name)\b", q):
        return True
    if asks_for_file(question) and re.search(r"\bfiles\b", q):
        return True
    return False


def asks_for_file_attributes(question: str) -> bool:
    q = _q_lower(question)
    if "file" not in q and "files" not in q:
        return False
    return any(
        phrase in q
        for phrase in (
            "line count",
            "line counts",
            "responsibilit",
            "with their line",
            "with their lines",
            "purpose",
        )
    ) or (re.search(r"\blines?\b", q) and re.search(r"\b(responsibilit|purpose|contain)\b", q))


def asks_for_directory_overview(question: str) -> bool:
    q = _q_lower(question)
    if asks_for_command(question) or asks_for_multiple_files(question):
        return False
    if asks_for_file_attributes(question):
        return False
    if asks_for_development_status(question):
        return False
    if "directory" in q and any(word in q for word in ("about", "explain", "describe")):
        return True
    if "project" in q and "about" in q:
        return True
    return False


def asks_for_development_status(question: str) -> bool:
    """True when the question asks for project/development/implementation status or progress."""
    q = _q_lower(question)
    if re.search(r"\bdevelopment\s+status\b", q):
        return True
    if re.search(r"\bproject\s+status\b", q):
        return True
    if re.search(r"\bimplementation\s+status\b", q):
        return True
    if re.search(r"\b(?:reported|current)\b", q) and re.search(r"\bstatus\b", q):
        return True
    if re.search(r"\bstatus\s+of\s+(?:the\s+)?project\b", q):
        return True
    if re.search(r"\bimplementation\s+progress\b", q):
        return True
    if re.search(r"\bprogress\s+of\s+(?:the\s+)?(?:project|implementation)\b", q):
        return True
    return False


def multi_file_inventory_applies(question: str) -> bool:
    if asks_for_multiple_files(question):
        return True
    return asks_for_file_attributes(question) and re.search(
        r"\b(both|all|list)\b",
        question.lower(),
    )


_RESOLUTION_OUTCOME = ("resolved", "fixed", "restored", "recovered")


def _asks_resolution_outcome(question: str) -> bool:
    """True when the question asks how/why an incident was fixed or restored (not root cause)."""
    q = _q_lower(question)
    if any(
        phrase in q
        for phrase in (
            "how was the incident resolved",
            "how was it resolved",
            "how was the issue resolved",
            "how was the problem resolved",
            "how was this resolved",
            "how was it fixed",
            "how was the issue fixed",
            "how was the incident fixed",
            "what action restored",
            "how was the service restored",
        )
    ):
        return True
    if ("how was" in q or "how were" in q) and any(w in q for w in _RESOLUTION_OUTCOME):
        return True
    if re.search(r"\bwhy\s+(?:was|were)\b", q) and any(w in q for w in _RESOLUTION_OUTCOME):
        return True
    return False


def _seeks_prohibited_secret(question: str) -> bool:
    """True when the user asks to reveal passwords, keys, tokens, or live credentials."""
    q = _q_lower(question)
    if re.search(r"\bpassword\b", q):
        return True
    if re.search(r"\bapi key\b", q):
        return True
    if re.search(r"\btoken\b", q) and re.search(
        r"\b(?:what|show|reveal|give|tell|share)\b",
        q,
    ):
        return True
    if re.search(r"\bsecret\b", q):
        if re.search(
            r"\bsecrets?\s+(?:rotation|management|policy|storage|scanning|vault)\b",
            q,
        ):
            return False
        if re.search(r"\b(?:rotation|management|policy)\s+(?:for|of)\s+secrets?\b", q):
            return False
        return True
    if re.search(r"\bcredentials?\b", q):
        if re.search(
            r"\bcredentials?\s+(?:rotation|management|policy|lifecycle|storage)\b",
            q,
        ) or re.search(
            r"\b(?:rotation|management|policy)\s+(?:for|of)\s+credentials?\b",
            q,
        ):
            return False
        if re.search(
            r"\b(?:what|show|reveal|give|tell)\s+(?:me\s+)?(?:the\s+)?(?:actual\s+)?credentials?\b",
            q,
        ):
            return True
        if re.search(r"\bcredentials?\s+(?:is|was|are|were)\b", q):
            return True
    return False


def asks_for_command(question: str) -> bool:
    q = _q_lower(question)
    if re.search(r"\bcommands?\b", q):
        return True
    return any(
        phrase in q
        for phrase in (
            "run ",
            "execute",
            "how do i",
            "how to",
            "what do i run",
        )
    )


def detect_question_intent(question: str) -> QuestionIntent:
    q = _q_lower(question)
    if asks_for_file(question):
        return QuestionIntent.FILE
    if asks_for_command(question):
        return QuestionIntent.COMMAND

    if _asks_resolution_outcome(question):
        return QuestionIntent.RESOLUTION

    if any(
        phrase in q
        for phrase in (
            "root cause",
            "what caused",
            "what was the cause",
            "why did the",
            "why did ",
            "why was the",
            "why was ",
            "what led to",
        )
    ):
        return QuestionIntent.ROOT_CAUSE

    if any(
        phrase in q
        for phrase in (
            "timeline",
            "what happened between",
            "what happened after",
            "sequence of events",
            "chronological",
        )
    ) or re.search(r"between\s+\d{1,2}:\d{2}", q):
        return QuestionIntent.TIMELINE

    if detect_metadata_field(question) is not None:
        return QuestionIntent.METADATA

    return QuestionIntent.GENERAL


def detect_metadata_field(question: str) -> str | None:
    """Return logical field key requested by the question, if any."""
    q = _q_lower(question)
    if "incident id" in q or "incident identifier" in q:
        return "incident_id"
    if "service name" in q or "which service" in q or q.startswith("what service"):
        return "service"
    if "severity" in q:
        return "severity"
    if "date" in q and ("incident" in q or "when" in q):
        return "date"
    if _seeks_prohibited_secret(question):
        return "sensitive_missing"
    return None


_TIME_RANGE = re.compile(
    r"between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
    re.IGNORECASE,
)


def parse_time_range_minutes(question: str) -> tuple[int | None, int | None]:
    """Parse 'between HH:MM AM and HH:MM PM' into minutes-from-midnight bounds."""
    match = _TIME_RANGE.search(question)
    if not match:
        return None, None
    start = _parse_clock_to_minutes(match.group(1).strip())
    end = _parse_clock_to_minutes(match.group(2).strip())
    return start, end


def _parse_clock_to_minutes(clock: str) -> int | None:
    clock = clock.strip().upper()
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", clock)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3)
    if meridiem == "PM" and hour != 12:
        hour += 12
    if meridiem == "AM" and hour == 12:
        hour = 0
    return hour * 60 + minute
