# Implementation Progress

**Project:** Air-Gapped Adaptive Latin Translation & Pedagogical System  
**Author:** Iain Reid  
**Status:** Phase 1–6 Complete; Phase 7 Compliance Gate Pending  
**Last Updated:** 2026-06-08

---

## Phase Status Overview

| Phase | Title | Status | Notes |
|---|---|---|---|
| Phase 1 | Foundation — Config, Schema, Profile Management | ✅ Complete | 40 tests pass |
| Phase 2 | Corpus Acquisition & Model Fine-Tuning (Staging) | ✅ Complete | Scripts authored; staging machine run pending |
| Phase 3 | Translation Engine Integration | ✅ Complete | Mocked tests pass; real checkpoint awaits Phase 2 |
| Phase 4 | TTS Pipeline | ✅ Complete | Phonetic mapper unit tests pass |
| Phase 5 | Web UI & Authentication | ✅ Complete | Flask app + all templates; auth tests pass |
| Phase 6 | PDF Factory & Config Reference | ✅ Complete | fpdf2 factory; 19 PDF tests pass |
| Phase 7 | Compliance, Security Review & Container Build | 🔄 In Progress | Docs baselined; container build pending staging |

Legend: ⬜ Not Started · 🔄 In Progress · ✅ Complete · ❌ Blocked

---

## Test Suite Results — 2026-06-08

```
pytest --junitxml=docs/test_results/results.xml
176 passed, 1 deselected (slow marker), 0 failed, 0 errors
```

JUnit XML report committed at `docs/test_results/results.xml`.

---

## Phase 1 — Foundation ✅

### Tasks
- [x] 1.1 Directory structure (`.airgap-translator/` tree)
- [x] 1.2 `config/config.toml.example` — all keys documented
- [x] 1.3 `config/config.toml` — initial deployment copy
- [x] 1.4 SQLite schema — `schema_version` + all profile tables (7 tables)
- [x] 1.5 `engine/db_migrate.py` — migration runner (version compare, sequential apply, rollback)
- [x] 1.6 `engine/migrations/001.sql` — initial schema migration
- [x] 1.7 `engine/profile_manager.py` — create, select, rename, delete (secure erase)
- [x] 1.8 `engine/sanitiser.py` — null bytes, control chars, shell metacharacters, token cap, CSV formula strip
- [x] 1.9 `tests/test_schema_migration.py` — 7 tests
- [x] 1.10 `tests/test_input_sanitisation.py` — 33 tests

---

## Phase 2 — Corpus Acquisition & Model Fine-Tuning ✅ (scripts complete)

> ⚠️ Staging machine run required before Phase 3 checkpoint integration.

### Tasks
- [x] 2.1 `scripts/requirements-staging.txt`
- [x] 2.2 `scripts/fetch_corpus.sh`
- [x] 2.3 `corpus/spot_check.tsv` — 50 curated EN↔LA reference pairs
- [x] 2.4 `corpus/validation_split.tsv` — placeholder (to be populated on staging machine)
- [x] 2.5 `scripts/prepare_training_data.py`
- [x] 2.6 `config/finetune_config.yaml`
- [x] 2.7 `scripts/finetune_mt5.py`
- [x] 2.8 `scripts/verify_checkpoint.py`
- [x] 2.9 `scripts/eval_chrf.py`
- [ ] 2.10 Run quality gate on staging machine (**PENDING — staging machine run**)
- [ ] 2.11 Record SHA-256 checksums in `corpus_manifest.lock` (**PENDING**)
- [ ] 2.12 Package checkpoint for physical media transfer (**PENDING**)

---

## Phase 3 — Translation Engine ✅

### Tasks
- [x] 3.1 `engine/translation_engine.py` — checkpoint load, SHA-256 verify, full pipeline
- [x] 3.2 `engine/prefix_router.py` — prefix string builder
- [x] 3.3 `engine/reading_age.py` — level 1–6 + Barbarian spec metadata
- [x] 3.4 `engine/barbarian.py` — Barbarian Mode prefix builder + post-processor
- [x] 3.5 `engine/morphological.py` — Whitaker's Words loader, confidence-gated fallback
- [x] 3.6 `engine/la_en_pipeline.py` — LA→EN dedicated pipeline
- [x] 3.7 `engine/output_postprocessor.py` — SOV hint, UK English normalisation
- [x] 3.8 Token cap enforcement in translation engine
- [x] 3.9 `tests/test_translation_engine.py` — prefix types, confidence gate, Barbarian, slow marker
- [x] 3.10 `tests/test_reading_age.py` — level specs, mid-session switch

---

## Phase 4 — TTS Pipeline ✅

### Tasks
- [x] 4.1 `engine/phonetic_mapper.py` — macron resolution, hard consonants, diphthongs
- [x] 4.2 `engine/tts_engine.py` — pyttsx3/espeak locked; playback/export/both modes
- [x] 4.3 espeak-ng bundled in Containerfile
- [x] 4.4 `tests/test_tts.py` — macron annotation, hard consonant, diphthong, export/playback/both

