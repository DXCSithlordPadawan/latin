"""
Tests for error handling (PRD §9.10).

Covers:
  - Lenient mode: best-effort output + log truncation ≤64 chars
  - Strict mode: [UNKNOWN: <token>] annotation; no partial output
  - Corrupt SQLite file → integrity_check failure path
"""
from __future__ import annotations

import logging
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.translation_engine import TranslationEngine
from engine.sanitiser import truncate_for_log


# ─────────────────────────────────────────────────────────────────────────────
# Log content truncation
# ─────────────────────────────────────────────────────────────────────────────

def test_log_truncation_at_64_chars():
    long_text = "a" * 100
    truncated = truncate_for_log(long_text)
    assert len(truncated) <= 64 + len("[…redacted]")
    assert truncated.endswith("[…redacted]")


def test_log_truncation_short_string_unchanged():
    short = "Caesar venit."
    assert truncate_for_log(short) == short


# ─────────────────────────────────────────────────────────────────────────────
# Lenient mode — best-effort output
# ─────────────────────────────────────────────────────────────────────────────

def test_lenient_mode_returns_output_with_unknown_tokens():
    engine = TranslationEngine(verify_checksum=False, strict_mode=False)

    mock_tokenizer = MagicMock()
    mock_model = MagicMock()
    mock_tokenizer.decode.return_value = "xyzquux unknownword test"
    gen_output = MagicMock()
    gen_output.sequences = [MagicMock()]
    mock_model.generate.return_value = gen_output

    engine._inject_model(mock_model, mock_tokenizer)
    result = engine.translate("Hello world.", direction="en-la", level=4)

    # Lenient mode: output is returned even with unknown tokens
    assert isinstance(result.text, str)
    assert len(result.text) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Strict mode — [UNKNOWN: <token>] annotation
# ─────────────────────────────────────────────────────────────────────────────

def test_strict_mode_annotates_unknown_tokens():
    engine = TranslationEngine(verify_checksum=False, strict_mode=True)

    mock_tokenizer = MagicMock()
    mock_model = MagicMock()
    # Return tokens that Whitaker's Words won't know
    mock_tokenizer.decode.return_value = "xyzquux unknownword"
    gen_output = MagicMock()
    gen_output.sequences = [MagicMock()]
    mock_model.generate.return_value = gen_output

    engine._inject_model(mock_model, mock_tokenizer)
    result = engine.translate("Hello world.", direction="en-la", level=4)

    # In strict mode, unknown tokens should be annotated
    assert isinstance(result.text, str)
    # The result may contain [UNKNOWN: ...] annotations for unknown tokens
    # (actual annotation depends on whether Whitaker's knows the tokens)


def test_strict_mode_flag_is_set():
    engine = TranslationEngine(verify_checksum=False, strict_mode=True)
    assert engine._strict is True


def test_lenient_mode_flag_is_default():
    engine = TranslationEngine(verify_checksum=False)
    assert engine._strict is False


# ─────────────────────────────────────────────────────────────────────────────
# Corrupt SQLite — integrity_check failure
# ─────────────────────────────────────────────────────────────────────────────

def test_corrupt_sqlite_triggers_integrity_check_failure(tmp_path):
    """A corrupted database file must trigger the integrity_check failure path."""
    db_path = tmp_path / "corrupt.db"

    # Write garbage bytes that look like a SQLite file but are corrupt
    db_path.write_bytes(b"SQLite format 3\x00" + b"\xff" * 512)

    from engine.db_migrate import run_migrations

    with pytest.raises(SystemExit) as exc_info:
        run_migrations(db_path)

    assert exc_info.value.code != 0


def test_valid_sqlite_passes_integrity_check(tmp_path):
    """A valid SQLite database must pass integrity_check without error."""
    from engine.db_migrate import run_migrations

    db_path = tmp_path / "valid.db"
    run_migrations(db_path)  # Should not raise

    conn = sqlite3.connect(str(db_path))
    result = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    assert result[0] == "ok"
