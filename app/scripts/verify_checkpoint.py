"""
verify_checkpoint.py — Spot-check quality gate.

Evaluates the fine-tuned checkpoint against corpus/spot_check.tsv.
Gate: ≥40/50 pairs must pass (80%) in BOTH translation directions.
Exits with code 0 on pass; code 1 on failure.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from transformers import MT5ForConditionalGeneration, T5Tokenizer

SPOT_CHECK_FILE = Path("corpus/spot_check.tsv")
CHECKPOINT_DIR = Path("models/mt5-latin")
PASS_THRESHOLD = 40  # out of 50


def translate(model, tokenizer, prefix: str, text: str, max_len: int = 128) -> str:
    input_text = f"{prefix} {text}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=128)
    outputs = model.generate(**inputs, max_length=max_len, num_beams=4, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def main() -> None:
    if not SPOT_CHECK_FILE.exists():
        print(f"ERROR: {SPOT_CHECK_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading checkpoint from {CHECKPOINT_DIR}...")
    tokenizer = T5Tokenizer.from_pretrained(str(CHECKPOINT_DIR))
    model = MT5ForConditionalGeneration.from_pretrained(str(CHECKPOINT_DIR))
    model.eval()

    pairs = []
    with open(SPOT_CHECK_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pairs.append(row)

    en_la_pass = 0
    la_en_pass = 0
    total = len(pairs)

    for pair in pairs:
        en = pair.get("en", "").strip()
        la_ref = pair.get("la", "").strip()
        la_pred = translate(model, tokenizer, "translate en-la age-18:", en)
        if la_pred.lower() == la_ref.lower():
            en_la_pass += 1

        la = pair.get("la", "").strip()
        en_ref = pair.get("en", "").strip()
        en_pred = translate(model, tokenizer, "translate la-en:", la)
        if en_pred.lower() == en_ref.lower():
            la_en_pass += 1

    print(f"EN→LA: {en_la_pass}/{total} ({100*en_la_pass/total:.1f}%)")
    print(f"LA→EN: {la_en_pass}/{total} ({100*la_en_pass/total:.1f}%)")

    passed = en_la_pass >= PASS_THRESHOLD and la_en_pass >= PASS_THRESHOLD

    if passed:
        print(f"GATE PASSED: Both directions ≥{PASS_THRESHOLD}/{total}")
        sys.exit(0)
    else:
        print(
            f"GATE FAILED: One or both directions below threshold {PASS_THRESHOLD}/{total}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
