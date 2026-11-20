"""
Output post-processor.

- SOV word order enforcement for Latin output (heuristic; model should already
  produce SOV but this acts as a guardrail for lower levels)
- UK English spelling normalisation for LA→EN output
"""
from __future__ import annotations

import re

# US → UK spelling normalisation map (common high-frequency substitutions)
_US_TO_UK: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\banalyze\b", re.I), "analyse"),
    (re.compile(r"\bcenter\b", re.I), "centre"),
    (re.compile(r"\bcolor\b", re.I), "colour"),
    (re.compile(r"\bfavor\b", re.I), "favour"),
    (re.compile(r"\bhonor\b", re.I), "honour"),
    (re.compile(r"\blabor\b", re.I), "labour"),
    (re.compile(r"\bneighbor\b", re.I), "neighbour"),
    (re.compile(r"\borganize\b", re.I), "organise"),
    (re.compile(r"\brecognize\b", re.I), "recognise"),
    (re.compile(r"\brealize\b", re.I), "realise"),
    (re.compile(r"\bspecialize\b", re.I), "specialise"),
    (re.compile(r"\btraveler\b", re.I), "traveller"),
    (re.compile(r"\bcatalog\b", re.I), "catalogue"),
    (re.compile(r"\bdialog\b", re.I), "dialogue"),
    (re.compile(r"\bplow\b", re.I), "plough"),
    (re.compile(r"\bgray\b", re.I), "grey"),
    (re.compile(r"\btire\b", re.I), "tyre"),
    (re.compile(r"\bcheck\b", re.I), "cheque"),
]


def normalise_uk_english(text: str) -> str:
    """Apply US → UK spelling normalisation to a translation output string."""
    for pattern, replacement in _US_TO_UK:
        text = pattern.sub(
            lambda m, r=replacement: _match_case(m.group(0), r), text
        )
    return text


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def enforce_sov_hint(latin_text: str) -> str:
    """
    Very light heuristic: if the text appears to already end with a verb
    (common Latin SOV pattern) return unchanged. If it ends with what looks
    like a noun/adjective nominative and the text is a single clause, apply
    no reordering (model output is trusted; SOV is enforced primarily through
    prefix conditioning during training). This function is a no-op placeholder
    for a future rule-based SOV reorderer.
    """
    return latin_text


def postprocess_la_en(text: str) -> str:
    """Full post-processing pipeline for LA→EN output."""
    text = text.strip()
    text = normalise_uk_english(text)
    # Ensure sentence ends with punctuation
    if text and text[-1] not in ".!?":
        text += "."
    return text


def postprocess_en_la(text: str) -> str:
    """Post-processing for EN→LA output."""
    text = text.strip()
    text = enforce_sov_hint(text)
    return text
