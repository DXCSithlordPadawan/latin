"""
Prefix router — builds the multi-task prefix string for mT5 seq2seq inference.

Prefix conventions:
  EN→LA standard:  "translate en-la age-<N>: <text>"
  EN→LA barbarian: "translate en-la barbarian: <text>"
  LA→EN:           "translate la-en: <text>"
"""
from __future__ import annotations

# Maps level integers 1–6 to the age tag used in the prefix.
LEVEL_AGE_MAP: dict[int, int] = {
    1: 4,
    2: 6,
    3: 8,
    4: 12,
    5: 16,
    6: 18,
}

VALID_LEVELS = frozenset(range(1, 7))
VALID_DIRECTIONS = frozenset({"en-la", "la-en"})


def build_prefix(direction: str, level: int | None = None, barbarian: bool = False) -> str:
    """
    Return the task prefix string for a given direction and level.

    Args:
        direction: 'en-la' or 'la-en'
        level: integer 1–6 (required for en-la non-barbarian)
        barbarian: if True, use Barbarian Mode prefix (only valid for en-la)

    Returns:
        Prefix string, e.g. "translate en-la age-8:"

    Raises:
        ValueError on invalid direction, level, or incompatible combination.
    """
    direction = direction.lower().strip()
    if direction not in VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid direction '{direction}'. Must be one of: {sorted(VALID_DIRECTIONS)}"
        )

    if direction == "la-en":
        return "translate la-en:"

    # direction == "en-la"
    if barbarian:
        return "translate en-la barbarian:"

    if level is None:
        raise ValueError("Level must be specified for EN→LA non-barbarian translation.")

    if level not in VALID_LEVELS:
        raise ValueError(
            f"Invalid level {level!r}. Must be an integer 1–6."
        )

    age = LEVEL_AGE_MAP[level]
    return f"translate en-la age-{age}:"


def build_input(prefix: str, text: str) -> str:
    """Combine prefix and source text into the full model input string."""
    return f"{prefix} {text.strip()}"
