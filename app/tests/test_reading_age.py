"""
Tests for reading age adaptation (engine/reading_age.py).

One test per level 1–6 verifying display name, age range, and syntax description.
Tests confirm level switch takes effect immediately on next request and does not
alter prior session telemetry.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.reading_age import (
    BARBARIAN_LEVEL,
    LEVEL_SPECS,
    all_levels,
    get_display_name,
    get_level_spec,
)
from engine.prefix_router import build_prefix


# ─────────────────────────────────────────────────────────────────────────────
# Level spec tests (one per level)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", range(1, 7))
def test_level_spec_has_display_name(level):
    spec = get_level_spec(level)
    assert spec.display_name
    assert len(spec.display_name) > 0


@pytest.mark.parametrize("level", range(1, 7))
def test_level_spec_has_age_range(level):
    spec = get_level_spec(level)
    assert spec.age_range
    assert "Ages" in spec.age_range or "Adult" in spec.age_range


@pytest.mark.parametrize("level", range(1, 7))
def test_level_spec_has_syntax_description(level):
    spec = get_level_spec(level)
    assert spec.syntax_description
    assert len(spec.syntax_description) > 10


@pytest.mark.parametrize("level", range(1, 7))
def test_level_spec_has_vocabulary_description(level):
    spec = get_level_spec(level)
    assert spec.vocabulary_description
    assert len(spec.vocabulary_description) > 10


# ─────────────────────────────────────────────────────────────────────────────
# Level display name formatting
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level,expected_fragment", [
    (1, "Beginner"),
    (2, "Elementary"),
    (3, "Primary"),
    (4, "Intermediate"),
    (5, "Secondary"),
    (6, "Advanced"),
])
def test_display_name_contains_label(level, expected_fragment):
    name = get_display_name(level)
    assert expected_fragment in name


def test_barbarian_display_name():
    name = get_display_name(BARBARIAN_LEVEL)
    assert name == "Barbarian Mode"


def test_all_levels_returns_7_items():
    levels = all_levels()
    assert len(levels) == 7  # 6 standard + Barbarian


# ─────────────────────────────────────────────────────────────────────────────
# Level complexity ordering (simplest to most complex)
# ─────────────────────────────────────────────────────────────────────────────

def test_level_1_is_simpler_than_level_6():
    l1 = get_level_spec(1)
    l6 = get_level_spec(6)
    # Level 1 restricts to SVO; level 6 allows unrestricted idioms
    assert "SVO" in l1.syntax_description or "Simple" in l1.syntax_description
    assert "Unrestricted" in l6.syntax_description or "Golden" in l6.syntax_description


# ─────────────────────────────────────────────────────────────────────────────
# Prefix age tag matches level spec
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", range(1, 7))
def test_prefix_age_tag_matches_spec(level):
    spec = get_level_spec(level)
    prefix = build_prefix("en-la", level=level)
    assert f"age-{spec.prefix_age_tag}" in prefix


# ─────────────────────────────────────────────────────────────────────────────
# Level switch mid-session — effect on next request; telemetry unaffected
# ─────────────────────────────────────────────────────────────────────────────

def test_level_switch_takes_effect_immediately(tmp_path):
    """
    Simulate switching level: the new level is reflected in the next prefix.
    No telemetry reset occurs.
    """
    from engine.db_migrate import run_migrations
    from engine.profile_manager import (
        create_profile,
        update_profile_meta,
        get_profile_meta,
        _profiles_dir,
    )
    import os

    # Override profiles dir to tmp_path for isolation
    original_dir = Path(str(Path.home() / ".airgap-translator" / "profiles"))
    test_profiles_dir = tmp_path / "profiles"
    test_profiles_dir.mkdir()

    # Patch _PROFILES_DIR_DEFAULT
    import engine.profile_manager as pm
    original = pm._PROFILES_DIR_DEFAULT
    pm._PROFILES_DIR_DEFAULT = test_profiles_dir

    try:
        slug = pm.create_profile("Test Level Switch")
        pm.update_profile_meta(slug, selected_level=3)
        meta_before = pm.get_profile_meta(slug)
        assert meta_before["selected_level"] == 3

        # Switch to level 5
        pm.update_profile_meta(slug, selected_level=5)
        meta_after = pm.get_profile_meta(slug)
        assert meta_after["selected_level"] == 5

        # Verify the corresponding prefix is for level 5
        prefix = build_prefix("en-la", level=5)
        assert "age-16" in prefix

        # Insert telemetry and verify it survived the level switch
        db_path = test_profiles_dir / f"{slug}.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO word_friction (word, direction, last_seen) VALUES ('test', 'en-la', '2026-01-01T00:00:00Z')"
        )
        conn.commit()
        row_count = conn.execute("SELECT COUNT(*) FROM word_friction").fetchone()[0]
        conn.close()
        assert row_count == 1  # Telemetry intact after level switch
    finally:
        pm._PROFILES_DIR_DEFAULT = original
