"""
eval_chrf.py — chrF metric evaluation against validation_split.tsv.

Gate: chrF ≥45.0 in BOTH EN→LA and LA→EN directions.
Outputs breakdown by direction and level.
Exits with code 0 on pass; code 1 on failure.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

from sacrebleu.metrics import CHRF
from transformers import MT5ForConditionalGeneration, T5Tokenizer

VALIDATION_FILE = Path("corpus/validation_split.tsv")
CHECKPOINT_DIR = Path("models/mt5-latin")
CHRF_THRESHOLD = 45.0


def translate(model, tokenizer, text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    outputs = model.generate(**inputs, max_length=128, num_beams=4, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def main() -> None:
    if not VALIDATION_FILE.exists():
        print(f"ERROR: {VALIDATION_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading checkpoint from {CHECKPOINT_DIR}...")
    tokenizer = T5Tokenizer.from_pretrained(str(CHECKPOINT_DIR))
    model = MT5ForConditionalGeneration.from_pretrained(str(CHECKPOINT_DIR))
    model.eval()

    chrf = CHRF()
    en_la_hyps, en_la_refs = [], []
    la_en_hyps, la_en_refs = [], []
    by_level: dict[str, dict[str, list]] = defaultdict(
        lambda: {"hyps": [], "refs": []}
    )

    with open(VALIDATION_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            direction = row.get("direction", "en-la").strip()
            input_text = row.get("input_text", "").strip()
            ref = row.get("target_text", row.get("reference", "")).strip()
            level = row.get("level", "?").strip()
            if not input_text or not ref:
                continue
            hyp = translate(model, tokenizer, input_text)
            if direction == "en-la":
                en_la_hyps.append(hyp)
                en_la_refs.append([ref])
                by_level[f"en-la-{level}"]["hyps"].append(hyp)
                by_level[f"en-la-{level}"]["refs"].append([ref])
            else:
                la_en_hyps.append(hyp)
                la_en_refs.append([ref])
                by_level[f"la-en-{level}"]["hyps"].append(hyp)
                by_level[f"la-en-{level}"]["refs"].append([ref])

    if not en_la_hyps or not la_en_hyps:
        print("ERROR: Insufficient validation examples.", file=sys.stderr)
        sys.exit(1)

    en_la_score = chrf.corpus_score(en_la_hyps, en_la_refs).score
    la_en_score = chrf.corpus_score(la_en_hyps, la_en_refs).score

    print(f"\nchrF Scores:")
    print(f"  EN→LA: {en_la_score:.2f}")
    print(f"  LA→EN: {la_en_score:.2f}")
    print(f"\nBreakdown by direction/level:")
    for key, data in sorted(by_level.items()):
        if data["hyps"]:
            score = chrf.corpus_score(data["hyps"], data["refs"]).score
            print(f"  {key}: {score:.2f}  (n={len(data['hyps'])})")

    passed = en_la_score >= CHRF_THRESHOLD and la_en_score >= CHRF_THRESHOLD

    print(f"\nThreshold: {CHRF_THRESHOLD}")
    if passed:
        print("GATE PASSED: Both directions ≥ threshold")
        sys.exit(0)
    else:
        failing = []
        if en_la_score < CHRF_THRESHOLD:
            failing.append(f"EN→LA {en_la_score:.2f}")
        if la_en_score < CHRF_THRESHOLD:
            failing.append(f"LA→EN {la_en_score:.2f}")
        print(f"GATE FAILED: {', '.join(failing)} below threshold", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
