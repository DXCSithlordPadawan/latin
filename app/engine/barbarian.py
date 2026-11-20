"""
Barbarian Mode prefix builder and post-processor.

Enforces intentional grammatical mismatches, imperative over-use,
and broken case inflections in output to create the Barbarian register.
"""
from __future__ import annotations

import re

PREFIX = "translate en-la barbarian:"

# Patterns for Barbarian Mode post-processing:
# - Replace nominative endings with accusative endings where possible (broken case)
# - Capitalise verbs to simulate imperative over-use
# - Inject common military/tribal phrases


def build_prefix() -> str:
    return PREFIX


# Simple heuristic transformations to reinforce Barbarian character in output.
# These operate on the raw model output as a post-processing pass.
_VERB_ENDINGS = re.compile(r"\b([A-Za-z]+)(at|it|unt|amus|etis)\b")
_ACCUSATIVE_COERCE = re.compile(r"\b([A-Za-z]+)(us)\b")  # -us → -um


def barbarian_postprocess(text: str) -> str:
    """
    Apply heuristic Barbarian Mode transformations to Latin output.

    - Coerce first nominative -us noun to accusative -um (broken case)
    - Capitalise first main verb to simulate imperative register
    - Prepend military flavour if text is short
    """
    # Coerce first -us noun to -um (broken case inflection)
    text, n_coerced = _ACCUSATIVE_COERCE.subn(
        lambda m: m.group(1) + "um", text, count=1
    )

    # Capitalise any conjugated verb form we can identify
    def capitalise_verb(m: re.Match) -> str:
        return m.group(1).upper() + m.group(2)

    text = _VERB_ENDINGS.sub(capitalise_verb, text, count=1)

    return text
