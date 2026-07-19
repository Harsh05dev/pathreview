# Contribution Journal — PathReview

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's `GET /health` endpoint (in `api/routes/health.py`) checks that
PostgreSQL is reachable by handing the plain string `"SELECT 1"` straight to
SQLAlchemy's `execute()`. SQLAlchemy 2.x no longer accepts a bare string as
executable SQL, so the probe raises `ArgumentError` and the surrounding
`try/except` marks Postgres as `"unhealthy"`, returning HTTP `503` even when
the database is completely healthy — a permanent false outage for any monitor
polling `/health`. A successful fix wraps the query in `sqlalchemy.text()` so
the probe runs under SQLAlchemy 2.x, letting `/health` report `"healthy"` and
`200` whenever the database is actually up, with a unit test guarding against
a raw-string regression. This is a Tier 1 fix scoped to a single file in the
`api` module.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
