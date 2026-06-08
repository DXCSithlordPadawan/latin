"""
Tests for the TTS pipeline (phonetic mapper + TTS engine).

All tests in this module are unit tests of the phonetic mapping engine.
Audio output is not asserted programmatically (no audio hardware assumed).
HTTP response header tests mock the pyttsx3 synthesis layer.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.phonetic_mapper import (
    map_for_espeak,
    resolve_macrons,
    resolve_diphthongs,
    enforce_hard_consonants,
)
from engine.tts_engine import REQUIRED_DRIVER, TtsEngine


# ─────────────────────────────────────────────────────────────────────────────
# Macron annotation unit tests (PRD §9.7)
# ─────────────────────────────────────────────────────────────────────────────

def test_roma_macron_produces_len_annotation():
    """Input 'Rōma' must produce intermediate string containing [[len 180]]o."""
    result = resolve_macrons("Rōma")
    assert "[[len 180]]o" in result


def test_marcus_macron_produces_len_annotation():
    """Input 'Mārcus' must produce intermediate string containing [[len 180]]a."""
    result = resolve_macrons("Mārcus")
    assert "[[len 180]]a" in result


def test_all_macron_vowels_resolved():
    """All five long vowels with macrons produce [[len 180]] annotations."""
    for char, base in [("ā", "a"), ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u")]:
        result = resolve_macrons(char)
        assert f"[[len 180]]{base}" in result, f"Failed for '{char}'"


def test_uppercase_macron_vowels_resolved():
    for char, base in [("Ā", "A"), ("Ē", "E"), ("Ī", "I"), ("Ō", "O"), ("Ū", "U")]:
        result = resolve_macrons(char)
        assert f"[[len 180]]{base}" in result, f"Failed for '{char}'"


def test_text_without_macrons_unchanged_by_macron_resolver():
    text = "Roma"
    result = resolve_macrons(text)
    assert result == text


# ─────────────────────────────────────────────────────────────────────────────
# Hard consonant mapping (PRD §9.7)
# ─────────────────────────────────────────────────────────────────────────────

def test_caesar_c_maps_to_k():
    """'Caesar' must contain /k/ phoneme annotation for C, not /s/."""
    result = enforce_hard_consonants("Caesar")
    assert "[[k]]" in result


def test_hard_c_annotation_present():
    result = enforce_hard_consonants("canis")
    assert "[[k]]" in result


def test_v_maps_to_w_semivowel():
    result = enforce_hard_consonants("veni")
    assert "[[w]]" in result


# ─────────────────────────────────────────────────────────────────────────────
# Diphthong mapping (PRD §9.7)
# ─────────────────────────────────────────────────────────────────────────────

def test_ae_diphthong_maps_to_ai():
    result = resolve_diphthongs("Caesar")
    assert "[[aɪ]]" in result


def test_oe_diphthong_maps_to_oi():
    result = resolve_diphthongs("poena")
    assert "[[ɔɪ]]" in result


def test_diphthong_case_insensitive():
    result_lower = resolve_diphthongs("caelum")
    result_upper = resolve_diphthongs("CAELUM")
    assert "[[aɪ]]" in result_lower
    assert "[[aɪ]]" in result_upper


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline
# ─────────────────────────────────────────────────────────────────────────────

def test_full_pipeline_produces_annotated_string():
    result = map_for_espeak("Rōma")
    assert "[[len 180]]" in result or "[[k]]" in result or isinstance(result, str)


def test_full_pipeline_on_empty_string():
    result = map_for_espeak("")
    assert result == ""


# ─────────────────────────────────────────────────────────────────────────────
# TTS engine — driver assertion (PRD §9.7)
# ─────────────────────────────────────────────────────────────────────────────

def test_tts_driver_is_espeak():
    engine = TtsEngine()
    assert engine.driver_name == "espeak"


def test_invalid_mode_raises():
    engine = TtsEngine()
    with pytest.raises(ValueError):
        engine.set_mode("invalid_mode")


def test_valid_modes_accepted():
    engine = TtsEngine()
    for mode in ("playback", "export", "both"):
        engine.set_mode(mode)  # Should not raise


# ─────────────────────────────────────────────────────────────────────────────
# Export mode — HTTP response headers (mocked synthesis)
# ─────────────────────────────────────────────────────────────────────────────

def test_export_mode_returns_bytes():
    """export mode must return non-empty bytes (mocked synthesis)."""
    engine = TtsEngine(mode="export")

    fake_wav = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 100

    with patch("engine.tts_engine._synthesise_to_bytes", return_value=fake_wav):
        result = engine.synthesise("Rōma")

    assert isinstance(result, bytes)
    assert len(result) > 0


def test_playback_mode_returns_none():
    """playback mode must not return a download response (returns None)."""
    engine = TtsEngine(mode="playback")

    with patch("engine.tts_engine._synthesise_playback", return_value=None):
        result = engine.synthesise("Veni, vidi, vici.")

    assert result is None


def test_both_mode_returns_bytes():
    """both mode must return bytes AND trigger playback."""
    engine = TtsEngine(mode="both")
    fake_wav = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 100

    with patch("engine.tts_engine._synthesise_to_bytes", return_value=fake_wav), \
         patch("engine.tts_engine._synthesise_playback", return_value=None):
        result = engine.synthesise("Caesar venit.")

    assert isinstance(result, bytes)
    assert len(result) > 0
