# Contribution Journal — PathReview

## Week 7 — Issue Selection

### Issue Link

https://github.com/ascherj/pathreview/issues/154

(Individual issue page — *"Health check DB probe passes a raw SQL string,
which fails under SQLAlchemy 2.x"*.)

### Issue Fit and Selection Reasoning

- **Tier:** This is a **Tier 1** issue (labels: `tier-1`, `bug`, `api`,
  `good first issue`).
- **Why this tier fits me:** I'm new to contributing to a large,
  multi-service codebase, so a Tier 1 issue scoped to a single file is the
  right starting point per the module guidance ("starting with a
  well-scoped Tier 1 issue is a smart move if you're newer").
- **Scope reasoning (not just "looked interesting"):** The fix is
  contained to one file, `api/routes/health.py`, and one line — no schema
  changes, no migrations, no cross-module coordination, no API contract
  change. The root cause is a well-understood SQLAlchemy 2.x behavior
  change, so the risk of scope creep is low. That lets me focus this first
  contribution on getting the *process* right (branch naming, conventional
  commits, tests, `make check`, PR template) rather than fighting
  architectural complexity. I confirmed the scope by reading the file and
  the SQLAlchemy 2.x migration notes before committing to it.

### Problem Summary (in my own words)

**What the issue is:** PathReview's `GET /health` endpoint checks whether
PostgreSQL is reachable. It runs that check by handing the plain text
`"SELECT 1"` straight to SQLAlchemy's `execute()`.

**What is currently broken:** SQLAlchemy 2.x no longer accepts a bare
string as executable SQL — it requires the string to be wrapped in
`sqlalchemy.text()`. So the probe raises
`ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly
declared as text('SELECT 1')`. That error is caught by the surrounding
`try/except`, which then marks Postgres as `"unhealthy"` and makes the
endpoint return HTTP `503` — **even when the database is completely
healthy and reachable**. Any monitor or load balancer polling `/health`
sees a false outage.

**What a successful fix accomplishes:** After the fix, the probe runs
`await db.execute(text("SELECT 1"))`, which SQLAlchemy 2.x executes
correctly. `/health` reports Postgres as `"healthy"` and returns `200`
whenever the database is actually up, so monitoring reflects real service
state instead of a permanent false-negative. A regression test locks in
that the probe uses a `text()` clause, not a raw string.

### Setup Work Completed

- Forked `ascherj/pathreview` → `Harsh05dev/pathreview`; added `upstream`
  remote.
- Created working branch `fix/154-health-db-probe-text` (per the
  `<type>/<issue-number>-<desc>` convention in `docs/CONTRIBUTING.md`).
- Set up a local Python 3.13 virtualenv and installed dev dependencies
  (`pip install -e ".[dev]"`); confirmed the unit suite collects (428
  tests). Docker is not installed locally, so the full `docker compose`
  stack / migration step is deferred to when I reproduce end-to-end.
- Removed a stray committed pip-log artifact (`=0.29.0`) from the repo
  root as an initial cleanup.
- Claimed the issue publicly:
  https://github.com/ascherj/pathreview/issues/154#issuecomment-5013752780

Detailed reproduction, root cause, fix, and test plan live in
[PLAN.md](PLAN.md).
