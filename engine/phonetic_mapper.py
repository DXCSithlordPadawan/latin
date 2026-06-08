"""
Phonetic mapping engine for Classical Latin → espeak-ng.

Transformations applied before passing text to pyttsx3/espeak-ng:
  1. Macron resolution: precomposed long-vowel characters → [[len 180]] annotations
  2. Hard consonant enforcement: C → /k/, G → /g/, V → /w/ semivowel
  3. Diphthong handling: ae → /aɪ/, oe → /ɔɪ/

espeak-ng does not natively interpret precomposed Latin macrons as duration
markers, so explicit prosody length annotations are required.
"""
from __future__ import annotations

import re

# Mapping of precomposed long-vowel characters to their espeak-ng equivalents.
# Each macron vowel is replaced with an espeak-ng prosody length annotation
# followed by the base vowel.
_MACRON_MAP: dict[str, str] = {
    "ā": "[[len 180]]a",
    "ē": "[[len 180]]e",
    "ī": "[[len 180]]i",
    "ō": "[[len 180]]o",
    "ū": "[[len 180]]u",
    "Ā": "[[len 180]]A",
    "Ē": "[[len 180]]E",
    "Ī": "[[len 180]]I",
    "Ō": "[[len 180]]O",
    "Ū": "[[len 180]]U",
}

# Diphthong replacements using espeak-ng IPA override syntax.
# Resolved AFTER macron decomposition so precomposed chars in diphthongs are
# handled first.
_DIPHTHONG_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"ae", re.IGNORECASE), "[[aɪ]]"),
    (re.compile(r"oe", re.IGNORECASE), "[[ɔɪ]]"),
]

# Hard consonant enforcement:
# C (not followed by h, as 'ch' is rare in Classical Latin) → /k/
# G → /g/  (already default in many espeak contexts, but make explicit)
# V → /w/ semivowel
_CONSONANT_MAP: list[tuple[re.Pattern, str]] = [
    # C at word boundary or before vowel/consonant (not already annotated) → [[k]]
    (re.compile(r"\bC\b", re.IGNORECASE), "[[k]]"),
    # V (capital) → [[w]] — semivowel
    (re.compile(r"\bV\b"), "[[w]]"),
    # Lowercase v at word start or between vowels
    (re.compile(r"(?<![A-Za-z])v(?=[aeiouāēīōū])", re.IGNORECASE), "[[w]]"),
    # Standalone c (Classical /k/ sound)
    (re.compile(r"(?<!\[)c(?!\[)", re.IGNORECASE), "[[k]]"),
]


def resolve_macrons(text: str) -> str:
    """Replace precomposed long-vowel characters with espeak-ng prosody annotations."""
    for char, annotation in _MACRON_MAP.items():
        text = text.replace(char, annotation)
    return text


def resolve_diphthongs(text: str) -> str:
    """Replace ae/oe with espeak-ng phoneme annotations."""
    for pattern, replacement in _DIPHTHONG_MAP:
        text = pattern.sub(replacement, text)
    return text


def enforce_hard_consonants(text: str) -> str:
    """
    Annotate C as /k/ and V as /w/ for Classical Latin pronunciation.
    Applied after macron and diphthong resolution.
    """
    # Replace 'c' that hasn't already been wrapped in [[ ]]
    # Simple pass: replace c/C not already inside [[...]]
    result = []
    i = 0
    while i < len(text):
        if text[i : i + 2] == "[[":
            # Already inside an annotation — find the closing ]]
            end = text.find("]]", i + 2)
            if end == -1:
                result.append(text[i:])
                break
            result.append(text[i : end + 2])
            i = end + 2
        elif text[i].lower() == "c":
            result.append("[[k]]")
            i += 1
        elif text[i] == "V":
            result.append("[[w]]")
            i += 1
        elif text[i] == "v":
            # Only semivowel-ise v between/before vowels
            result.append("[[w]]")
            i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def map_for_espeak(text: str) -> str:
    """
    Full phonetic mapping pipeline for espeak-ng.

    Steps:
      1. Resolve macrons (precomposed → [[len 180]] annotation)
      2. Resolve diphthongs (ae/oe → IPA annotation)
      3. Enforce hard consonants (C → [[k]], V → [[w]])

    Returns the annotated string ready for pyttsx3/espeak-ng.
    """
    text = resolve_macrons(text)
    text = resolve_diphthongs(text)
    text = enforce_hard_consonants(text)
    return text
