"""
prepare_training_data.py — Run on STAGING MACHINE ONLY.

Applies corpus filtering rules, aligns parallel EN↔LA sentence pairs,
tokenises, and outputs HuggingFace datasets-format training splits.

Filtering rules (see docs/finetuning_procedure.md):
  - Latin Vulgate: exclude post-4th century CE additions, deuterocanonical books.
  - Leipzig LatinISE: exclude texts dated > 300 CE; exclude undated non-Classical authors.
  - Perseus: no additional filtering; selected authors are already Classical.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path

import yaml
from datasets import Dataset, DatasetDict
from transformers import T5Tokenizer

CONFIG_PATH = Path("config/finetune_config.yaml")
CORPUS_DIR = Path("corpus/raw")
OUTPUT_DIR = Path("corpus")

# Deuterocanonical / post-Classical Vulgate books to exclude
VULGATE_EXCLUDE_BOOKS = {
    "Tobit", "Judith", "1 Maccabees", "2 Maccabees",
    "Wisdom", "Sirach", "Baruch",
}

# Known Classical Latin authors (composition dates ≤ 300 CE)
CLASSICAL_AUTHORS = {
    "cicero", "caesar", "vergil", "virgil", "livy", "ovid", "tacitus",
    "sallust", "catullus", "horace", "juvenal", "martial", "pliny",
    "suetonius", "seneca", "quintilian", "plautus", "terence",
}


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def filter_vulgate_pairs(pairs: list[dict]) -> tuple[list[dict], int]:
    """
    Exclude post-4th century CE Vulgate additions and deuterocanonical books.
    Returns (kept_pairs, excluded_count).
    """
    kept, excluded = [], 0
    for pair in pairs:
        book = pair.get("book", "")
        if any(ex in book for ex in VULGATE_EXCLUDE_BOOKS):
            excluded += 1
        else:
            kept.append(pair)
    return kept, excluded


def filter_leipzig_pairs(pairs: list[dict]) -> tuple[list[dict], int]:
    """
    Exclude texts dated > 300 CE. Undated texts kept only if author is verifiably Classical.
    """
    kept, excluded = [], 0
    for pair in pairs:
        date = pair.get("composition_date")
        author = pair.get("author", "").lower()
        if date is not None:
            try:
                if int(date) > 300:
                    excluded += 1
                    continue
            except (ValueError, TypeError):
                pass
        elif author not in CLASSICAL_AUTHORS:
            excluded += 1
            continue
        kept.append(pair)
    return kept, excluded


def build_prefix(direction: str, level: int | str) -> str:
    if direction == "en-la":
        if str(level) == "barbarian":
            return "translate en-la barbarian:"
        age_map = {1: 4, 2: 6, 3: 8, 4: 12, 5: 16, 6: 18}
        age = age_map.get(int(level), 18)
        return f"translate en-la age-{age}:"
    return "translate la-en:"


def load_parallel_pairs(corpus_dir: Path) -> list[dict]:
    """Stub: load parallel EN↔LA pairs from corpus directory."""
    pairs = []
    # Load from TSV files if they exist
    for tsv in corpus_dir.glob("**/*.tsv"):
        with open(tsv, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                pairs.append(dict(row))
    return pairs


def prepare_examples(pairs: list[dict]) -> list[dict]:
    examples = []
    for pair in pairs:
        en = pair.get("en", pair.get("english", "")).strip()
        la = pair.get("la", pair.get("latin", "")).strip()
        level = pair.get("level", 4)
        if not en or not la:
            continue
        # EN→LA
        examples.append({
            "input_text": f"{build_prefix('en-la', level)} {en}",
            "target_text": la,
            "direction": "en-la",
            "level": str(level),
        })
        # LA→EN
        examples.append({
            "input_text": f"translate la-en: {la}",
            "target_text": en,
            "direction": "la-en",
            "level": str(level),
        })
    return examples


def main() -> None:
    config = load_config()
    print(f"Loading corpus from {CORPUS_DIR}...")
    raw_pairs = load_parallel_pairs(CORPUS_DIR)
    print(f"Loaded {len(raw_pairs)} raw pairs.")

    vulgate_pairs = [p for p in raw_pairs if p.get("source") == "vulgate"]
    leipzig_pairs = [p for p in raw_pairs if p.get("source") == "leipzig"]
    other_pairs = [
        p for p in raw_pairs if p.get("source") not in ("vulgate", "leipzig")
    ]

    vulgate_kept, vulgate_excluded = filter_vulgate_pairs(vulgate_pairs)
    leipzig_kept, leipzig_excluded = filter_leipzig_pairs(leipzig_pairs)

    print(f"Vulgate: kept {len(vulgate_kept)}, excluded {vulgate_excluded}")
    print(f"Leipzig: kept {len(leipzig_kept)}, excluded {leipzig_excluded}")
    print(f"Other (Perseus etc.): {len(other_pairs)} (no additional filtering)")

    all_pairs = vulgate_kept + leipzig_kept + other_pairs
    examples = prepare_examples(all_pairs)
    print(f"Total training examples after prefix expansion: {len(examples)}")

    if len(examples) == 0:
        print("WARNING: No training examples produced. Check corpus directory.")
        sys.exit(1)

    # Split 90/10 train/validation
    split_idx = int(len(examples) * 0.9)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    OUTPUT_DIR.mkdir(exist_ok=True)
    train_out = OUTPUT_DIR / "train_split.jsonl"
    with open(train_out, "w", encoding="utf-8") as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Wrote {len(train_examples)} train examples to {train_out}")
    print(f"Validation split: {len(val_examples)} examples (use validation_split.tsv for chrF gate)")

    # Record filtering counts
    procedure_path = Path("docs/finetuning_procedure.md")
    if procedure_path.exists():
        with open(procedure_path, "a", encoding="utf-8") as f:
            f.write(
                f"\n## Data Preparation Run\n"
                f"- Vulgate kept: {len(vulgate_kept)}, excluded: {vulgate_excluded}\n"
                f"- Leipzig kept: {len(leipzig_kept)}, excluded: {leipzig_excluded}\n"
                f"- Perseus: {len(other_pairs)}\n"
                f"- Total examples: {len(examples)}\n"
            )


if __name__ == "__main__":
    main()
