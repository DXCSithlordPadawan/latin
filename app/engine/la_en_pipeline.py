"""
LA→EN dedicated pipeline.

Steps:
  1. Tokenise input Latin text
  2. Principal-parts lookup against Whitaker's Words data
  3. Case and mood disambiguation (heuristic)
  4. mT5 seq2seq decoding with 'translate la-en:' prefix
  5. UK English spelling normalisation
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from engine.morphological import WhitakersWordsMorphAnalyser, get_analyser
from engine.output_postprocessor import postprocess_la_en

if TYPE_CHECKING:
    from engine.translation_engine import TranslationEngine

# Basic Latin tokeniser — splits on whitespace and strips punctuation
_PUNCT_RE = re.compile(r"[,;:.!?()\[\]\"']")


def tokenise_latin(text: str) -> list[str]:
    """Return a list of Latin word tokens (punctuation stripped)."""
    text = _PUNCT_RE.sub(" ", text)
    return [t for t in text.split() if t]


def _case_tag(analysis: str) -> str | None:
    """Extract case tag from a Whitaker's Words analysis line."""
    case_markers = ("NOM", "GEN", "DAT", "ACC", "ABL", "VOC", "LOC")
    upper = analysis.upper()
    for case in case_markers:
        if case in upper:
            return case
    return None


def _mood_tag(analysis: str) -> str | None:
    """Extract mood from a Whitaker's Words analysis line."""
    moods = ("IND", "SUB", "IMP", "INF", "PPL")
    upper = analysis.upper()
    for mood in moods:
        if mood in upper:
            return mood
    return None


def annotate_morphology(tokens: list[str], analyser: WhitakersWordsMorphAnalyser) -> list[dict]:
    """
    Return a list of morphological annotations for each token.
    Each annotation is a dict with keys: token, analyses, case, mood.
    """
    annotations = []
    for token in tokens:
        analyses = analyser.principal_parts_lookup(token)
        case = None
        mood = None
        if analyses:
            # Use first analysis for case/mood hints
            case = _case_tag(analyses[0])
            mood = _mood_tag(analyses[0])
        annotations.append(
            {"token": token, "analyses": analyses, "case": case, "mood": mood}
        )
    return annotations


def run_la_en_pipeline(
    latin_text: str,
    engine: "TranslationEngine",
) -> str:
    """
    Full LA→EN pipeline.

    1. Tokenise
    2. Whitaker's lookup + case/mood annotation
    3. mT5 decode with 'translate la-en:' prefix
    4. UK English normalisation
    """
    analyser = get_analyser()
    tokens = tokenise_latin(latin_text)
    annotations = annotate_morphology(tokens, analyser)

    # Use mT5 for the actual translation
    raw_output = engine.decode_with_prefix("translate la-en:", latin_text)

    # Post-process: UK English normalisation + punctuation
    return postprocess_la_en(raw_output)
