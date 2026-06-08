# Implementation Progress

**Project:** Air-Gapped Adaptive Latin Translation & Pedagogical System  
**Author:** Iain Reid  
**Status:** Planning  
**Last Updated:** 2026-06-08

---

## Phase Status Overview

| Phase | Title | Status | Notes |
|---|---|---|---|
| Phase 1 | Foundation — Config, Schema, Profile Management | ⬜ Not Started | |
| Phase 2 | Corpus Acquisition & Model Fine-Tuning (Staging) | ⬜ Not Started | Requires network-connected staging machine |
| Phase 3 | Translation Engine Integration | ⬜ Not Started | Depends on Phase 2 checkpoint |
| Phase 4 | TTS Pipeline | ⬜ Not Started | |
| Phase 5 | Web UI & Authentication | ⬜ Not Started | |
| Phase 6 | PDF Factory & Config Reference | ⬜ Not Started | |
| Phase 7 | Compliance, Security Review & Container Build | ⬜ Not Started | Final gate |

Legend: ⬜ Not Started · 🔄 In Progress · ✅ Complete · ❌ Blocked

---

## Phase 1 — Foundation

**Goal:** Repository scaffold, config schema, SQLite storage, user profile management, DB migration runner.

### Tasks
- [ ] 1.1 Create directory structure (see PRD §8 tree)
- [ ] 1.2 `config/config.toml.example` — document all keys with types, defaults, ranges
- [ ] 1.3 `config/config.toml` — initial operator deployment copy
- [ ] 1.4 SQLite schema — `schema_version` table + profile tables (telemetry, feedback, word-friction, proficiency, error records)
- [ ] 1.5 `engine/db_migrate.py` — migration runner (version compare, sequential apply, rollback on failure)
- [ ] 1.6 `engine/migrations/001.sql` — initial schema migration
- [ ] 1.7 Profile management module — create, select, rename, delete (with secure erase: shred/null-overwrite)
- [ ] 1.8 Input sanitisation module — strip null bytes, control chars, overlong UTF-8, shell metacharacters
- [ ] 1.9 `tests/test_schema_migration.py` — migration runner tests (N-1 upgrade, future version exit, rollback on bad SQL)
- [ ] 1.10 `tests/test_input_sanitisation.py` — sanitisation tests (null bytes, control chars, 513-token rejection, 100 MB prompt)

**Acceptance:** `pytest tests/test_schema_migration.py tests/test_input_sanitisation.py` passes.

---

## Phase 2 — Corpus Acquisition & Model Fine-Tuning (Staging Machine)

**Goal:** Acquire corpus artifacts, prepare training data, fine-tune mT5-small, pass quality gate, record `corpus_manifest.lock`.

> ⚠️ This phase runs on a **network-connected staging machine** only. No network activity is permitted on the air-gapped host.

### Tasks
- [ ] 2.1 `scripts/requirements-staging.txt` — pin Python 3.11.x deps (transformers, datasets, sacrebleu, torch, etc.)
- [ ] 2.2 `scripts/fetch_corpus.sh` — download Perseus Digital Library excerpts, Latin Vulgate parallel text, LatinISE corpus, mT5-small base weights; record SHA-256 for each
- [ ] 2.3 `corpus/spot_check.tsv` — author 50 curated EN↔LA reference pairs for spot-check quality gate
- [ ] 2.4 `corpus/validation_split.tsv` — ≥500 stratified sentence pairs (levels 1–6, both directions) for chrF evaluation
- [ ] 2.5 `scripts/prepare_training_data.py` — apply corpus filtering rules (Vulgate post-Classical exclusion, Leipzig post-300 CE exclusion), align parallel pairs, tokenise, output HuggingFace `datasets` splits
- [ ] 2.6 `config/finetune_config.yaml` — hyperparameters (learning rate, batch size, epoch count, model version)
- [ ] 2.7 `scripts/finetune_mt5.py` — supervised fine-tuning of mT5-small with multi-task prefix conditioning
- [ ] 2.8 `scripts/verify_checkpoint.py` — spot-check gate (≥40/50 pairs = 80%)
- [ ] 2.9 `scripts/eval_chrf.py` — chrF evaluation against `validation_split.tsv` (threshold ≥45 both directions); breakdown by direction/level
- [ ] 2.10 Run quality gate; record results in `docs/finetuning_procedure.md` (pass count, chrF scores, date, operator)
- [ ] 2.11 Record all SHA-256 checksums + quality gate results in `corpus_manifest.lock`
- [ ] 2.12 Package checkpoint + artifacts for physical media transfer

