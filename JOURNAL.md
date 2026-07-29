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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Harsh05dev/pathreview/commit/2347ee4bbfa79cf64f827cdf6009b7fc3f203829

**Reproduction summary:**
I reproduced issue #154 with a unit test (`tests/unit/test_health_repro.py`)
that drives `health_check()` in `api/routes/health.py` with a mock async
session mimicking SQLAlchemy 2.x `execute()` semantics. The raw string
`"SELECT 1"` is rejected with `ArgumentError: Textual SQL expression
'SELECT 1' should be explicitly declared as text('SELECT 1')` (confirmed
against the installed `sqlalchemy 2.0.51`); the broad `try/except` swallows it
and the endpoint falsely reports Postgres `"unhealthy"` and returns HTTP `503`
even though the database is reachable. A second test pins the underlying 2.x
behavior directly (raw string rejected, `text("SELECT 1")` accepted as a
`TextClause`). Both tests pass against the current buggy code, so CI stays
green; they document the reproduction and will be superseded by the fix test
in Week 9.

**PLAN.md link:** https://github.com/Harsh05dev/pathreview/blob/fix/154-health-db-probe-text/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
- Nearby latent bug on the same file: `settings.redis_host` is referenced in
  the Redis probe but may not exist on `Settings` (separate issue #155) — out
  of scope for #154, will not touch it.
- Need to confirm the async-mock pattern in the Week 9 `test_health.py` matches
  the sibling tests' style in `tests/unit/` (pytest markers + `pytest-asyncio`
  strict mode, which requires an explicit `@pytest.mark.asyncio`).

## Week 9 — Solution building & PR submission

**Pull request:** https://github.com/ascherj/pathreview/pull/359 (`fix(api): wrap health check DB probe in text()`, `Fixes #154`)

**Fix commit:** https://github.com/Harsh05dev/pathreview/commit/ea34abf

**What I changed:**
- `api/routes/health.py` — imported `text` from `sqlalchemy` and changed the
  Postgres probe from `db.execute("SELECT 1")` to `db.execute(text("SELECT 1"))`.
  One-line behavioral change; no handler logic or response schema touched.
  (Project `ruff --fix` also reordered imports and dropped an unused
  `timedelta` import in the same file.)
- `tests/unit/test_health.py` — new. Happy path asserts a reachable DB reports
  `postgres == "healthy"` and that the probe is called with a `TextClause`
  (regression guard against a raw string); error path asserts a real DB failure
  still yields `"unhealthy"` + `503`.
- Removed `tests/unit/test_health_repro.py` (Week 8 scaffold, superseded).

**Verification:**
- `pytest tests/unit/test_health.py -v` → 2 passed.
- Full `pytest -m unit`: 53 failures both before and after my change — the
  failing set is byte-identical, so I introduced **0** new failures. Those 53
  are pre-existing and documented in the PR's Notes for Reviewers.
- Changed files pass `ruff check` and `black --check`. Repo-wide `make check`
  has pre-existing lint/type failures unrelated to this change (also noted in
  the PR).

**Confirmed unknowns from Week 8:**
- Risk #1 resolved: `core/database.py` `get_db` yields a real SQLAlchemy 2.x
  `AsyncSession` (via `async_sessionmaker`), so `text()` is the correct fix.
- The test asserts on `dependencies.postgres` specifically, so the unrelated
  Redis/`settings` gap (#155) does not mask the Postgres fix.

**Blockers or open questions:**
- Cannot run `make test-integration` locally (no Docker services); relied on
  unit tests + manual `curl` reasoning for the endpoint behavior.
