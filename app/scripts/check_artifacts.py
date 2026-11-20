"""
List which build inputs are present (G-12). Run on the staging machine before a build.
Exit 1 if anything required is missing. Does not download or create anything.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _lines(p: Path) -> int:
    return sum(1 for _ in p.open(encoding="utf-8", errors="replace")) if p.is_file() else 0


def checks(root: Path = ROOT) -> list[tuple[str, bool, str]]:
    mdl = root / "models" / "mt5-latin"
    weights = [f for f in ("pytorch_model.bin", "model.safetensors") if (mdl / f).is_file()]
    return [
        ("checkpoint models/mt5-latin (config + weights)", (mdl / "config.json").is_file() and bool(weights), "run the staging build (DOC-12)"),
        ("Whitaker data/whitakers_words/DICTLINE.GEN", (root / "data" / "whitakers_words" / "DICTLINE.GEN").is_file(), "DOC-15 item 1"),
        ("font static/fonts/FreeSerif.ttf", (root / "static" / "fonts" / "FreeSerif.ttf").is_file(), "DOC-15"),
        ("wheelhouse wheels/*.whl", bool(list((root / "wheels").glob("*.whl"))) if (root / "wheels").is_dir() else False, "DOC-15 s3a"),
        ("rpms/*.rpm (espeak-ng and dependencies)", bool(list((root / "rpms").glob("*.rpm"))) if (root / "rpms").is_dir() else False, "rpms/README.txt"),
        ("corpus/spot_check.tsv has 50 pairs", _lines(root / "corpus" / "spot_check.tsv") >= 50, "PRD 4.2a"),
        ("corpus/validation_split.tsv has >= 500 pairs", _lines(root / "corpus" / "validation_split.tsv") >= 500, "PRD 4.2a"),
        ("requirements-runtime.txt has hashed requirement lines", any("--hash=sha256:" in l for l in (root / "requirements-runtime.txt").read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#")) if (root / "requirements-runtime.txt").is_file() else False, "DOC-15 s3a"),
    ]


def main() -> int:
    bad = 0
    for name, ok, hint in checks():
        print(("OK      " if ok else "MISSING ") + name + ("" if ok else f"   ({hint})"))
        bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
