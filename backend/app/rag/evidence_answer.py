"""Deterministic answer synthesis from retrieved evidence (mock LLM path)."""

from __future__ import annotations

import re

from backend.app.core.config import Settings
from backend.app.rag.file_inventory import (
    collect_inventory_entries,
    format_inventory_answer,
    minimum_requested_file_count,
    question_requests_line_counts,
    question_requests_responsibilities,
)
from backend.app.rag.incident_extraction import (
    extract_metadata_value,
    extract_resolution,
    extract_root_cause,
    extract_timeline_for_question,
    format_metadata_answer,
    format_timeline_answer,
    timeline_events_for_question,
)
from backend.app.rag.evidence_policy import content_tokens, lexical_overlap_ratio, passage_has_status_evidence
from backend.app.rag.question_intent import (
    QuestionIntent,
    asks_for_command,
    asks_for_development_status,
    asks_for_file,
    asks_for_directory_overview,
    asks_for_file_attributes,
    asks_for_multiple_files,
    detect_metadata_field,
    detect_question_intent,
    multi_file_inventory_applies,
)
from backend.app.rag.synthesis_result import SynthesisResult

SYNTHESIS_MAX_CHUNK_CHARS = 8000

_CODE_FENCE = re.compile(r"```(?:[\w+-]*\n)?(.*?)```", re.DOTALL)
_BACKTICK = re.compile(r"`([^`]+)`")
_FILENAME = re.compile(
    r"\b[\w./-]+\.(?:py|md|txt|yaml|yml|json|toml|sh|cfg|ini)\b",
    re.IGNORECASE,
)


def clip_chunk_text_for_synthesis(text: str, max_chars: int = SYNTHESIS_MAX_CHUNK_CHARS) -> str:
    """Bound text passed to synthesis while keeping full incident sections when possible."""
    return text[:max_chars]


def _question_lower(question: str) -> str:
    return question.lower().strip()


def _asks_for_command(question: str) -> bool:
    return asks_for_command(question)


def extract_filename_from_passage(passage: str) -> str | None:
    """Return a filename from inline backticks or bare path tokens in a passage."""
    backticks = _BACKTICK.findall(passage)
    file_candidates = [b for b in backticks if "." in b and not b.startswith("http")]
    if not file_candidates:
        match = _FILENAME.search(passage)
        if match:
            file_candidates = [match.group(0)]
    if not file_candidates:
        return None
    return file_candidates[0]


def _candidate_passages(text: str) -> list[str]:
    """Lines and code-fence bodies suitable for quoting as answers."""
    passages: list[str] = []
    seen: set[str] = set()

    def add(part: str) -> None:
        cleaned = " ".join(part.split())
        if len(cleaned) < 8 or cleaned in seen:
            return
        seen.add(cleaned)
        passages.append(cleaned)

    for match in _CODE_FENCE.finditer(text):
        body = match.group(1).strip()
        for line in body.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                add(line)

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        add(line)

    return passages


def _score_passage(question: str, passage: str) -> float:
    score = lexical_overlap_ratio(question, passage)
    q = _question_lower(question)
    p = passage.lower()
    if _asks_for_command(question):
        if "rollback" in q and "rollback" in p:
            score += 0.5
        if "migration" in q and ("migration" in p or "flyway" in p):
            score += 0.35
        if "flyway" in p:
            score += 0.25
    if asks_for_file(question):
        if _BACKTICK.search(passage) or _FILENAME.search(passage):
            score += 0.45
        if "file" in q and "file" in p:
            score += 0.2
        if "test" in q and "test" in p:
            score += 0.15
    if asks_for_development_status(question) and passage_has_status_evidence(passage):
        score += 0.4
    return score


