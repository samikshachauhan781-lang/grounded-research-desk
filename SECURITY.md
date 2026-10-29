# Security

## Threat model (proportionate MVP)

| Threat | Mitigation |
| --- | --- |
| Secret leakage via repo | `.gitignore`, no secrets in docs |
| Malicious upload (zip bomb, huge file) | Size cap, extension allowlist |
| Prompt injection in documents | Delimiters + grounding prompts |
| SSRF via agent | No URL fetch tool in MVP |
| SQL injection | SQLAlchemy parameterized queries only |
| Path traversal on upload | Sanitize filename; store outside web root with UUID prefix |
| Open API docs in prod | Disable `/docs` when `APP_ENV=production` |

## Authentication (future)

MVP: **no auth** for local dev.  
Phase 9+: optional API key header `Authorization: Bearer <token>` for deploy.

Document clearly on public demos.

## Data classification

Users may upload confidential runbooks. Recommend:

- Local-only deployment for sensitive data
- Do not use public Render demo for private content

## Upload validation

1. Check extension ∈ `ALLOWED_UPLOAD_EXTENSIONS`
2. Reject empty files
3. `byte_size <= MAX_UPLOAD_BYTES`
4. Store with random prefix path — never execute uploaded content

## Agent safety

Cross-reference [GUARDRAILS.md](./GUARDRAILS.md).

## Dependencies

- Pin versions in `pyproject.toml`
- Run `pip audit` or `uv pip audit` in CI when available

## Logging hygiene

- Do not log full prompts at INFO in production
- Redact tokens if auth added

## HTTPS

Required in production deployment behind TLS terminator ([DEPLOYMENT.md](./DEPLOYMENT.md)).

## Security checklist before public deploy

- [ ] `DEMO_MODE` considered
- [ ] `/docs` disabled
- [ ] CORS restricted to frontend origin
- [ ] Rate limit on upload and ask
- [ ] No default admin credentials

## Incident linkage

Production security incidents: [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).

## Interview Q&A

**Q:** How is this different from “secure AI”?  
**A:** We combine input validation, read-only tools, citation verification, and explicit non-goals (no shell/network) — defense in depth for a demo-grade agent.
