# Payment API Incident

Incident ID: INC-2026-105
Service: Payment API

## Root cause

The new deployment increased database connection usage, exhausting the database connection pool.

## Timeline

- 10:00 AM — New deployment started.
- 10:05 AM — API error rate increased.
- 10:10 AM — Database connection pool exhaustion detected.
- 10:15 AM — Deployment rollback initiated.
- 10:20 AM — API service recovered.

## Resolution

The deployment was rolled back, and the API recovered after database connections were released.
