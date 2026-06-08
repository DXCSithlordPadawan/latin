"""
Schema migration runner.

Compares stored schema_version against the application's declared target.
Applies sequential migration scripts from engine/migrations/<N>.sql.
On failure, rolls back the transaction and exits with non-zero code.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
TARGET_SCHEMA_VERSION = 1


def _migrations_path() -> Path:
    return MIGRATIONS_DIR


def _read_current_version(conn: sqlite3.Connection) -> int | None:
    """Return the version stored in schema_version, or None if table absent."""
    try:
        row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        return int(row[0]) if row else None
    except sqlite3.OperationalError:
        return None


def _apply_migration(conn: sqlite3.Connection, version: int) -> None:
    script_path = _migrations_path() / f"{version:03d}.sql"
    if not script_path.exists():
        raise FileNotFoundError(f"Migration script not found: {script_path}")
    sql = script_path.read_text(encoding="utf-8")
    conn.executescript(sql)


def run_migrations(db_path: str | os.PathLike) -> None:
    """
    Open *db_path* and apply any pending migrations.

    Exits the process with code 1 on version-future or migration failure.
    """
    db_path = Path(db_path)

    # Open — a fresh (empty) file is created by sqlite3.connect if absent.
    try:
        conn = sqlite3.connect(str(db_path))
    except sqlite3.DatabaseError as exc:
        print(f"ERROR: Cannot open database {db_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        # Integrity check — catches corrupt files
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result[0] != "ok":
                print(
                    f"ERROR: Database integrity check failed for {db_path}: {result[0]}",
                    file=sys.stderr,
                )
                sys.exit(1)
        except sqlite3.DatabaseError as exc:
            print(
                f"ERROR: Database integrity check error for {db_path}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

        current = _read_current_version(conn)
        if current is None:
            # Fresh database — no schema_version table yet
            current = 0

        if current > TARGET_SCHEMA_VERSION:
            print(
                f"ERROR: Database schema version {current} is newer than application "
                f"target version {TARGET_SCHEMA_VERSION}. "
                "Downgrading is not supported. Restore from backup or use a newer image.",
                file=sys.stderr,
            )
            sys.exit(1)

        if current == TARGET_SCHEMA_VERSION:
            return  # Nothing to do

        # Apply each pending migration sequentially
        for version in range(current + 1, TARGET_SCHEMA_VERSION + 1):
            try:
                _apply_migration(conn, version)
                # executescript auto-commits; update schema_version for versions > 1
                if version > 1:
                    conn.execute(
                        "UPDATE schema_version SET version = ?", (version,)
                    )
                    conn.commit()
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                print(
                    f"ERROR: Migration to version {version} failed: {exc}",
                    file=sys.stderr,
                )
                sys.exit(1)

    finally:
        try:
            conn.close()
        except Exception:
            pass
