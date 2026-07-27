"""Week 8 reproduction for issue #154.

Documents the reproduced bug: ``GET /health`` probes PostgreSQL with the raw
string ``"SELECT 1"``. Under SQLAlchemy 2.x, ``Session.execute()`` rejects a
bare string with ``ArgumentError``. Because the probe sits inside a broad
``try/except``, the error is swallowed and Postgres is falsely marked
``"unhealthy"`` (HTTP 503) even when the database is fully reachable.

This test reproduces that behavior and PASSES against the current (buggy) code
so CI stays green. In Week 9 it is superseded by ``test_health.py``, which
asserts the fixed behavior (probe wrapped in ``sqlalchemy.text()``).

Root cause: api/routes/health.py -> health_check() -> ``await db.execute("SELECT 1")``.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


class _FakeSQLAlchemy2xSession:
    """Minimal async DB session mimicking SQLAlchemy 2.x execute() semantics.

    A raw ``str`` statement raises ``ArgumentError`` (as real 2.x does); a
    ``TextClause`` (produced by ``sqlalchemy.text()``) is accepted.
    """

    def __init__(self) -> None:
        self.received = None

    async def execute(self, statement):
        self.received = statement
        if isinstance(statement, str):
            raise ArgumentError(
                "Textual SQL expression 'SELECT 1' should be explicitly "
                "declared as text('SELECT 1')"
            )
        if isinstance(statement, TextClause):
            return object()
        raise ArgumentError(f"unexpected statement type: {type(statement)!r}")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_raw_string_probe_marks_postgres_unhealthy():
    """REPRO #154: raw-string DB probe falsely reports Postgres unhealthy.

    With a healthy (mocked) database, the endpoint should report Postgres as
    ``"healthy"``. Instead, the raw-string probe raises under SQLAlchemy 2.x,
    is swallowed, and Postgres is reported ``"unhealthy"`` with HTTP 503.
    """
    db = _FakeSQLAlchemy2xSession()

    with pytest.raises(HTTPException) as excinfo:
        await health_check(db=db)

    detail = excinfo.value.detail
    # The bug: the raw string reached execute() and was rejected...
    assert isinstance(db.received, str)
    # ...so a fully-reachable DB is falsely reported unhealthy with 503.
    assert excinfo.value.status_code == 503
    assert detail["dependencies"]["postgres"] == "unhealthy"


@pytest.mark.unit
def test_sqlalchemy_2x_rejects_raw_string_accepts_text():
    """REPRO #154: pin down the SQLAlchemy 2.x behavior driving the bug."""
    from sqlalchemy.sql import coercions, roles

    with pytest.raises(ArgumentError):
        coercions.expect(roles.StatementRole, "SELECT 1")

    stmt = coercions.expect(roles.StatementRole, text("SELECT 1"))
    assert isinstance(stmt, TextClause)
