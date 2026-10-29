"""LLM generation providers."""

from abc import ABC, abstractmethod
import json
import re

import httpx

from backend.app.core.config import Settings
from backend.app.core.exceptions import LLMProviderError, LLMTimeoutError
from backend.app.models.schemas import Citation
from backend.app.rag.prompt_guard import build_grounded_generation_prompt


class GenerationProvider(ABC):
    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> tuple[str, list[str]]:
        """Return answer text and chunk ids cited in the answer."""
        raise NotImplementedError


class MockGenerationProvider(GenerationProvider):
    """Deterministic grounded answers for tests."""

    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> tuple[str, list[str]]:
        _ = timeout_seconds
        if not context_blocks:
            return (
                "No relevant passages found in your documents.",
                [],
            )
        best_id, best_text = context_blocks[0]
        snippet = best_text.strip().split("\n")[0][:240]
        answer = (
            f"Based on the retrieved evidence: {snippet} "
            f"[chunk:{best_id}]"
        )
        return answer, [best_id]


class OllamaGenerationProvider(GenerationProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_answer(
        self,
        question: str,
        context_blocks: list[tuple[str, str]],
        timeout_seconds: int,
    ) -> tuple[str, list[str]]:
        if not context_blocks:
            return ("No relevant passages found in your documents.", [])

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
        cited = re.findall(r"\[chunk:([a-f0-9-]{36})\]", answer, flags=re.IGNORECASE)
        if not cited:
            cited = re.findall(r"\[([a-f0-9-]{36})\]", answer)
        valid = [cid for cid in cited if any(cid == block[0] for block in context_blocks)]
        return answer, valid


def get_generation_provider(settings: Settings) -> GenerationProvider:
    if settings.llm_provider == "ollama":
        return OllamaGenerationProvider(settings)
    return MockGenerationProvider()


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
