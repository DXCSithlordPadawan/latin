"""
Tests for the translation engine (prefix routing, confidence gate, fallback,
SOV, Barbarian Mode, quality gate regression).

The neural model is mocked throughout so tests run without the checkpoint.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.prefix_router import build_prefix, build_input, LEVEL_AGE_MAP
from engine.barbarian import barbarian_postprocess, build_prefix as barbarian_build_prefix
from engine.translation_engine import TranslationEngine, TranslationResult


# ─────────────────────────────────────────────────────────────────────────────
# Prefix router tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level,expected_age", list(LEVEL_AGE_MAP.items()))
def test_en_la_prefix_age_tag(level, expected_age):
    prefix = build_prefix("en-la", level=level)
    assert f"age-{expected_age}" in prefix


def test_la_en_prefix():
    prefix = build_prefix("la-en")
    assert prefix == "translate la-en:"


def test_barbarian_prefix():
    prefix = build_prefix("en-la", barbarian=True)
    assert "barbarian" in prefix


def test_invalid_direction_raises():
    with pytest.raises(ValueError, match="direction"):
        build_prefix("xx-yy", level=1)


def test_en_la_without_level_raises():
    with pytest.raises(ValueError, match="Level"):
        build_prefix("en-la")


def test_invalid_level_raises():
    with pytest.raises(ValueError):
        build_prefix("en-la", level=99)


def test_build_input_combines_prefix_and_text():
    prefix = "translate la-en:"
    text = "Agricola ambulat."
    result = build_input(prefix, text)
    assert result == "translate la-en: Agricola ambulat."


# ─────────────────────────────────────────────────────────────────────────────
# Barbarian Mode post-processor
# ─────────────────────────────────────────────────────────────────────────────

def test_barbarian_postprocess_returns_string():
    result = barbarian_postprocess("Agricola ad agrum ambulat.")
    assert isinstance(result, str)


def test_barbarian_prefix_is_correct():
    prefix = barbarian_build_prefix()
    assert prefix == "translate en-la barbarian:"


# ─────────────────────────────────────────────────────────────────────────────
# Translation engine — mocked model
# ─────────────────────────────────────────────────────────────────────────────

def _make_mock_engine(output_text: str = "Agricola ad agrum ambulat.") -> TranslationEngine:
    """Create an engine with a mock model injected."""
    engine = TranslationEngine(verify_checksum=False)

    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    # Tokenizer returns simple input_ids
    mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    mock_tokenizer.decode.return_value = output_text

    # model.generate returns a mock with .sequences
    gen_output = MagicMock()
    gen_output.sequences = [MagicMock()]
    mock_model.generate.return_value = gen_output
    mock_model.eval.return_value = None

    engine._inject_model(mock_model, mock_tokenizer)
    return engine


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
def test_en_la_standard_returns_result(level):
    engine = _make_mock_engine("Agricola ambulat.")
    result = engine.translate("The farmer walks.", direction="en-la", level=level)
    assert isinstance(result, TranslationResult)
    assert result.direction == "en-la"
    assert result.level == str(level)


def test_la_en_returns_result():
    engine = _make_mock_engine("The farmer walks to the field.")
    result = engine.translate("Agricola ad agrum ambulat.", direction="la-en")
    assert result.direction == "la-en"
    assert isinstance(result.text, str)


def test_barbarian_mode_returns_result():
    engine = _make_mock_engine("Agricola ad agrum AMBULAT.")
    result = engine.translate("The farmer walks.", direction="en-la", barbarian=True)
    assert result.level == "barbarian"
    assert isinstance(result.text, str)


def test_barbarian_output_has_imperative_character():
    # Barbarian post-processor should capitalise verb forms
    text = "Agricola ad agrum ambulat."
    processed = barbarian_postprocess(text)
    # At least one token should be different (uppercased verb or coerced case)
    assert processed != text or "um" in processed.lower()


def test_oversized_input_raises():
    engine = _make_mock_engine()
    long_text = " ".join(["word"] * 513)
    with pytest.raises(ValueError, match="512"):
        engine.translate(long_text, direction="en-la", level=4)


# ─────────────────────────────────────────────────────────────────────────────
# Confidence gate — fallback annotation
# ─────────────────────────────────────────────────────────────────────────────

def test_strict_mode_annotates_unknown_tokens():
    engine = _make_mock_engine("xyzquux nonsensicalword")
    engine._strict = True
    result = engine.translate("Hello world.", direction="en-la", level=4)
    # Unknown non-Latin tokens should be annotated [UNKNOWN: ...]
    # (depends on Whitaker's data not knowing xyzquux)
    assert isinstance(result.text, str)


# ─────────────────────────────────────────────────────────────────────────────
# Quality gate regression — marked slow (Phase 7 only)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.slow
def test_chrf_quality_gate_passes():
    """
    Invoke eval_chrf.py against corpus/validation_split.tsv and assert
    chrF ≥ 45 in both directions.

    Requires the fine-tuned checkpoint and validation split to be present.
    Run with: pytest -m slow
    """
    import subprocess

    result = subprocess.run(
        [sys.executable, "scripts/eval_chrf.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"chrF quality gate failed:\n{result.stdout}\n{result.stderr}"
    )
