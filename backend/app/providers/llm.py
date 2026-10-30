"""LLM generation providers."""

from abc import ABC, abstractmethod
import re

import httpx

from backend.app.core.config import Settings
from backend.app.core.exceptions import LLMProviderError, LLMTimeoutError
from backend.app.models.schemas import Citation
from backend.app.rag.evidence_answer import (
    synthesize_answer_from_evidence,
    validate_cited_chunk_provenance,
)
from backend.app.rag.prompt_guard import build_grounded_generation_prompt
from backend.app.rag.synthesis_result import SynthesisResult, SynthesisStatus


class GenerationProvider(ABC):
    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> SynthesisResult:
        """Return synthesis outcome with answer text and source chunk on success."""
        raise NotImplementedError


class MockGenerationProvider(GenerationProvider):
    """Deterministic grounded answers extracted from retrieved evidence (not an LLM)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> SynthesisResult:
        _ = timeout_seconds
        return synthesize_answer_from_evidence(question, context_blocks, self._settings)


class OllamaGenerationProvider(GenerationProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> SynthesisResult:
        if not context_blocks:
            return SynthesisResult.insufficient("no_context_blocks")

        prompt = build_grounded_generation_prompt(question, context_blocks)
        url = f"{self._settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self._settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"Generation timed out after {timeout_seconds}s.",
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama unavailable: {exc}") from exc

        answer = str(data.get("response", "")).strip()
        if not answer:
            return SynthesisResult.insufficient("empty_model_response")

        cited = re.findall(r"\[chunk:([a-f0-9-]{36})\]", answer, flags=re.IGNORECASE)
        if not cited:
            cited = re.findall(r"\[([a-f0-9-]{36})\]", answer)
        valid = [cid for cid in cited if any(cid == block[0] for block in context_blocks)]
        if not valid:
            return SynthesisResult.insufficient("missing_chunk_citation")

        cited_id = valid[0]
        provenance_ok, provenance_reason = validate_cited_chunk_provenance(
            question,
            answer,
            cited_id,
            context_blocks,
            self._settings,
        )
        if not provenance_ok:
            return SynthesisResult.insufficient(provenance_reason)

        return SynthesisResult.success(answer, cited_id)


def get_generation_provider(settings: Settings) -> GenerationProvider:
    if settings.llm_provider == "ollama":
        return OllamaGenerationProvider(settings)
    return MockGenerationProvider(settings)


def build_citations(
    chunk_ids: list[str],
    retrieval_map: dict[str, Citation],
) -> list[Citation]:
    citations: list[Citation] = []
    for idx, chunk_id in enumerate(chunk_ids, start=1):
        base = retrieval_map.get(chunk_id)
        if base is None:
            continue
        citations.append(
            Citation(
                citation_id=f"cite-{idx}",
                chunk_id=base.chunk_id,
                document_id=base.document_id,
                filename=base.filename,
                snippet=base.snippet,
                score=base.score,
                char_start=base.char_start,
                char_end=base.char_end,
            ),
        )
    return citations


def synthesis_failed(result: SynthesisResult) -> bool:
    return result.status != SynthesisStatus.SUCCESS
