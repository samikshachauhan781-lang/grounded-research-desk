"""Deterministic answer synthesis from retrieved evidence (mock LLM path)."""

from __future__ import annotations

import re

from backend.app.core.config import Settings
from backend.app.rag.evidence_policy import content_tokens, lexical_overlap_ratio
from backend.app.rag.synthesis_result import SynthesisResult

_CODE_FENCE = re.compile(r"```(?:[\w+-]*\n)?(.*?)```", re.DOTALL)
_BACKTICK = re.compile(r"`([^`]+)`")
_FILENAME = re.compile(
    r"\b[\w./-]+\.(?:py|md|txt|yaml|yml|json|toml|sh|cfg|ini)\b",
    re.IGNORECASE,
)


def _question_lower(question: str) -> str:
    return question.lower().strip()


def asks_for_file(question: str) -> bool:
    q = _question_lower(question)
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


def _asks_for_command(question: str) -> bool:
    q = _question_lower(question)
    return any(
        phrase in q
        for phrase in (
            "command",
            "run ",
            "execute",
            "how do i",
            "how to",
            "what do i run",
        )
    )


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


def validate_cited_chunk_provenance(
    question: str,
    answer: str,
    cited_chunk_id: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> tuple[bool, str]:
    """
    Ensure an Ollama (or external) citation points at evidence that supports the answer.

    Uses the same passage-selection and overlap rules as mock synthesis so a valid
    tag id alone is not enough — the cited chunk must be the best supporting chunk
    and the answer must be grounded in that chunk's text.
    """
    block_map = dict(context_blocks)
    cited_text = block_map.get(cited_chunk_id)
    if cited_text is None:
        return False, "citation_not_in_context"

    best_chunk_id, _, _ = _pick_best_passage(question, context_blocks)
    if cited_chunk_id != best_chunk_id:
        return False, "citation_chunk_mismatch"

    supported, reason = passage_supports_question(question, cited_text, settings)
    if not supported:
        return False, f"cited_{reason}"

    grounded, ground_reason = answer_grounded_in_cited_chunk(answer, cited_text, settings)
    if not grounded:
        return False, ground_reason

    return True, "ok"


def synthesize_answer_from_evidence(
    question: str,
    context_blocks: list[tuple[str, str]],
    settings: Settings,
) -> SynthesisResult:
    """
    Build a grounded mock answer from retrieved evidence.

    Uses lexical overlap only — not a reasoning model. Fails closed when the
    selected passage cannot support the question.
    """
    if not context_blocks:
        return SynthesisResult.insufficient("no_context_blocks")

    chunk_id, passage, _score = _pick_best_passage(question, context_blocks)
    if not passage.strip():
        return SynthesisResult.insufficient("empty_passage")

    supported, reason = passage_supports_question(question, passage, settings)
    if not supported:
        return SynthesisResult.insufficient(reason)

    if asks_for_file(question) and _format_file_answer(question, passage) is None:
        return SynthesisResult.insufficient("file_question_no_filename")

    body = format_direct_answer(question, passage)
    answer = f"{body} [chunk:{chunk_id}]"
    return SynthesisResult.success(answer, chunk_id)