**Acceptance:** Both quality gate sub-checks pass (spot-check ≥80%, chrF ≥45 both directions). `corpus_manifest.lock` updated and complete. `docs/finetuning_procedure.md` records the build run.

**Escalation path:** If 2 consecutive runs fail either gate → corpus expansion (≥500 pairs per failing band) + hyperparameter review before attempt 3. If 3 consecutive failures → halt and escalate to project lead.

---

## Phase 3 — Translation Engine Integration

**Goal:** Integrate fine-tuned checkpoint; implement prefix routing, reading-age grader, Barbarian Mode, LA→EN morphological pre-processor, Whitaker's Words fallback.

### Tasks
- [ ] 3.1 Load `mT5-small` fine-tuned checkpoint from `/app/models/mt5-latin/`; verify SHA-256 at startup against `corpus_manifest.lock`
- [ ] 3.2 `engine/prefix_router.py` — build prefix string from direction + level + mode (e.g., `translate en-la age-8:`)
- [ ] 3.3 `engine/reading_age.py` — map level 1–6 to prefix age tag and vocabulary constraint metadata
- [ ] 3.4 `engine/barbarian.py` — Barbarian Mode prefix builder + post-processor (enforce imperative over-use, broken case inflections)
- [ ] 3.5 `engine/morphological.py` — Whitaker's Words data loader; principal-parts lookup; confidence-gated fallback (threshold 0.6); annotate `[FALLBACK: <token>]` on fallback tokens
- [ ] 3.6 `engine/la_en_pipeline.py` — LA→EN pipeline: tokenise → principal-parts → case/mood disambiguation → mT5 decode → UK English normalisation
- [ ] 3.7 `engine/output_postprocessor.py` — SOV enforcement for Latin output, UK English spelling normalisation
- [ ] 3.8 `engine/translation_engine.py` — orchestrate the full pipeline; enforce 512-token hard cap (reject oversized input before inference)
- [ ] 3.9 `tests/test_translation_engine.py` — unit tests per prefix type (≥5 pairs per direction), confidence gate + fallback annotation, SOV per level, subjunctive at L5–6, Barbarian Mode checks, quality gate regression (marked `slow`)
- [ ] 3.10 `tests/test_reading_age.py` — one test per level (vocabulary + syntax complexity), mid-session level switch

**Acceptance:** `pytest tests/test_translation_engine.py tests/test_reading_age.py` passes (excluding `slow` marker).

---

## Phase 4 — Text-to-Speech Pipeline

**Goal:** Implement Classical Latin phonetic mapping engine and espeak-ng integration via pyttsx3.

### Tasks
- [ ] 4.1 `engine/phonetic_mapper.py` — macron resolution (precomposed Unicode → espeak-ng `[[len 180]]` annotations), hard consonant enforcement (C→/k/, G→/g/, V→/w/), diphthong mapping (ae→/aɪ/, oe→/ɔɪ/)
- [ ] 4.2 `engine/tts_engine.py` — pyttsx3 binding locked to espeak backend; `playback` (audio device, no file write), `export` (HTTP download response, no file write), `both` mode; interrupt-on-new-request behaviour
- [ ] 4.3 Verify espeak-ng binary + voice data bundled in container image; no host TTS dependency
- [ ] 4.4 `tests/test_tts.py` — macron annotation unit test (Rōma, Mārcus), hard consonant mapping (Caesar), diphthong mapping, export mode HTTP response headers + no file written, playback no download response, both mode, espeak driver assertion

**Acceptance:** `pytest tests/test_tts.py` passes.

---

## Phase 5 — Web UI & Authentication

