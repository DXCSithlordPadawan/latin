"""
check_checksums.py — Build-time SHA-256 artifact verification.

Reads corpus_manifest.lock, verifies every non-PENDING entry against its
declared checksum. Exits with code 1 if any mismatch is found.
Called by Containerfile at image build time.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

MANIFEST = Path(__file__).parent.parent / "corpus_manifest.lock"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not MANIFEST.exists():
        print(f"ERROR: {MANIFEST} not found.", file=sys.stderr)
        sys.exit(1)

    failures = []
    checked = 0
    pending = 0

    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "sha256=PENDING" in line:
            pending += 1
            continue

        # Parse: artifact=<path> sha256=<hex> license=<id>
        parts = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
        artifact_rel = parts.get("artifact")
        expected = parts.get("sha256")

        if not artifact_rel or not expected:
            continue

        artifact_path = Path(__file__).parent.parent / artifact_rel
        if not artifact_path.exists():
            failures.append(f"MISSING: {artifact_rel}")
            continue

        actual = sha256_file(artifact_path)
        if actual != expected:
            failures.append(
                f"MISMATCH: {artifact_rel}\n  expected: {expected}\n  actual:   {actual}"
            )
        else:
            checked += 1

    print(f"Verified {checked} artifact(s). Pending: {pending}. Failures: {len(failures)}.")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        sys.exit(1)

    if pending > 0:
        print(f"WARN: {pending} artifact(s) have PENDING checksums (pre-fine-tuning build).")

    sys.exit(0)


if __name__ == "__main__":
    main()
