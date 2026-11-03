"""Explicit outcomes for evidence-based answer synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SynthesisStatus(str, Enum):
    SUCCESS = "success"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_EVIDENCE = "invalid_evidence"


@dataclass(frozen=True)
class SynthesisResult:
    status: SynthesisStatus
    answer: str = ""
    source_chunk_id: str | None = None
    source_chunk_ids: tuple[str, ...] = ()
    reason: str = ""

    @classmethod
    def success(
        cls,
        answer: str,
        source_chunk_id: str,
        source_chunk_ids: tuple[str, ...] | list[str] | None = None,
    ) -> SynthesisResult:
        if source_chunk_ids is None:
            ids: tuple[str, ...] = (source_chunk_id,)
        else:
            ids = tuple(source_chunk_ids)
            if not ids:
                ids = (source_chunk_id,)
        primary = source_chunk_id if source_chunk_id in ids else ids[0]
        return cls(
            status=SynthesisStatus.SUCCESS,
            answer=answer,
            source_chunk_id=primary,
            source_chunk_ids=ids,
        )

    @classmethod
    def insufficient(cls, reason: str) -> SynthesisResult:
        return cls(status=SynthesisStatus.INSUFFICIENT_EVIDENCE, reason=reason)

    @classmethod
    def invalid(cls, reason: str) -> SynthesisResult:
        return cls(status=SynthesisStatus.INVALID_EVIDENCE, reason=reason)
