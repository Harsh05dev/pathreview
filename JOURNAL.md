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

**Issue fit and selection reasoning:**
I chose this as a **Tier 1** issue because it's my first contribution to a
large, multi-service codebase, and the module guidance recommends a
well-scoped Tier 1 issue for newcomers. The scope genuinely fits: the fix is
contained to a single file (`api/routes/health.py`) and effectively one line,
with no schema changes, no database migrations, no cross-module coordination,
and no change to the API contract — so the risk of scope surprises in Week 9
is low. The root cause is a well-documented SQLAlchemy 2.x behavior change,
which means the work is bounded and understandable rather than open-ended. I
estimate 3–6 hours total (fix + unit test + `make check`), which is realistic
for the Week 8–9 window. This lets my first contribution focus on getting the
*process* right (branch naming, conventional commits, tests, PR template)
instead of fighting architectural complexity.

**"Is this right for me?" checklist (all confirmed before claiming):**
- [x] Part 1 — I can explain the issue in my own words; the affected area is
  the `api` module; I can describe a concrete before/after (false `503` while
  DB is up → `200` healthy after the fix).
- [x] Part 2 — Tier 1 is a realistic match for a first contribution; I am not
  reaching for a higher tier to "challenge myself."
- [x] Part 3 — I located and read the exact code (`api/routes/health.py:31`,
  `await db.execute("SELECT 1")`) and its surrounding handler; I noted there
  is no `tests/unit/test_health.py` yet, so I will add one and matched the
  async-mock/pytest pattern used by sibling tests in `tests/unit/`.
- [x] Part 4 — Checked issue comments/ledger claims and am fine with the
  count; scope is realistic for Weeks 8–9; the issue has no open blockers or
  dependencies.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