**Goal:** Flask/FastAPI loopback-bound server, full web UI, profile management interface, adaptive learning dashboard, session token auth, WCAG 2.1 Level A.

### Tasks
- [ ] 5.1 `app.py` (or `main.py`) — Flask or FastAPI server; bind to `127.0.0.1` only; port from `config.toml`; port-in-use check → exit with error message
- [ ] 5.2 Startup — generate 128-bit session token via `secrets.token_hex()`, write to `~/.airgap-translator/session.token` (permissions 600), print `Ready: http://127.0.0.1:<port>/?token=<hex_token>` to stdout
- [ ] 5.3 Authentication middleware — validate token on first load, issue session cookie, redirect to path without token param; suppress token query string from access log; reject re-submitted token after first use; HTTP 409 on second concurrent session; HTTP 401 on idle timeout
- [ ] 5.4 SIGTERM handler — 5-second grace window; drop in-flight requests at expiry; delete token file; exit code 0
- [ ] 5.5 Config validation at startup — validate all `config.toml` keys; reset invalid values to defaults with WARN log entry
- [ ] 5.6 UI pages — translation input/output (with thumbs-up/down controls), level selector (persistent header, levels 1–6 + Barbarian Mode), profile management, TTS mode selection, corpus import trigger, PDF generation request, adaptive learning dashboard, About/Licenses page
- [ ] 5.7 Operation status badge — shown during in-flight requests; cleared on response; graceful degradation when JS disabled
- [ ] 5.8 WCAG 2.1 Level A — keyboard navigation, `<label for>`/`aria-label` on all controls, alt text on images, 4.5:1 contrast, `<html lang="en-GB">`, `aria-describedby` on error messages
- [ ] 5.9 Level selector — persist selected level per profile in SQLite; restore on login; immediate effect on next request; no confirmation required
- [ ] 5.10 All UI assets bundled — no external CDN, fonts, or remote assets
- [ ] 5.11 `tests/test_auth_session.py` — token not in access log after redirect, cookie auth, token file absent post-shutdown, HTTP 409 second session, idle timeout HTTP 401, config validation WARN log, SIGTERM grace window (4 assertions), startup URL format
- [ ] 5.12 `tests/test_port_startup.py` — port-in-use exit with non-zero code + correct error message, startup URL stdout format
- [ ] 5.13 `tests/test_adaptive_learning.py` — Clear Telemetry scope, proficiency accumulation across level switches, thumbs-up/down feedback record (3 tests)
- [ ] 5.14 `tests/test_error_handling.py` — lenient mode best-effort + log truncation, strict mode `[UNKNOWN: <token>]`, corrupt SQLite integrity_check path

**Acceptance:** `pytest tests/test_auth_session.py tests/test_port_startup.py tests/test_adaptive_learning.py tests/test_error_handling.py` passes.

---

## Phase 6 — PDF Factory & Config Reference

**Goal:** fpdf2-based PDF generation (workbooks, note sheets, declension matrices); FreeSerif font bundle; `config.toml.example` complete.

### Tasks
- [ ] 6.1 `engine/pdf_factory.py` — fpdf2 PDF generation; A4 default (configurable to Letter); 20 mm margins (configurable 10–40); 300 DPI rasterised elements; FreeSerif font for macron/diacritic support; serve as HTTP download response (no file written to disk)
- [ ] 6.2 Alternating line buffer layout — translation items followed by open spacing for handwritten entries
- [ ] 6.3 Declension matrix layout — empty tabular grids for case inflections targeting weak terms from adaptive engine
- [ ] 6.4 Note-taking margin layout — fixed structural borders for physical notes
- [ ] 6.5 `config/config.toml.example` — all keys present: `server.port`, `server.session_timeout_minutes`, `pdf.paper_size`, `pdf.margin_mm`, `tts.output_mode`; document types, defaults, valid ranges, descriptions; must be in sync with application code
- [ ] 6.6 `tests/test_pdf.py` — macron rendering (ā ē ī ō ū via FreeSerif), alternating line buffers, declension matrices, note-taking margins all present in output, Letter paper size via config, HTTP 200 + `Content-Disposition: attachment` + `Content-Type: application/pdf`, no PDF file written to container filesystem

