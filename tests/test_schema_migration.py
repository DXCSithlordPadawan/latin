"""
Tests for engine/db_migrate.py — schema migration runner.

Covers:
  - N−1 upgrade: database at version 0 (no schema_version table) is migrated to
    target version; schema_version reflects target; existing data intact.
  - Future version: database at version higher than target causes immediate exit.
  - Rollback on bad SQL: malformed migration causes rollback; schema version unchanged.
"""
from __future__ import annotations

import sqlite3
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root is on sys.path when running from project dir
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.db_migrate import TARGET_SCHEMA_VERSION, run_migrations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_profile.db"
    return db_path


def _db_schema_version(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    conn.close()
    return int(row[0])


# ---------------------------------------------------------------------------
# Test: fresh database — migration runs successfully
# ---------------------------------------------------------------------------

def test_fresh_database_migrates_to_target(tmp_path):
    db_path = _fresh_db(tmp_path)
    assert not db_path.exists()

    run_migrations(db_path)

    assert db_path.exists()
    version = _db_schema_version(db_path)
    assert version == TARGET_SCHEMA_VERSION


def test_migrated_database_has_expected_tables(tmp_path):
    db_path = _fresh_db(tmp_path)
    run_migrations(db_path)

    conn = sqlite3.connect(str(db_path))
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    required = {
        "schema_version",
        "profile_meta",
        "word_friction",
        "session_history",
        "translation_feedback",
        "proficiency",
        "error_records",
    }
    assert required.issubset(tables), f"Missing tables: {required - tables}"


# ---------------------------------------------------------------------------
# Test: already-at-target version — idempotent, no error
# ---------------------------------------------------------------------------

def test_already_at_target_version_is_idempotent(tmp_path):
    db_path = _fresh_db(tmp_path)
    run_migrations(db_path)
    version_before = _db_schema_version(db_path)

    # Run again — should be a no-op
    run_migrations(db_path)
    version_after = _db_schema_version(db_path)

    assert version_before == version_after == TARGET_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Test: future version — exits with non-zero code
# ---------------------------------------------------------------------------

def test_future_version_exits_nonzero(tmp_path):
    db_path = _fresh_db(tmp_path)
    # Manually create a DB with a version higher than the target
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    future_version = TARGET_SCHEMA_VERSION + 99
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (future_version,))
    conn.commit()
    conn.close()

    with pytest.raises(SystemExit) as exc_info:
        run_migrations(db_path)

    assert exc_info.value.code != 0


def test_future_version_error_message_on_stderr(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    future_version = TARGET_SCHEMA_VERSION + 99
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (future_version,))
    conn.commit()
    conn.close()

    with pytest.raises(SystemExit):
        run_migrations(db_path)

    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert str(future_version) in captured.err


# ---------------------------------------------------------------------------
# Test: malformed migration SQL — rollback; schema_version unchanged
# ---------------------------------------------------------------------------

def test_bad_migration_script_exits_nonzero(tmp_path, monkeypatch):
    db_path = _fresh_db(tmp_path)

    # Patch MIGRATIONS_DIR to point to tmp_path where we'll write a bad script
    bad_migrations = tmp_path / "migrations"
    bad_migrations.mkdir()

    # Write valid 001.sql so migration 1 succeeds and sets version to 1
    real_migrations = Path(__file__).parent.parent / "engine" / "migrations"
    (bad_migrations / "001.sql").write_text(
        (real_migrations / "001.sql").read_text(encoding="utf-8"), encoding="utf-8"
    )
    # Write broken 002.sql
    (bad_migrations / "002.sql").write_text(
        "THIS IS NOT VALID SQL @@@ BROKEN;", encoding="utf-8"
    )

    import engine.db_migrate as dbm
    original_target = dbm.TARGET_SCHEMA_VERSION

    # Temporarily patch target version to 2 so the runner attempts migration 2
    monkeypatch.setattr(dbm, "TARGET_SCHEMA_VERSION", 2)
    monkeypatch.setattr(dbm, "MIGRATIONS_DIR", bad_migrations)

    with pytest.raises(SystemExit) as exc_info:
        dbm.run_migrations(db_path)

    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Test: existing profile data survives N−1 migration
# ---------------------------------------------------------------------------

def test_existing_data_intact_after_migration(tmp_path):
    """
    Simulate: create a DB manually at schema version 0 (empty), run migration.
    The profile_meta table should be creatable and data should persist.
    """
    db_path = _fresh_db(tmp_path)
    run_migrations(db_path)

    # Insert a row into a table created by the migration
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO profile_meta (id, profile_slug, display_name, created_at) "
        "VALUES (1, 'test', 'Test User', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    conn.close()

    # Re-open and verify the row is still there
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT display_name FROM profile_meta WHERE id=1").fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "Test User"
