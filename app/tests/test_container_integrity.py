"""
Tests for OCI container integrity (PRD §9.13).

Covers:
  - SHA-256 mismatch on an artifact fails the build check
  - SHA-256 match passes the build check
  - Corpus manifest lock file exists and is non-empty
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST_PATH = Path(__file__).parent.parent / "corpus_manifest.lock"


# ─────────────────────────────────────────────────────────────────────────────
# SHA-256 verification helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_artifact(artifact_path: Path, expected_sha256: str) -> bool:
    if not artifact_path.exists():
        return False
    actual = _sha256_file(artifact_path)
    return actual == expected_sha256


# ─────────────────────────────────────────────────────────────────────────────
# Manifest exists
# ─────────────────────────────────────────────────────────────────────────────

def test_corpus_manifest_lock_exists():
    assert MANIFEST_PATH.exists(), f"corpus_manifest.lock not found at {MANIFEST_PATH}"


def test_corpus_manifest_lock_is_non_empty():
    content = MANIFEST_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 0


# ─────────────────────────────────────────────────────────────────────────────
# SHA-256 verification logic
# ─────────────────────────────────────────────────────────────────────────────

def test_sha256_mismatch_detected(tmp_path):
    """A file whose checksum does not match the expected value must fail verification."""
    artifact = tmp_path / "test_artifact.bin"
    artifact.write_bytes(b"correct content")
    correct_hash = _sha256_file(artifact)

    # Corrupt the file
    artifact.write_bytes(b"tampered content")

    result = _verify_artifact(artifact, correct_hash)
    assert result is False


def test_sha256_match_passes(tmp_path):
    """A file whose checksum matches the expected value must pass verification."""
    artifact = tmp_path / "test_artifact.bin"
    artifact.write_bytes(b"correct content")
    correct_hash = _sha256_file(artifact)

    result = _verify_artifact(artifact, correct_hash)
    assert result is True


def test_missing_artifact_fails_verification(tmp_path):
    """A file that does not exist must fail verification."""
    missing = tmp_path / "nonexistent.bin"
    result = _verify_artifact(missing, "a" * 64)
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Spot-check corpus file exists
# ─────────────────────────────────────────────────────────────────────────────

def test_spot_check_tsv_exists():
    spot_check = Path(__file__).parent.parent / "corpus" / "spot_check.tsv"
    assert spot_check.exists(), "corpus/spot_check.tsv not found"


def test_spot_check_has_50_pairs():
    spot_check = Path(__file__).parent.parent / "corpus" / "spot_check.tsv"
    lines = [l for l in spot_check.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Subtract 1 for header row
    data_rows = len(lines) - 1
    assert data_rows == 50, f"Expected 50 spot-check pairs, found {data_rows}"
