# Grounded Research Desk — Live Demo Speaker Notes

Use this script for interviews and live demos. **Five steps**, ~5–8 minutes. Speak in Hinglish where noted; UI labels stay in English.

---

## Before you start (startup)

From [README.md](./README.md):

**Terminal 1 — API**

```bash
cd /Users/samiksha/Documents/Project_2
source .venv/bin/activate
EMBEDDING_PROVIDER=fake LLM_PROVIDER=mock uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — UI**

```bash
cd /Users/samiksha/Documents/Project_2/frontend
npm run dev
```

**Open:** http://127.0.0.1:5173

**Pass check:** Top bar shows **API Connected** (green status). If it says **Disconnected**, start Terminal 1 first, wait a few seconds, refresh the browser.

Optional health check:

```bash
curl http://127.0.0.1:8000/health
```

Expect `"status":"ok"`.

**Demo providers (say this early):** The commands above use **`EMBEDDING_PROVIDER=fake`** and **`LLM_PROVIDER=mock`**. That is the same stack as pytest and Playwright — it proves RAG plumbing, evidence gating, and citations **without** neural embedding models or Ollama. Answers in this mode come from the **mock LLM** summarizing retrieved chunks, not from live LLM inference. For real models, see [CONFIGURATION.md](./CONFIGURATION.md).

---

## Demo flow (one line)

Guide purpose → Library upload → Research rollback → Evidence **Open source** → Mars question → **Insufficient evidence**.

---

## Step 1 — Guide Bot (website purpose)

### UI actions

1. Click the **teal bot icon** (bottom-right) — aria label **Open Research Desk Guide**.
2. Confirm welcome: *“Hi! I'm your Research Desk Guide. I can explain this website and help you get started.”*
3. Click FAQ chip: **What does this website do?**
4. (Optional) Point to subtitle: **Built-in FAQ · not a live AI chatbot**

### Kya bolo (Hinglish)

*“Yeh Research Desk Guide sirf product help hai — live AI chatbot nahi. Website ka kaam: aap Markdown ya text upload karte ho, system relevant document chunks retrieve karta hai, jawab citations ke saath aata hai; agar proof strong nahi hai to system guess nahi karta, insufficient evidence dikhata hai.”*

### Expected outcome

- Panel opens as a dialog; suggested FAQ chips visible.
- Answer explains upload, chunk retrieval, citations, and refusing unsupported questions.
- **Open Library** / **Start Research** buttons navigate to `/library` and `/` and close the panel.

### Troubleshooting

- No bot button? Guide is mounted in the app shell; refresh after `npm run dev`. It can be disabled with `VITE_GUIDE_ENABLED=false` (not needed for demo).
- Panel blocks view? Close with **✕**, click **backdrop**, or **Escape**.

---

## Step 2 — Library (upload fixture)

### UI actions

1. Sidebar → **Library** (or use **Open Library** from the guide).
2. **Upload documents** or drag-drop file onto the drop zone.
3. Upload: `tests/fixtures/sample.md` (from repo root).

### Kya bolo

*“Pehle source of truth library mein aati hai. Is MVP mein sirf Markdown aur plain text — PDF nahi. Upload ke baad ingestion chunk banata hai aur embedding index hota hai.”*

### Expected outcome

- Row appears for `sample.md`.
- Status **completed** (after processing).
- **Chunk count** ≥ 1 on the document row.

Fixture content includes (for later steps):

```bash
flyway rollback -count=1
```

under a **Database rollback** section.

### Troubleshooting

- Upload fails → check **API Connected**; API must be running on port 8000.
- Stuck processing → refresh Library; check Terminal 1 for errors.
- Duplicate rows from earlier demos are OK; pick the newest `sample.md` or any completed copy.

---

## Step 3 — Research (rollback question)

### UI actions

1. Sidebar → **Research** (`/`).
2. In **Research question**, type exactly:

```text
What command rolls back the database migration?
```

3. Click **Submit question**.

### Kya bolo

*“Yeh document-grounded research assistant hai — guide bot nahi. Question par retrieval chalti hai, evidence check hota hai, phir answer citations ke saath generate hota hai.”*

### Expected outcome

- Answer area shows text mentioning **flyway rollback** (from retrieved chunks).
- **Evidence rail** (right on desktop) lists at least one citation with a snippet containing **flyway rollback**.
- **Insufficient evidence** banner should **not** appear for this question.

### Troubleshooting

- Empty answer / error → **API Disconnected** or no documents indexed; redo Step 2.
- No evidence rail on small screen → use **Evidence** toggle button near the answer.

---

## Step 4 — Evidence (open source → chunk)

### UI actions

1. In **Evidence rail**, find the citation for the rollback question.
2. Click **Open source** (this is a **button**, not a link).
3. Document inspector opens (`/library/<documentId>`), optionally with `?chunk=` in the URL.
4. Select the highlighted **Chunk** in the sidebar if needed.

### Kya bolo

*“Citation sirf decoration nahi — yeh wahi chunk hai jo retrieve hua. Inspector mein original chunk text dikhta hai; audience ko `flyway rollback -count=1` line dikhao.”*

### Expected outcome

- Inspector shows chunk list and chunk body text including:

```bash
flyway rollback -count=1
```

- Matching chunk may show highlight class when `chunk` query param matches.

### Troubleshooting

- **Open source** does nothing → API must be up; document id must still exist in Library.
- Wrong chunk selected → click the chunk in the sidebar that contains the rollback command.

---

## Step 5 — Safety (Mars / Zephyr-9)

### UI actions

1. Stay on **Research** (same session flow — use **Ask another question** or equivalent composer after the first answer).
2. Type exactly:

```text
What is the capital of Mars colony Zephyr-9?
```

3. Click **Submit question**.

### Kya bolo

*“Library mein Mars colony ka koi chunk nahi — isliye system confidently jhoot nahi bolta. Insufficient evidence, zero citations — yahi safety gate hai.”*

### Expected outcome

- Warning alert with heading **Insufficient evidence**.
- Explanation text in the answer area (refusal / no grounded support).
- Link **Upload a relevant source** → Library.
- Evidence rail: **no** **Open source** buttons (zero citations).

### Troubleshooting

- If you still get citations → wrong document corpus or evidence policy bypass; use fresh `sample.md` upload and fake/mock providers as in startup commands.
- Same Mars question is used in `tests/integration/test_retrieval_and_ask.py` and Playwright E2E — expected `insufficient_evidence: true`.

---

## Close the demo (optional 10 seconds)

*“Local-first RAG: ingest, retrieve, cite, refuse when weak — optional agent behind `AGENT_ENABLED`. Not production-ready: no auth, no PDF.”*

Point to **Research History** if time allows (sessions saved from Research submits).

---

## Quick troubleshooting summary

| Symptom | Fix |
| --- | --- |
| **API Disconnected** | Start Terminal 1; refresh UI; confirm `curl …/health` |
| Guide won't open | Refresh; confirm frontend dev server on 5173 |
| Upload fails | API running; file is `.md` or `.txt` |
| No rollback in answer | Upload `sample.md`; ask exact rollback question |
| Can't open citation | Use **Open source** button in Evidence rail |
| Mars question gives citations | Re-upload fixture; use exact question; check providers `fake` + `mock` |

---

## Re-verify automation (optional)

Does not replace a live demo; confirms the same flow **locally** (Playwright is **not** run in GitHub Actions CI):

```bash
cd frontend && npx playwright install   # first time only
npm run test:e2e                        # 4 tests
```

Or run a subset:

```bash
cd frontend && npx playwright test e2e/demo-checklist.spec.ts e2e/research.spec.ts e2e/guide.spec.ts
```

Backend:

```bash
pytest tests/ -q
```

---

## Related docs

- [README.md](./README.md) — install, demo checklist, pitch
- [ARCHITECTURE.md](./ARCHITECTURE.md) — ask flow and evidence gate
