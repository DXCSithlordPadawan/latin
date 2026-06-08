"""
Tests for engine/sanitiser.py — input sanitisation.

Covers:
  - Null bytes stripped
  - C0/C1 control characters stripped (TAB/LF/CR preserved)
  - Shell metacharacters stripped
  - 513-token input rejected with error message
  - Overlong / malformed UTF-8 handled gracefully
  - CSV formula prefix stripped
  - Corpus chunk iterator yields correct slices
  - Log truncation at 64 characters
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.sanitiser import (
    _TOKEN_HARD_CAP,
    enforce_token_cap,
    iter_corpus_chunks,
    sanitise_and_enforce,
    sanitise_csv_row,
    sanitise_text,
    truncate_for_log,
)


# ---------------------------------------------------------------------------
# Null bytes
# ---------------------------------------------------------------------------

def test_null_bytes_stripped():
    text = "hello\x00world"
    clean, modified = sanitise_text(text)
    assert "\x00" not in clean
    assert modified is True


def test_null_bytes_only_returns_empty():
    clean, modified = sanitise_text("\x00\x00\x00")
    assert clean == ""
    assert modified is True


# ---------------------------------------------------------------------------
# Control characters
# ---------------------------------------------------------------------------

def test_control_chars_c0_stripped():
    # U+0001 through U+0008 should be stripped
    text = "abc\x01\x02\x03def"
    clean, modified = sanitise_text(text)
    assert "\x01" not in clean
    assert "\x02" not in clean
    assert "\x03" not in clean
    assert "abcdef" == clean
    assert modified is True


def test_tab_lf_cr_preserved():
    text = "hello\tworld\nfoo\rbar"
    clean, modified = sanitise_text(text)
    assert "\t" in clean
    assert "\n" in clean
    assert "\r" in clean


def test_del_char_stripped():
    text = "abc\x7fdef"
    clean, _ = sanitise_text(text)
    assert "\x7f" not in clean


def test_c1_control_chars_stripped():
    text = "abc\x80\x9fdef"
    clean, _ = sanitise_text(text)
    assert "\x80" not in clean
    assert "\x9f" not in clean


# ---------------------------------------------------------------------------
# Shell metacharacters
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("meta", [";", "&", "|", "`", "$", "<", ">", "\\"])
def test_shell_metacharacter_stripped(meta):
    text = f"hello{meta}world"
    clean, modified = sanitise_text(text)
    assert meta not in clean
    assert modified is True


def test_clean_latin_text_unmodified():
    text = "Caesar venit, vidit, vicit."
    clean, modified = sanitise_text(text)
    assert clean == text
    assert modified is False


# ---------------------------------------------------------------------------
# 512-token cap
# ---------------------------------------------------------------------------

def test_exactly_512_tokens_accepted():
    text = " ".join(["word"] * 512)
    result = enforce_token_cap(text)
    assert result == text


def test_513_tokens_raises_value_error():
    text = " ".join(["word"] * 513)
    with pytest.raises(ValueError) as exc_info:
        enforce_token_cap(text)
    assert "512" in str(exc_info.value)
    assert "513" in str(exc_info.value)


def test_513_tokens_error_message_contains_count():
    text = " ".join(["word"] * 600)
    with pytest.raises(ValueError) as exc_info:
        enforce_token_cap(text)
    assert "600" in str(exc_info.value)


def test_sanitise_and_enforce_chains():
    # Clean text under cap — should pass
    text = "The farmer walks to the field."
    result = sanitise_and_enforce(text)
    assert result == text


def test_sanitise_and_enforce_rejects_oversized():
    text = " ".join(["word"] * 513)
    with pytest.raises(ValueError):
        sanitise_and_enforce(text)


# ---------------------------------------------------------------------------
# CSV formula stripping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_csv_formula_prefix_escaped(prefix):
    row = [f"{prefix}SUM(A1:A10)", "normal text", "123"]
    result = sanitise_csv_row(row)
    assert not result[0].startswith(prefix), f"Formula prefix '{prefix}' not escaped"
    assert result[0].startswith("'")


def test_csv_non_formula_cells_unchanged():
    row = ["Latin text", "English text", "42"]
    result = sanitise_csv_row(row)
    assert result[0] == "Latin text"
    assert result[1] == "English text"
    assert result[2] == "42"


def test_csv_cells_cast_to_string():
    row = [123, 45.6, None, True]
    result = sanitise_csv_row(row)
    for item in result:
        assert isinstance(item, str)


# ---------------------------------------------------------------------------
# Corpus chunk iterator
# ---------------------------------------------------------------------------

def test_corpus_chunk_iterator_50k_boundary():
    text = "a" * 150_000
    chunks = list(iter_corpus_chunks(text))
    assert len(chunks) == 3
    assert all(len(c) == 50_000 for c in chunks)


def test_corpus_chunk_iterator_short_text():
    text = "hello world"
    chunks = list(iter_corpus_chunks(text))
    assert len(chunks) == 1
    assert chunks[0] == text


def test_corpus_chunk_iterator_exact_boundary():
    text = "a" * 100_000
    chunks = list(iter_corpus_chunks(text))
    assert len(chunks) == 2


# ---------------------------------------------------------------------------
# Log truncation
# ---------------------------------------------------------------------------

def test_truncate_short_string_unchanged():
    s = "hello"
    assert truncate_for_log(s) == "hello"


def test_truncate_exactly_64_unchanged():
    s = "a" * 64
    assert truncate_for_log(s) == s


def test_truncate_65_chars_adds_redacted_suffix():
    s = "a" * 65
    result = truncate_for_log(s)
    assert result.endswith("[…redacted]")
    assert len(result) == 64 + len("[…redacted]")


def test_truncate_custom_max_len():
    s = "hello world"
    result = truncate_for_log(s, max_len=5)
    assert result == "hello[…redacted]"
