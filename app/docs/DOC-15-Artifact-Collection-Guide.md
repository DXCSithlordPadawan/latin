# DOC-15 External Artifact Collection, Packaging and Integration Guide

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Staging Engineer (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s4.2a, s7, `scripts/fetch_corpus.sh`, `corpus_manifest.lock` |
| **Status** | Procedure only. Nothing collected. **No download URL is recorded here** because none has been checked this session |

> Nothing here has been verified against a running system.

## 1. Pattern

Collect, verify, quarantine, stage, package, install, record. Collection happens on the staging machine only. Entry to the air-gapped host is by the OCI tarball only.

## 2. Items to collect

| Item | Used for | Licence | Verify how | Staged to |
|---|---|---|---|---|
| Whitaker's Words data (DICTLINE.GEN, STEMLIST.GEN) | Morphology and fallback | Public domain | SHA-256, source note | `data/whitakers_words/` (absent today) |
| Perseus Latin excerpts | Training corpus | CC BY-SA 3.0 | SHA-256 | `corpus/raw/` |
| Latin Vulgate parallel text | Training corpus | Public domain | SHA-256 | `corpus/raw/` |
| Leipzig LatinISE | Training corpus (monolingual) | CC BY | SHA-256 | `corpus/raw/` |
| mT5-small base weights | Fine-tune base | Apache 2.0 | SHA-256; upstream hash from a second channel | `models/mt5-small-base/` |
| FreeSerif and DejaVu Sans fonts | PDF macrons | GPL with font exception | SHA-256 | `static/fonts/` (absent today) |
| Python wheels (flask, fpdf2, pyttsx3, tomli, transformers, torch, sentencepiece, sacrebleu and their dependencies) | Runtime and staging | Various | `--require-hashes` | `wheels/` (absent today) |
| RHEL UBI 9 base image | Container base | Red Hat UBI EULA (CONFIRM) | Pin by digest | Local registry or tarball |
| espeak-ng RPMs and dependencies (EPEL 9; not in UBI) | TTS | GPL | RPM signature and SHA-256 | `rpms/` (see `rpms/README.txt`) |

CC BY-SA 3.0 and GPL terms may carry share-alike duties for the combined work: **legal review is CONFIRM** (JSP936-GOV-04 asks for legal advice at project start).

## 3. Per-item checklist

1. Record source, date, collector, version and licence.
2. Record SHA-256; compare with the publisher's value on a second channel where one exists.
3. Scan; keep the item out of the build tree until the scan record exists.
4. Review against the corpus filtering rules (PRD s4.2a) and record retained and excluded counts.
5. Add `artifact=<path> sha256=<hex> license=<id>` to `corpus_manifest.lock`.
6. Generate an SBOM for the wheelhouse and attach it to the release notes.

## 3b. Check what is missing

`python scripts/check_artifacts.py` lists eight build inputs and exits 1 if any is missing. On 2026-11-20 only `corpus/spot_check.tsv` passes. It downloads and creates nothing.

## 3a. Wheelhouse list

`requirements-runtime.txt` holds package names only. Generate exact versions and hashes on staging (`pip download`, `pip hash` or `pip-compile --generate-hashes`) before an image build; the Containerfile uses `--require-hashes` and fails otherwise.

## 4. Update procedure

New bundle and new image tag only; no in-place swap (PRD s7.1). Re-run the quality gate whenever corpus or base weights change.

## 5. Known gaps

Manifest entries are all commented PENDING; no SBOM tool chosen; licence review not done; `fetch_corpus.sh` not reviewed against the Bash guide (s3 to s6).

## Sources

[PRD](../../prd.md) s4.2a, s7; `corpus_manifest.lock`; [README](../../README.md) licence table; Bash guide s3 to s6 in `aip/standards`.
