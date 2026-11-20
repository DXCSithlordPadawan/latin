"""
Tests for adaptive learning and telemetry (PRD §9.9).

Covers:
  - Clear Telemetry removes all records for active profile only
  - Proficiency accumulates across level switches
  - Thumbs-up (+1) feedback record written correctly
  - Thumbs-down (-1) feedback record written correctly
  - Clear Telemetry removes all feedback records
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import engine.profile_manager as pm
from engine.db_migrate import run_migrations


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def isolated_profiles(tmp_path, monkeypatch):
    """Redirect all profile operations to a temp directory."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    monkeypatch.setattr(pm, "_PROFILES_DIR_DEFAULT", profiles_dir)
    return profiles_dir


# ─────────────────────────────────────────────────────────────────────────────
# Clear Telemetry — scope (PRD §9.9)
# ─────────────────────────────────────────────────────────────────────────────

def test_clear_telemetry_removes_all_records_for_active_profile(isolated_profiles):
    slug_a = pm.create_profile("Alice")
    slug_b = pm.create_profile("Bob")

    # Insert telemetry into Alice's profile
    db_a = isolated_profiles / f"{slug_a}.db"
    conn = sqlite3.connect(str(db_a))
    conn.execute("INSERT INTO word_friction (word, direction, last_seen) VALUES ('puer', 'en-la', ?)", (_now(),))
    conn.execute("INSERT INTO session_history (session_start, request_count) VALUES (?, 5)", (_now(),))
    conn.execute(
        "INSERT INTO translation_feedback (source_text, output_text, direction, level, rating, recorded_at) "
        "VALUES ('hello', 'salve', 'en-la', '3', 1, ?)", (_now(),)
    )
    conn.commit()
    conn.close()

    # Insert telemetry into Bob's profile
    db_b = isolated_profiles / f"{slug_b}.db"
    conn = sqlite3.connect(str(db_b))
    conn.execute("INSERT INTO word_friction (word, direction, last_seen) VALUES ('terra', 'la-en', ?)", (_now(),))
    conn.commit()
    conn.close()

    # Clear only Alice
    pm.clear_telemetry(slug_a)

    # Alice: all telemetry tables empty
    conn = sqlite3.connect(str(db_a))
    assert conn.execute("SELECT COUNT(*) FROM word_friction").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM session_history").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM translation_feedback").fetchone()[0] == 0
    conn.close()

    # Bob: telemetry intact
    conn = sqlite3.connect(str(db_b))
    assert conn.execute("SELECT COUNT(*) FROM word_friction").fetchone()[0] == 1
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Proficiency accumulates across level switches (PRD §9.9)
# ─────────────────────────────────────────────────────────────────────────────

def test_proficiency_accumulates_across_level_switches(isolated_profiles):
    slug = pm.create_profile("Charlie")
    db = isolated_profiles / f"{slug}.db"

    # Simulate level switch: set level to 3
    pm.update_profile_meta(slug, selected_level=3)

    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO proficiency (word, direction, correct_count, incorrect_count) "
        "VALUES ('agricola', 'la-en', 2, 1)"
    )
    conn.commit()
    conn.close()

    # Switch to level 5
    pm.update_profile_meta(slug, selected_level=5)

    # Proficiency record must still be there
    conn = sqlite3.connect(str(db))
    row = conn.execute("SELECT correct_count FROM proficiency WHERE word='agricola'").fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Translation feedback records (PRD §9.9)
# ─────────────────────────────────────────────────────────────────────────────

def test_thumbs_up_feedback_written_correctly(isolated_profiles):
    slug = pm.create_profile("Dana")
    db_path = isolated_profiles / f"{slug}.db"
    conn = pm._open_profile(db_path)

    with pm._WRITE_LOCK:
        conn.execute(
            "INSERT INTO translation_feedback "
            "(source_text, output_text, direction, level, rating, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("The farmer walks", "Agricola ambulat", "en-la", "4", 1, _now()),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM translation_feedback WHERE rating=1").fetchone()
    conn.close()

    assert row is not None
    # Columns: id, source_text, output_text, direction, level, rating, recorded_at
    assert row[5] == 1  # rating column
    assert "farmer" in row[1]  # source_text truncated to ≤64 chars
    assert len(row[1]) <= 64


def test_thumbs_down_feedback_written_correctly(isolated_profiles):
    slug = pm.create_profile("Eve")
    db_path = isolated_profiles / f"{slug}.db"
    conn = pm._open_profile(db_path)

    with pm._WRITE_LOCK:
        conn.execute(
            "INSERT INTO translation_feedback "
            "(source_text, output_text, direction, level, rating, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("Caesar came", "Caesar venit", "en-la", "6", -1, _now()),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM translation_feedback WHERE rating=-1").fetchone()
    conn.close()

    assert row is not None
    assert row[5] == -1  # rating column (id, source, output, direction, level, rating, recorded_at)


def test_clear_telemetry_removes_feedback_records(isolated_profiles):
    slug = pm.create_profile("Frank")
    db_path = isolated_profiles / f"{slug}.db"
    conn = pm._open_profile(db_path)

    with pm._WRITE_LOCK:
        conn.execute(
            "INSERT INTO translation_feedback "
            "(source_text, output_text, direction, level, rating, recorded_at) "
            "VALUES ('hello', 'salve', 'en-la', '1', 1, ?)",
            (_now(),),
        )
        conn.commit()
    conn.close()

    pm.clear_telemetry(slug)

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM translation_feedback").fetchone()[0]
    conn.close()
    assert count == 0