**Acceptance:** `pytest tests/test_pdf.py` passes.

---

## Phase 7 — Compliance, Security Review & Container Build

**Goal:** FIPS stack verification, DISA STIG audit log, OWASP input sanitisation, OCI container build with SHA-256 artifact verification, full test suite pass, documentation complete.

### Tasks
- [ ] 7.1 `Containerfile` — base image with OpenSSL ≥3.0 FIPS provider (RHEL 9 UBI or Ubuntu 22.04 + openssl-fips); build-time `openssl fips-mode-set 1` assertion (fail build if not supported); rootless execution; `--network=none` enforcement; bundle espeak-ng, DejaVu Sans / FreeSerif fonts, mT5-small checkpoint, Whitaker's Words data
- [ ] 7.2 Build-time SHA-256 verification of all artifacts against `corpus_manifest.lock`
- [ ] 7.3 `docs/fips_verification.md` — OpenSSL FIPS provider build assertion procedure
- [ ] 7.4 `docs/deployment_checklist.md` — auditd rules (5 rules listed in PRD §6.2), backup cron task registration + timezone guidance, physical media handling steps, SLA verification procedure (steps 1–7), pre-upgrade backup step, SIGTERM guidance, secure erase residual risk note
- [ ] 7.5 `docs/architecture.md` — component descriptions, data flow, Mermaid diagrams (replicate and extend PRD §5 diagram)
- [ ] 7.6 `docs/adaptive_learning_schema.md` — full SQLite schema documentation
- [ ] 7.7 `docs/input_sanitization_policy.md` — sanitisation rules, token cap, CSV formula strip policy
- [ ] 7.8 `docs/finetuning_procedure.md` — corpus filtering records, filtering counts (retained/excluded per source), training procedure, quality gate log, escalation log if applicable, staging machine spec
- [ ] 7.9 Produce all 12 required documentation deliverables under `docs/` (see PRD §10 table)
- [ ] 7.10 `tests/test_container_integrity.py` — SHA-256 artifact verification at build time fails on mismatch, end-to-end smoke test inside container (translation → PDF → TTS export)
- [ ] 7.11 Run full pytest suite: `pytest --junitxml=docs/test_results/results.xml`; zero failures, zero errors; commit `docs/test_results/results.xml`
- [ ] 7.12 Run `pytest -m slow` to execute chrF quality gate regression test; assert chrF ≥45 both directions
- [ ] 7.13 Manual SLA verification on target host (4-core x86-64, no GPU) — record all measured values in `docs/deployment_checklist.md`
- [ ] 7.14 Security review — OWASP Top 10, injection avoidance (CSV formula strip, no dynamic expression eval), least privilege (rootless UID), zero-network enforcement
- [ ] 7.15 Export final OCI image tarball; record SHA-256 in release notes; prepare physical media transfer package

**Acceptance:** Full pytest suite passes (zero failures/errors). All 12 documentation deliverables baselined. Compliance gate signed off. OCI image tarball ready for physical media transfer.

---

## Key Cross-Cutting Requirements

| Requirement | Where Enforced |
|---|---|
| All log timestamps in UTC ISO 8601 | Phase 5 logging setup |
| Log content truncated to 64 chars | Phase 5 logging setup |
| Token file deleted on shutdown | Phase 5 SIGTERM handler |
| Rootless container, UID-isolated profile dir (700) | Phase 7 Containerfile |
| `--network=none` Podman flag | Phase 7 Containerfile / launch script |
| SHA-256 verification at startup | Phase 3 + Phase 7 |
| Single-writer queue for SQLite writes | Phase 1 DB layer |
| UK English spelling normalisation in LA→EN output | Phase 3 post-processor |
| No file written to disk for PDF or TTS export | Phase 4 + Phase 6 |
| About/Licenses page — all corpus licences listed | Phase 5 UI |

---

## Issues & Blockers

_None at this time._

---

## Build Record Summary

| Run | Date | Operator | Spot-Check | chrF EN→LA | chrF LA→EN | Result |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
