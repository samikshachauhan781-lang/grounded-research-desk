"""Measure ask latency with fake embeddings (local dev fixture)."""

from __future__ import annotations

import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def main() -> None:
    sample = (ROOT / "tests" / "fixtures" / "sample.md").read_bytes()
    tmp = Path(tempfile.mkdtemp(prefix="grd-bench-"))
    settings = Settings(
        DATABASE_URL=f"sqlite:///{tmp / 'bench.db'}",
        UPLOAD_DIR=str(tmp / "uploads"),
        DATA_DIR=str(tmp),
        EMBEDDING_PROVIDER="fake",
        LLM_PROVIDER="mock",
    )
    app = create_app(settings=settings)

    with TestClient(app) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("sample.md", sample, "text/markdown")},
        )
        upload.raise_for_status()
        document_id = upload.json()["document_id"]

        samples: list[float] = []
        for _ in range(5):
            start = time.perf_counter()
            response = client.post(
                "/api/v1/ask",
                json={
                    "question": "What command rolls back the database migration?",
                    "document_ids": [document_id],
                },
            )
            response.raise_for_status()
            samples.append((time.perf_counter() - start) * 1000)

    print("Grounded Research Desk — ask latency (fake embed + mock LLM)")
    print(f"  corpus: tests/fixtures/sample.md")
    print(f"  samples: {len(samples)}")
    print(f"  p50: {statistics.median(samples):.1f} ms")
    print(f"  max: {max(samples):.1f} ms")


if __name__ == "__main__":
    main()
