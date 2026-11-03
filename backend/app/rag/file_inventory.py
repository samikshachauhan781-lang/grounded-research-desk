"""Extract structured file inventory lines from markdown-style evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.rag.evidence_policy import content_tokens

_FILE_EXTENSIONS = r"(?:py|md|txt|yaml|yml|json|toml|sh|cfg|ini)"
_INVENTORY_LINE = re.compile(
    rf"^\s*[-*]\s*(?:`(?P<backtick>[\w./-]+\.{_FILE_EXTENSIONS})`|(?P<bare>[\w./-]+\.{_FILE_EXTENSIONS}))"
    rf"(?:\s*\((?P<lines>\d+)\s*lines?\))?"
    rf"\s*[-–—]\s*(?P<desc>.+?)\s*$",
    re.IGNORECASE,
)
_SECTION_HEADER = re.compile(r"^\s*\*\*(?P<title>.+?)\*\*\s*:?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class FileInventoryEntry:
    filename: str
    line_count: int | None
    description: str
    chunk_id: str
    section: str
    source_line: str

    @property
    def richness(self) -> int:
        score = 0
        if self.line_count is not None:
            score += 1
        if self.description.strip():
            score += 1
        return score


def extract_file_inventory_from_text(text: str, chunk_id: str) -> list[FileInventoryEntry]:
    entries: list[FileInventoryEntry] = []
    current_section = ""
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        section_match = _SECTION_HEADER.match(stripped)
        if section_match:
            current_section = section_match.group("title").strip().lower()
            continue
        match = _INVENTORY_LINE.match(raw_line)
        if not match:
            continue
        filename = (match.group("backtick") or match.group("bare") or "").strip()
        if not filename:
            continue
        lines_raw = match.group("lines")
        line_count = int(lines_raw) if lines_raw else None
        description = (match.group("desc") or "").strip()
        entries.append(
            FileInventoryEntry(
                filename=filename,
                line_count=line_count,
                description=description,
                chunk_id=chunk_id,
                section=current_section,
                source_line=stripped,
            ),
        )
    return entries


def inventory_scope_from_question(question: str) -> set[str] | None:
    """Return content tokens that should appear in the section or description, if scoped."""
    q_tokens = content_tokens(question)
    scope: set[str] = set()
    if "core" in q_tokens:
        scope.add("core")
    if "application" in q_tokens:
        scope.add("application")
    if "test" in q_tokens:
        scope.add("test")
    return scope or None


def entry_matches_scope(entry: FileInventoryEntry, scope: set[str]) -> bool:
    haystack = f"{entry.section} {entry.description} {entry.filename}".lower()
    return all(token in haystack for token in scope)


def minimum_requested_file_count(question: str) -> int | None:
    q = question.lower()
    if re.search(r"\bboth\b", q):
        return 2
    return None


def question_requests_line_counts(question: str) -> bool:
    q = question.lower()
    return "line count" in q or "line counts" in q or re.search(r"\blines?\b", q) and "file" in q


def question_requests_responsibilities(question: str) -> bool:
    q = question.lower()
    return any(
        phrase in q
        for phrase in (
            "responsibilit",
            "purpose",
            "what does",
            "with their",
        )
    )


def format_inventory_answer(
    entries: list[FileInventoryEntry],
    *,
    include_line_counts: bool,
    include_descriptions: bool,
) -> str:
    lines: list[str] = []
    for entry in entries:
        if include_line_counts and include_descriptions and entry.line_count is not None:
            desc = entry.description.rstrip(".")
            lines.append(
                f"- `{entry.filename}` ({entry.line_count} lines) — {desc}.",
            )
        elif include_descriptions and entry.description:
            desc = entry.description.rstrip(".")
            lines.append(f"- `{entry.filename}` — {desc}.")
        else:
            lines.append(f"- `{entry.filename}`")
    return "\n".join(lines)


def collect_inventory_entries(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> list[FileInventoryEntry]:
    scope = inventory_scope_from_question(question)
    merged: dict[str, FileInventoryEntry] = {}
    for chunk_id, text in context_blocks:
        for entry in extract_file_inventory_from_text(text, chunk_id):
            if scope and not entry_matches_scope(entry, scope):
                continue
            key = entry.filename.lower()
            existing = merged.get(key)
            if existing is None or entry.richness > existing.richness:
                merged[key] = entry
    return sorted(merged.values(), key=lambda item: item.filename.lower())