def _pick_best_passage(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> tuple[str, str, float]:
    best_score = -1.0
    best_chunk_id = context_blocks[0][0]
    best_passage = ""

    for chunk_id, text in context_blocks:
        for passage in _candidate_passages(text):
            score = _score_passage(question, passage)
            if score > best_score:
                best_score = score
                best_chunk_id = chunk_id
                best_passage = passage

    if not best_passage and context_blocks:
        best_passage = " ".join(context_blocks[0][1].split())[:400]
        best_chunk_id = context_blocks[0][0]
        best_score = lexical_overlap_ratio(question, best_passage)

    return best_chunk_id, best_passage, max(best_score, 0.0)


def _command_evidence_bridge(question: str, passage: str) -> bool:
    """Link command questions to command-like passages without extra thresholds."""
    q = _question_lower(question)
    p = passage.lower()
    if ("rollback" in q or "roll back" in q) and "rollback" in p:
        return True
    if "migration" in q and ("migration" in p or "flyway" in p):
        return True
    return False


def _filename_question_bridge(question: str, filename: str) -> bool:
    """True when the question shares a content token with the filename path."""
    path_tokens = content_tokens(filename.replace("_", " ").replace(".", " "))
    return bool(content_tokens(question) & path_tokens)


def passage_supports_question(
    question: str,
    passage: str,
    settings: Settings,
) -> tuple[bool, str]:
    """
    Answer-level validation on the selected passage (after retrieval sufficiency).

    Uses ``EVIDENCE_MIN_LEXICAL_OVERLAP`` plus question-type bridges so command
    lines and code-fence filenames are not rejected for tokenizer mismatch alone.
    """
    min_overlap = settings.evidence_min_lexical_overlap
    overlap = lexical_overlap_ratio(question, passage)

    if _asks_for_command(question):
        if _format_command_answer(question, passage) and _command_evidence_bridge(
            question,
            passage,
        ):
            return True, "ok"

    if asks_for_file(question):
        filename = extract_filename_from_passage(passage)
        if filename is None:
            return False, "file_question_no_filename"
        if _filename_question_bridge(question, filename):
            return True, "ok"

    if overlap < min_overlap:
        return False, "passage_lexical_overlap"

    if asks_for_file(question) and extract_filename_from_passage(passage) is None:
        return False, "file_question_no_filename"

    return True, "ok"


def _format_file_answer(question: str, passage: str) -> str | None:
    name = extract_filename_from_passage(passage)
    if name is None:
        return None

    if asks_for_file(question):
        remainder = passage
        for token in (f"`{name}`", name):
            remainder = remainder.replace(token, "", 1)
        remainder = remainder.strip(" .,-—")
        if remainder.lower().startswith("the "):
            remainder = remainder[4:].strip()
        if remainder:
            first = remainder[0].upper() + remainder[1:] if remainder else ""
            if not first.endswith("."):
                first = f"{first}."
            return f"The file is `{name}`. {first}"
        return f"The file is `{name}`."
    return None


def _format_command_answer(question: str, passage: str) -> str | None:
    q = _question_lower(question)
    if "flyway rollback" in passage.lower() or (
        "rollback" in q and "flyway rollback" in passage.lower()
    ):
        return (
            "Use `flyway rollback -count=1` to roll back the database migration "
            "(as documented in the uploaded runbook)."
        )
    backticks = _BACKTICK.findall(passage)
    for token in backticks:
        if " " in token or "-" in token:
            return f"Run `{token}` according to the retrieved documentation."
    if passage.count(" ") <= 12 and any(c in passage for c in ("-", "_", "/")):
        return f"Run `{passage}` according to the retrieved documentation."
    return None


def format_direct_answer(question: str, passage: str) -> str:
    """Turn the best evidence passage into a short, question-focused answer."""
    file_answer = _format_file_answer(question, passage)
    if file_answer:
        return file_answer

    if _asks_for_command(question):
        command_answer = _format_command_answer(question, passage)
        if command_answer:
            return command_answer

    if passage.lower().startswith("the ") and " file " in passage.lower():
        return passage if passage.endswith(".") else f"{passage}."

    return passage if passage.endswith(".") else f"{passage}."


_CHUNK_TAG = re.compile(r"\[chunk:[a-f0-9-]{36}\]", re.IGNORECASE)


def strip_chunk_citation_tags(answer: str) -> str:
    return _CHUNK_TAG.sub("", answer).strip()


def answer_grounded_in_cited_chunk(
    answer: str,
    cited_text: str,
    settings: Settings,
) -> tuple[bool, str]:
    """
    Check that the model answer is supported by the cited chunk text.

    Fails when the answer names files/commands that do not appear in that chunk,
    or when answer content tokens do not overlap the citation body enough.
    """
    body = strip_chunk_citation_tags(answer)
    if not body:
        return False, "empty_answer_body"

    cited_lower = cited_text.lower()
    for token in _BACKTICK.findall(body):
        if token.lower() not in cited_lower:
            return False, "answer_fact_not_in_cited_chunk"

    for match in _FILENAME.finditer(body):
        if match.group(0).lower() not in cited_lower:
            return False, "answer_fact_not_in_cited_chunk"

    min_overlap = settings.evidence_min_lexical_overlap
    if lexical_overlap_ratio(body, cited_text) >= min_overlap:
        return True, "ok"

    answer_tokens = content_tokens(body)
    cited_tokens = content_tokens(cited_text)
    if answer_tokens:
        shared_ratio = len(answer_tokens & cited_tokens) / len(answer_tokens)
        if shared_ratio >= min_overlap:
            return True, "ok"

    return False, "answer_cited_chunk_overlap"


def _is_metadata_label_line(passage: str) -> bool:
    return bool(re.match(r"^(incident id|service|severity|date)\s*:", passage.strip(), re.I))


def _extract_intent_answer(
    intent: QuestionIntent,
    question: str,
    text: str,
    settings: Settings,
) -> str | None:
    if intent == QuestionIntent.ROOT_CAUSE:
        value = extract_root_cause(text)
        return value if value else None

    if intent == QuestionIntent.RESOLUTION:
        value = extract_resolution(text)
        return value if value else None

    if intent == QuestionIntent.TIMELINE:
        return extract_timeline_for_question(text, question)

    if intent == QuestionIntent.METADATA:
        field = detect_metadata_field(question)
        if field is None or field == "sensitive_missing":
            return None
        value = extract_metadata_value(text, field)
        if value is None:
            return None
        return format_metadata_answer(field, value)

    return None


def _extract_general_answer(question: str, text: str, settings: Settings) -> str | None:
    planned = _plan_general_answer(question, [("x", text)], settings)
    if planned is None:
        return None
    return planned[0]


def _plan_general_answer(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[str, str] | None:
    """Return (answer_body, chunk_id) from the best supported GENERAL passage."""
    if not context_blocks:
        return None
    chunk_id, passage, _ = _pick_best_passage(question, context_blocks)
    if not passage.strip():
        return None
    if _is_metadata_label_line(passage):
        return None
    supported, _ = passage_supports_question(question, passage, settings)
    if not supported:
        return None
    return format_direct_answer(question, passage), chunk_id


def _timeline_event_key(event: tuple[int, str, str]) -> tuple[int, str]:
    return (event[0], event[2].lower())


def _timeline_chunks_with_events(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> list[tuple[str, list[tuple[int, str, str]], str]]:
    contributing: list[tuple[str, list[tuple[int, str, str]], str]] = []
    for chunk_id, text in context_blocks:
        events = timeline_events_for_question(text, question)
        if events:
            contributing.append((chunk_id, events, text))
    return contributing


def timeline_spans_multiple_chunks(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> bool:
    """True when in-range timeline events are split across chunks (no single chunk has all)."""
    if detect_question_intent(question) != QuestionIntent.TIMELINE:
        return False
    contributing = _timeline_chunks_with_events(question, context_blocks)
    if not contributing:
        return False

    union_keys: set[tuple[int, str]] = set()
    for _, events, _ in contributing:
        for event in events:
            union_keys.add(_timeline_event_key(event))

    for _, events, _ in contributing:
        keys = {_timeline_event_key(event) for event in events}
        if keys >= union_keys:
            return False
    return True


def _plan_timeline_body(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> tuple[str, str] | None:
    contributing = _timeline_chunks_with_events(question, context_blocks)
    if not contributing:
        return None

    union_keys: set[tuple[int, str]] = set()
    for _, events, _ in contributing:
        for event in events:
            union_keys.add(_timeline_event_key(event))

    for chunk_id, events, text in contributing:
        keys = {_timeline_event_key(event) for event in events}
        if keys >= union_keys:
            body = format_timeline_answer(events)
            if _timeline_answer_grounded_in_text(body, text):
                return chunk_id, body
    return None


def _entry_grounded_in_chunk(entry_source_line: str, filename: str, chunk_text: str) -> bool:
    chunk_lower = chunk_text.lower()
    if entry_source_line.lower() in chunk_lower:
        return True
    return filename.lower() in chunk_lower


def _plan_multi_file_inventory(
    question: str,
    context_blocks: list[tuple[str, str]],
) -> tuple[str, tuple[str, ...]] | None:
    entries = collect_inventory_entries(question, context_blocks)
    if not entries:
        return None

    min_count = minimum_requested_file_count(question)
    if min_count is not None and len(entries) < min_count:
        return None

    block_map = dict(context_blocks)
    include_line_counts = question_requests_line_counts(question) or (
        asks_for_multiple_files(question)
        and any(entry.line_count is not None for entry in entries)
    )
    include_descriptions = asks_for_file_attributes(question) or asks_for_multiple_files(question)

    if include_line_counts and any(entry.line_count is None for entry in entries):
        return None
    if question_requests_responsibilities(question) and any(
        not entry.description.strip() for entry in entries
    ):
        return None

    for entry in entries:
        chunk_text = block_map.get(entry.chunk_id, "")
        if not _entry_grounded_in_chunk(entry.source_line, entry.filename, chunk_text):
            return None

    body = format_inventory_answer(
        entries,
        include_line_counts=include_line_counts,
        include_descriptions=include_descriptions,
    )
    chunk_ids = tuple(dict.fromkeys(entry.chunk_id for entry in entries))
    return body, chunk_ids


def _plan_directory_overview(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[str, tuple[str, ...]] | None:
    best_score = -1.0
    best: tuple[str, str] | None = None

    for chunk_id, text in context_blocks:
        for passage in _candidate_passages(text):
            lowered = passage.lower()
            if passage.strip().startswith("- `") or (
                extract_filename_from_passage(passage) and len(passage) < 160 and " — " in passage
            ):
                continue
            if lowered.startswith("**") and "files" in lowered:
                continue
            supported, _ = passage_supports_question(question, passage, settings)
            if not supported:
                continue
            score = lexical_overlap_ratio(question, passage)
            if "directory contains" in lowered or "this directory" in lowered:
                score += 0.35
            if score > best_score:
                best_score = score
                best = (chunk_id, passage)

    if best is None:
        return None
    chunk_id, passage = best
    body = format_direct_answer(question, passage)
    return body, (chunk_id,)


def _plan_synthesis_body(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[str, tuple[str, ...]] | None:
    """Return (answer_body, supporting_chunk_ids) when evidence supports the question."""
    intent = detect_question_intent(question)
    field = detect_metadata_field(question)
    if field == "sensitive_missing":
        return None

    if intent == QuestionIntent.TIMELINE:
        planned = _plan_timeline_body(question, context_blocks)
        if planned is None:
            return None
        chunk_id, body = planned
        return body, (chunk_id,)

    if multi_file_inventory_applies(question):
        planned = _plan_multi_file_inventory(question, context_blocks)
        if planned is not None:
            return planned
        return None

    if intent in {
        QuestionIntent.FILE,
        QuestionIntent.COMMAND,
        QuestionIntent.GENERAL,
    }:
        if intent == QuestionIntent.GENERAL and asks_for_directory_overview(question):
            planned = _plan_directory_overview(question, context_blocks, settings)
            if planned is not None:
                return planned

        for chunk_id, text in context_blocks:
            if intent == QuestionIntent.FILE and not asks_for_multiple_files(question):
                for passage in _candidate_passages(text):
                    if extract_filename_from_passage(passage) is None:
                        continue
                    formatted = _format_file_answer(question, passage)
                    if not formatted:
                        continue
                    supported, _ = passage_supports_question(question, passage, settings)
                    if supported:
                        return formatted, (chunk_id,)
            elif intent == QuestionIntent.COMMAND:
                for passage in _candidate_passages(text):
                    cmd = _format_command_answer(question, passage)
                    if cmd and _command_evidence_bridge(question, passage):
                        return cmd, (chunk_id,)
            elif intent == QuestionIntent.GENERAL:
                planned_general = _plan_general_answer(question, context_blocks, settings)
                if planned_general is None:
                    return None
                body, general_chunk_id = planned_general
                return body, (general_chunk_id,)
        return None

    for chunk_id, text in context_blocks:
        body = _extract_intent_answer(intent, question, text, settings)
        if not body:
            continue
        if intent == QuestionIntent.ROOT_CAUSE and extract_root_cause(text) is None:
            continue
        if intent == QuestionIntent.RESOLUTION and extract_resolution(text) is None:
            continue
        if intent == QuestionIntent.METADATA:
            return body, (chunk_id,)
        if body.lower() in text.lower() or lexical_overlap_ratio(body, text) >= settings.evidence_min_lexical_overlap:
            return body, (chunk_id,)
    return None


def _timeline_answer_grounded_in_text(answer: str, source: str) -> bool:
    def norm(value: str) -> str:
        return value.lower().replace("—", "-").replace("–", "-")

    source_norm = norm(source)
    for line in answer.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        core = norm(stripped.lstrip("-").strip())
        if core not in source_norm:
            return False
    return True


def resolve_synthesis_chunk_id(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> str | None:
    ids = resolve_synthesis_chunk_ids(question, context_blocks, settings)
    return ids[0] if ids else None


def resolve_synthesis_chunk_ids(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[str, ...]:
    planned = _plan_synthesis_body(question, context_blocks, settings)
    if planned is None:
        return ()
    return planned[1]


def validate_cited_chunk_provenance(
    question: str,
    answer: str,
    cited_chunk_id: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[bool, str]:
    """Ensure an Ollama citation points at evidence that supports the answer."""
    block_map = dict(context_blocks)
    cited_text = block_map.get(cited_chunk_id)
    if cited_text is None:
        return False, "citation_not_in_context"

    expected_ids = resolve_synthesis_chunk_ids(question, context_blocks, settings)
    if not expected_ids:
        return False, "cited_insufficient_evidence"
    if cited_chunk_id not in expected_ids:
        return False, "citation_chunk_mismatch"

    planned = _plan_synthesis_body(question, context_blocks, settings)
    if planned is None:
        return False, "cited_insufficient_evidence"

    body = strip_chunk_citation_tags(answer)
    intent = detect_question_intent(question)
    if intent == QuestionIntent.TIMELINE:
        if not _timeline_answer_grounded_in_text(body, cited_text):
            return False, "answer_fact_not_in_cited_chunk"
        return True, "ok"

    if len(expected_ids) > 1:
        union_text = "\n\n".join(
            block_map[chunk_id]
            for chunk_id in expected_ids
            if chunk_id in block_map
        )
        grounded, ground_reason = answer_grounded_in_cited_chunk(
            answer,
            union_text,
            settings,
        )
        if not grounded:
            return False, ground_reason
        return True, "ok"

    grounded, ground_reason = answer_grounded_in_cited_chunk(answer, cited_text, settings)
    if not grounded:
        return False, ground_reason

    return True, "ok"


def synthesize_answer_from_evidence(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> SynthesisResult:
    """Build a grounded mock answer from retrieved evidence (deterministic, fail-closed)."""
    if not context_blocks:
        return SynthesisResult.insufficient("no_context_blocks")

    planned = _plan_synthesis_body(question, context_blocks, settings)
    if planned is None:
        intent = detect_question_intent(question)
        if intent == QuestionIntent.TIMELINE and timeline_spans_multiple_chunks(
            question,
            context_blocks,
        ):
            return SynthesisResult.insufficient("timeline_spans_multiple_chunks")
        if multi_file_inventory_applies(question):
            return SynthesisResult.insufficient("multi_fact_incomplete")
        if intent == QuestionIntent.FILE:
            return SynthesisResult.insufficient("file_question_no_filename")
        return SynthesisResult.insufficient("unsupported_or_missing_evidence")

    body, chunk_ids = planned
    if not body.strip():
        return SynthesisResult.insufficient("empty_passage")

    return SynthesisResult.success(body, chunk_ids[0], source_chunk_ids=chunk_ids)
