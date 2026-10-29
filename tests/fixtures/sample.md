# Sample runbook (test fixture)

This file supports retrieval golden tests. It is safe to commit — no secrets.

## Database rollback

If a migration fails in staging, run:

```bash
flyway rollback -count=1
```

Verify connectivity before rollback:

```bash
psql "$DATABASE_URL" -c 'SELECT 1'
```

## Checkout latency

When checkout latency exceeds 2 seconds for five minutes, check the payment gateway status page and scale API replicas to 3.

## On-call contact

Escalate to platform team if rollback fails twice.