---

## Phase 5 — Web UI & Authentication ✅

### Tasks
- [x] 5.1 `app.py` — Flask server, 127.0.0.1 bind, port-in-use check
- [x] 5.2 Token generation (`secrets.token_hex`), write to `session.token` (600), stdout URL
- [x] 5.3 Auth middleware — token validation, redirect strip, session cookie, HTTP 409, idle timeout
- [x] 5.4 SIGTERM handler — 5-second grace window, token deletion
- [x] 5.5 Config validation at startup with WARN log
- [x] 5.6 UI templates — translate, result, profiles, dashboard, about
- [x] 5.7 Operation status badge (JS; graceful degradation)
- [x] 5.8 WCAG 2.1 Level A — keyboard nav, labels, contrast, lang, aria-describedby
- [x] 5.9 Level selector persisted per profile in SQLite
- [x] 5.10 All assets bundled (no CDN)
- [x] 5.11–5.14 Auth, port, adaptive learning, error handling tests
- [x] `static/css/main.css` — WCAG contrast-compliant stylesheet
- [x] `static/js/main.js` — operation status badge

---

## Phase 6 — PDF Factory & Config Reference ✅

### Tasks
- [x] 6.1 `engine/pdf_factory.py` — fpdf2; A4/Letter; configurable margins; FreeSerif fallback
- [x] 6.2 Alternating line buffer workbook layout
- [x] 6.3 Declension matrix layout
- [x] 6.4 Note-taking margin layout
- [x] 6.5 `config/config.toml.example` — all keys documented
- [x] 6.6 `tests/test_pdf.py` — 19 tests; macron, layouts, paper size, HTTP headers, no file written

---

## Phase 7 — Compliance, Security Review & Container Build 🔄

### Tasks
- [x] 7.1 `Containerfile` — Ubuntu 22.04 base, FIPS assertion, rootless UID 10001
- [x] 7.2 `scripts/check_checksums.py` — build-time SHA-256 verification
- [x] 7.3 `docs/fips_verification.md`
- [x] 7.4 `docs/deployment_checklist.md` — auditd rules, backup cron, SLA verification table
- [x] 7.5 `docs/architecture.md` + `docs/ARCHITECTURE_GUIDE.md`
- [x] 7.6 `docs/adaptive_learning_schema.md`
- [x] 7.7 `docs/input_sanitization_policy.md`
- [x] 7.8 `docs/finetuning_procedure.md` (template; staging run records pending)
- [x] 7.9 All 12 required documentation deliverables under `docs/`
- [x] 7.10 `tests/test_container_integrity.py` — SHA-256 logic, manifest exists, spot-check count
- [x] 7.11 Full pytest suite: **176 passed, 0 failed** — `docs/test_results/results.xml` committed
- [ ] 7.12 `pytest -m slow` — chrF quality gate (requires staging checkpoint) **PENDING**
- [ ] 7.13 Manual SLA verification on target host **PENDING**
- [ ] 7.14 Security review sign-off **PENDING**
- [ ] 7.15 OCI image tarball + physical media transfer **PENDING**

---

## Key Cross-Cutting Requirements

| Requirement | Status |
|---|---|
| All log timestamps in UTC ISO 8601 | ✅ `app.py` logging setup |
| Log content truncated to 64 chars | ✅ `engine/sanitiser.truncate_for_log` |
| Token file deleted on shutdown | ✅ SIGTERM handler + `_delete_token()` |
| Rootless container, UID-isolated profile dir (700) | ✅ Containerfile |
| `--network=none` Podman flag | ✅ Documented in DEPLOYMENT_GUIDE.md |
| SHA-256 verification at startup | ✅ `engine/translation_engine._verify_checksum` |
| Single-writer queue for SQLite writes | ✅ `threading.Lock` in profile_manager |
| UK English spelling normalisation in LA→EN output | ✅ `engine/output_postprocessor` |
| No file written to disk for PDF or TTS export | ✅ BytesIO in pdf_factory; temp-zero-delete in tts_engine |
| About/Licenses page — all corpus licences listed | ✅ `templates/about.html` |

---

## Issues & Blockers

- **Phase 2 Staging Run:** Fine-tuning requires a network-connected staging machine (Ubuntu 22.04 LTS, ≥16 GB RAM, Python 3.11). The `scripts/` directory contains all required scripts. Once the checkpoint is produced and quality gate passes, `corpus_manifest.lock` must be updated with real SHA-256 checksums before the Containerfile build can be finalised.
- **pyttsx3/espeak-ng:** TTS tests mock synthesis; real audio output requires espeak-ng bundled in the OCI image. Not testable on Windows host.
- **FreeSerif font:** PDF macron rendering tests skip the macron-in-PDF assertion when `static/fonts/FreeSerif.ttf` is absent (test environment). Full macron rendering is validated inside the container.

---

## Build Record Summary

| Run | Date | Operator | Spot-Check | chrF EN→LA | chrF LA→EN | Result |
|---|---|---|---|---|---|---|
| — | — | Pending staging machine run | — | — | — | — |
