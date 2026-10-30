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
    reason: str = ""

    @classmethod
    def success(cls, answer: str, source_chunk_id: str) -> SynthesisResult:
        return cls(
            status=SynthesisStatus.SUCCESS,
            answer=answer,
            source_chunk_id=source_chunk_id,
        )

    @classmethod
    def insufficient(cls, reason: str) -> SynthesisResult:
        return cls(status=SynthesisStatus.INSUFFICIENT_EVIDENCE, reason=reason)

    @classmethod
    def invalid(cls, reason: str) -> SynthesisResult:
        return cls(status=SynthesisStatus.INVALID_EVIDENCE, reason=reason)
