"""
Whitaker's Words morphological analyser.

Loads the Whitaker's Words dictionary data and provides:
  - principal_parts_lookup(word) → list of morphological analyses
  - fallback_annotate(token) → "[FALLBACK: <token>]" annotation string

Used as the confidence-gated fallback when mT5 confidence < 0.6.
Also used in the LA→EN pre-processing pipeline for principal-parts lookup.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# Path to bundled Whitaker's Words data within the container image
WHITAKER_DATA_DIR = Path(__file__).parent.parent / "data" / "whitakers_words"
FALLBACK_CONFIDENCE_THRESHOLD = 0.6

# Pre-compiled regex for basic Latin word tokenisation
_LATIN_TOKEN_RE = re.compile(r"[A-Za-zāēīōūĀĒĪŌŪ]+", re.UNICODE)


class WhitakersWordsMorphAnalyser:
    """
    Lightweight wrapper around Whitaker's Words dictionary data.

    The data directory should contain:
      - DICTLINE.GEN (main dictionary entries in Whitaker's format)
      - STEMLIST.GEN (stem list)

    Falls back to returning an empty analysis list if the data directory
    is absent (useful for testing without the full corpus bundle).
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or WHITAKER_DATA_DIR
        self._entries: dict[str, list[str]] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        dictline = self._data_dir / "DICTLINE.GEN"
        if not dictline.exists():
            # Data not available; analyser will return empty results
            self._loaded = False
            return

        with open(dictline, encoding="latin-1", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("--"):
                    continue
                parts = line.split()
                if parts:
                    stem = parts[0].lower()
                    existing = self._entries.get(stem, [])
                    existing.append(line)
                    self._entries[stem] = existing
        self._loaded = True

    def principal_parts_lookup(self, word: str) -> list[str]:
        """Return known morphological analyses for *word* (lowercased lookup)."""
        if not self._loaded:
            return []
        key = word.lower().strip()
        return self._entries.get(key, [])

    def is_known(self, word: str) -> bool:
        return bool(self.principal_parts_lookup(word))

    @staticmethod
    def fallback_annotate(token: str) -> str:
        return f"[FALLBACK: {token}]"


def annotate_low_confidence_tokens(
    tokens: list[str],
    confidences: list[float],
    analyser: WhitakersWordsMorphAnalyser,
    threshold: float = FALLBACK_CONFIDENCE_THRESHOLD,
) -> list[str]:
    """
    For each token with confidence < threshold, attempt Whitaker's lookup.
    If found, keep the token; if not, annotate with [FALLBACK: token].
    Returns the annotated token list.
    """
    result = []
    for token, conf in zip(tokens, confidences):
        if conf < threshold:
            if analyser.is_known(token):
                result.append(token)
            else:
                result.append(analyser.fallback_annotate(token))
        else:
            result.append(token)
    return result


# Module-level singleton (lazy-initialised)
_ANALYSER: WhitakersWordsMorphAnalyser | None = None


def get_analyser(data_dir: Path | None = None) -> WhitakersWordsMorphAnalyser:
    global _ANALYSER
    if _ANALYSER is None:
        _ANALYSER = WhitakersWordsMorphAnalyser(data_dir)
    return _ANALYSER
