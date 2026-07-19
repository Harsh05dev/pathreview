# PLAN — Issue #154: Health check DB probe fails under SQLAlchemy 2.x

- **Issue:** https://github.com/ascherj/pathreview/issues/154
- **Tier:** 1 (labels: `api`, `bug`, `good first issue`, `tier-1`)
- **Branch:** `fix/154-health-db-probe-text`
- **Contributor:** Harsh Mehta (fork: `Harsh05dev/pathreview`)

## Problem Summary

The `GET /health` endpoint probes PostgreSQL by executing the literal
string `"SELECT 1"`. In SQLAlchemy 2.x, textual SQL passed to
`Session.execute()` must be wrapped in `sqlalchemy.text()`. Passing a raw
`str` raises `ArgumentError: Textual SQL expression 'SELECT 1' should be
explicitly declared as text('SELECT 1')`.

Because the probe is inside a `try/except Exception`, the raised error is
swallowed and the endpoint reports Postgres as `"unhealthy"` and returns
`503` — **even when the database is fully reachable**. This produces false
outage signals for any monitoring / load balancer hitting `/health`.

## Location

- File: `api/routes/health.py`
- Line 31: `await db.execute("SELECT 1")`

```python
try:
    # Check PostgreSQL
    await db.execute("SELECT 1")          # <-- raises under SQLAlchemy 2.x
    health_status["dependencies"]["postgres"] = "healthy"
```

## Root Cause

SQLAlchemy 2.0 removed implicit auto-conversion of plain strings into
executable text clauses (deprecated in 1.4, removed in 2.0). The project
pins `sqlalchemy>=2.0.0` in `pyproject.toml`, so the raw-string probe can
never succeed.

## Reproduction

1. Set up local env (`make setup`).
2. Start stack (`docker compose up -d`) so Postgres is reachable.
3. `curl -s localhost:8000/health` → `postgres` reports `"unhealthy"`,
   HTTP `503`, despite a healthy DB.
4. Alternatively, invoke `health_check` in a unit test with a mocked async
   session and assert `db.execute` is called with a `TextClause`, not a
   `str`.

## Proposed Fix

Wrap the probe in `sqlalchemy.text()`:

```python
from sqlalchemy import text
...
await db.execute(text("SELECT 1"))
```

Single-line behavioral change plus one import. No API contract change.

## Test Plan

- Add `tests/unit/test_health.py`:
  - Mock the async DB session; assert the successful path sets
    `dependencies.postgres == "healthy"` and status `200`.
  - Assert `db.execute` is called with a `sqlalchemy.TextClause`
    (regression guard against re-introducing a raw string).
  - Assert that a DB error path still reports `"unhealthy"` + `503`.
- Match existing patterns in `tests/unit/` (pytest, `-m unit`, async mocks).

## Definition of Done

- [ ] `text()` wrapper applied in `api/routes/health.py`
- [ ] Unit test added and passing (`make test-unit`)
- [ ] `make check` (ruff + black + mypy) passes
- [ ] Conventional commit: `fix(api): wrap health check DB probe in text()`
- [ ] PR opened against `ascherj/pathreview` with template filled, `Fixes #154`

## Notes / Risks

- Low risk: isolated to the health route, no schema or migration impact.
- Related nearby bug (separate issue #155): `settings.redis_host` on the
  same file does not exist on `Settings`. Out of scope for this PR.
