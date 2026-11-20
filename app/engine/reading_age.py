"""
Reading age adaptation — maps level 1–6 to display metadata and vocabulary constraint info.
"""
from __future__ import annotations

from dataclasses import dataclass

BARBARIAN_LEVEL = 7  # Sentinel value for Barbarian Mode


@dataclass(frozen=True)
class LevelSpec:
    level: int
    display_name: str
    age_range: str
    syntax_description: str
    vocabulary_description: str
    prefix_age_tag: int


LEVEL_SPECS: dict[int, LevelSpec] = {
    1: LevelSpec(
        level=1,
        display_name="Beginner",
        age_range="Ages 2–4",
        syntax_description="Simple Subject-Verb-Object (SVO). Single clauses only. No nesting.",
        vocabulary_description="Restricted to foundational concrete elements (fauna, flora, family units).",
        prefix_age_tag=4,
    ),
    2: LevelSpec(
        level=2,
        display_name="Elementary",
        age_range="Ages 5–6",
        syntax_description="Compound sentences joined via coordinating conjunctions (et, sed).",
        vocabulary_description="High-frequency active verbs and basic descriptive adjectives.",
        prefix_age_tag=6,
    ),
    3: LevelSpec(
        level=3,
        display_name="Primary",
        age_range="Ages 7–8",
        syntax_description="Simple subordinate structures (e.g. causal clauses with quod).",
        vocabulary_description="Basic noun declensions (1st & 2nd), simple present tense.",
        prefix_age_tag=8,
    ),
    4: LevelSpec(
        level=4,
        display_name="Intermediate",
        age_range="Ages 8–12",
        syntax_description="Multi-clause; perfect, imperfect, and future active indicatives.",
        vocabulary_description="Expanded general lexicon; standard abstract noun types.",
        prefix_age_tag=12,
    ),
    5: LevelSpec(
        level=5,
        display_name="Secondary",
        age_range="Ages 12–16",
        syntax_description="Complex rhetorical nesting; passive periphrastic; simple indirect statements.",
        vocabulary_description="Comprehensive academic classical vocabulary.",
        prefix_age_tag=16,
    ),
    6: LevelSpec(
        level=6,
        display_name="Advanced",
        age_range="Ages 16–18 / Adult",
        syntax_description="Unrestricted classical idioms; Golden Age prose (Cicero/Caesar).",
        vocabulary_description="Full unmitigated classical lexicon including poetic, technical, philosophy terms.",
        prefix_age_tag=18,
    ),
}

BARBARIAN_SPEC = LevelSpec(
    level=BARBARIAN_LEVEL,
    display_name="Barbarian Mode",
    age_range="Any",
    syntax_description="Fragmented, non-standard syntax. Over-reliance on direct command imperatives.",
    vocabulary_description="Intentional grammatical mismatches, military phrases, broken case inflections.",
    prefix_age_tag=0,
)


def get_level_spec(level: int) -> LevelSpec:
    if level == BARBARIAN_LEVEL:
        return BARBARIAN_SPEC
    if level not in LEVEL_SPECS:
        raise ValueError(f"Unknown level {level}. Valid values: 1–6 or {BARBARIAN_LEVEL} (Barbarian).")
    return LEVEL_SPECS[level]


def get_display_name(level: int) -> str:
    spec = get_level_spec(level)
    if level == BARBARIAN_LEVEL:
        return "Barbarian Mode"
    return f"Level {level} — {spec.display_name}"


def all_levels() -> list[LevelSpec]:
    """Return all specs in display order: 1–6 then Barbarian."""
    return [LEVEL_SPECS[i] for i in range(1, 7)] + [BARBARIAN_SPEC]
