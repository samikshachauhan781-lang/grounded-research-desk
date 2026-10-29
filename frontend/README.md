# Frontend — Grounded Research Desk

Evidence Atlas UI (React + TypeScript + Vite).

## Run

```bash
cd frontend
npm install
npm run dev
npm run test:unit
npm run build
npx playwright install   # once; required before E2E
npm run test:e2e         # 4 tests; requires repo root .venv for API (see playwright.config.ts)
```

Ensure the API is running on port 8000 (Vite proxies `/api` and `/health`), or let Playwright start both servers via `playwright.config.ts`.

## Build

```bash
npm run build
npm run preview
```
