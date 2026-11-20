# Air-Gapped Adaptive Latin Translation & Pedagogical System

**Version:** 1.0.0 (Pre-release)  
**Author:** Iain Reid  
**Status:** In Development. Documentation set 2.0 draft (2026-11-20); no image built, no model trained  
**Compliance targets (mapped, not claimed):** NIST SP 800-53 · OWASP Top 10 · CIS Benchmark Level 2 · DISA STIG · FIPS 140-3; voluntary Secure by Design, JSP 936, JSP 441

---

## What This Is

A self-contained, offline desktop application providing bidirectional translation between **UK English and Classical Latin**, with an integrated adaptive learning engine, printable PDF workbook generation, and Classical Latin text-to-speech synthesis.

The system operates with zero network connectivity at runtime. All model weights, corpus data, fonts, and dependencies are bundled within the OCI container image and transferred to the air-gapped host via physical media.

---

## Key Features

| Feature | Description |
|---|---|
| **Two-Way Translation** | UK English ↔ Classical Latin via fine-tuned mT5-small (~300 MB) |
| **Reading Age Adaptation** | Six levels (Ages 2–4 through Adult) plus Barbarian Mode stylistic register |
| **Morphological Fallback** | Whitaker's Words dictionary for low-confidence token resolution |
| **Adaptive Learning** | Per-profile SQLite telemetry; targets weak vocabulary dynamically |
| **PDF Workbooks** | fpdf2-generated A4 printable exercise sheets with handwriting space |
| **Classical Latin TTS** | espeak-ng with phonetic mapping for macrons, hard consonants, diphthongs |
| **Secure Local UI** | Flask/FastAPI loopback-only HTTP server; single-session token auth |
| **Air-Gap Native** | Podman rootless container; `--network=none`; FIPS 140-3 crypto |

---

## Repository Structure

```
.airgap-translator/
├── Containerfile                  # OCI image build; FIPS assertion
├── corpus_manifest.lock           # SHA-256 checksums + quality gate records
├── config/
│   ├── config.toml                # Active deployment configuration
│   ├── config.toml.example        # Reference for all config keys (canonical)
│   └── finetune_config.yaml       # Fine-tuning hyperparameters (staging only)
├── corpus/
│   ├── spot_check.tsv             # 50 curated EN↔LA pairs for quality gate
│   └── validation_split.tsv       # ≥500 stratified pairs for chrF evaluation
├── docs/                          # DOC-01..15 suite, standards matrix, components/, archive-v1/
│   ├── README.md
│   ├── DOC-01-Architecture-Guide.md … DOC-15-Artifact-Collection-Guide.md
│   ├── standards-conformance-matrix.md
│   ├── component-register.md, components/
│   ├── adaptive_learning_schema.md, input_sanitization_policy.md
│   ├── finetuning_procedure.md, fips_verification.md, deployment_checklist.md
│   └── test_results/results.xml   # JUnit XML dated 2026-06-08
├── brd/                           # BRD set and tube map (generated)
├── tools/                         # gen_brd.py, gen_components.py
├── engine/
│   ├── translation_engine.py
│   ├── prefix_router.py
│   ├── reading_age.py
│   ├── barbarian.py
│   ├── morphological.py
│   ├── la_en_pipeline.py
│   ├── output_postprocessor.py
│   ├── phonetic_mapper.py
│   ├── tts_engine.py
│   ├── pdf_factory.py
│   ├── db_migrate.py
│   └── migrations/
│       └── 001.sql
├── models/
│   └── mt5-latin/                 # Fine-tuned checkpoint (build artifact)
├── scripts/
│   ├── fetch_corpus.sh            # Staging machine only
│   ├── prepare_training_data.py
│   ├── finetune_mt5.py
│   ├── verify_checkpoint.py
│   ├── eval_chrf.py
│   └── requirements-staging.txt
└── tests/
    ├── test_translation_engine.py
    ├── test_reading_age.py
    ├── test_input_sanitisation.py
    ├── test_pdf.py
    ├── test_tts.py
    ├── test_auth_session.py
    ├── test_adaptive_learning.py
    ├── test_error_handling.py
    ├── test_port_startup.py
    ├── test_schema_migration.py
    └── test_container_integrity.py
```

---

## Quick Start (Air-Gapped Host)

> Prerequisites: Podman installed; OCI image tarball + release notes transferred via write-protected physical media.

```bash
# 1. Verify tarball integrity
sha256sum airgap-translator-<version>.tar
# Compare against SHA-256 in release notes. Do not proceed if mismatch.

# 2. Import container image
podman load -i airgap-translator-<version>.tar

# 3. Copy reference config (first deployment only)
cp config/config.toml.example ~/.airgap-translator/config.toml

# 4. Run (rootless, no network)
podman run --rm --network=none \
  -v ~/.airgap-translator:/home/appuser/.airgap-translator:Z \
  -p 127.0.0.1:8080:8080 \
  airgap-translator:<version>

# 5. Copy the printed URL from stdout and open in Firefox ESR or Chromium
# Example: Ready: http://127.0.0.1:8080/?token=<hex_token>
```

See [DOC-09](.airgap-translator/docs/DOC-09-Deployment-Guide.md) for full deployment procedure including auditd configuration and backup cron setup.

---

## Staging Machine Setup (Model Fine-Tuning)

> Requires: Ubuntu 22.04 LTS (or Windows 10/11 + WSL2 Ubuntu 22.04), Python 3.11.x, 16 GB RAM minimum, network access during corpus fetch only.

```bash
# 1. Install staging dependencies
pip install -r scripts/requirements-staging.txt

# 2. Download corpus artifacts and base model weights (network required)
bash scripts/fetch_corpus.sh

# 3. Prepare training data (filtering, alignment, tokenisation)
python scripts/prepare_training_data.py

# 4. Fine-tune mT5-small (8–14 hours CPU-only; 45–90 min with NVIDIA GPU ≥8 GB VRAM)
python scripts/finetune_mt5.py

# 5. Run quality gate (both sub-checks must pass)
python scripts/verify_checkpoint.py   # Spot-check: ≥40/50 pairs
python scripts/eval_chrf.py           # chrF: ≥45 both EN→LA and LA→EN

# 6. Package for transfer
# Update corpus_manifest.lock with SHA-256 checksums + quality gate results
```

See [docs/finetuning_procedure.md](.airgap-translator/docs/finetuning_procedure.md) for full procedure and build record.

---

## Running Tests

```bash
# Standard run (excludes slow quality-gate regression test)
pytest --junitxml=docs/test_results/results.xml

# Include slow tests (Phase 7 compliance run)
pytest -m slow --junitxml=docs/test_results/results.xml
```

Zero failures and zero errors are required before the Phase 7 compliance gate is passed.

---

## Configuration Reference

All configuration keys are documented in [`config/config.toml.example`](.airgap-translator/config/config.toml.example). Copy this file to `config.toml` for a new deployment. Key settings:

| Key | Default | Range | Description |
|---|---|---|---|
| `server.port` | `8080` | 1024–65535 | Loopback HTTP server port |
| `server.session_timeout_minutes` | `60` | 5–1440 | Idle session expiry |
| `pdf.paper_size` | `A4` | `A4`, `Letter` | PDF output paper size |
| `pdf.margin_mm` | `20` | 10–40 | PDF margin in millimetres |
| `tts.output_mode` | `playback` | `playback`, `export`, `both` | TTS audio output behaviour |

Invalid or out-of-range values are silently reset to defaults with a `WARN` entry in `/logs/error.log`.

---

## Reading Levels

| Level | Display Name | Ages |
|---|---|---|
| 1 | Beginner | 2–4 |
| 2 | Elementary | 5–6 |
| 3 | Primary | 7–8 |
| 4 | Intermediate | 8–12 |
| 5 | Secondary | 12–16 |
| 6 | Advanced | 16–18 / Adult |
| — | Barbarian Mode | Any |

The active level is displayed persistently in the UI header and can be changed at any time without navigating away from the current page.

---

## Performance SLAs

| Operation | Max Latency | Host Baseline |
|---|---|---|
| Translation EN→LA or LA→EN (≤512 tokens) | 5 seconds | 4-core x86-64, no GPU |
| Barbarian Mode translation | 5 seconds | 4-core x86-64, no GPU |
| PDF generation (≤50 pages) | 10 seconds | — |
| TTS synthesis playback start (≤512 tokens) | 3 seconds | espeak-ng |
| SQLite proficiency query | 200 ms | — |
| Container startup (ready to serve) | 30 seconds | — |

---

## Security & Compliance

> Design intent, not evidence. The PRD (section 13) lists 14 known gaps between the requirements and the code, including token re-use, a stubbed startup checksum and an unproven run line.

- **FIPS 140-3:** All cryptographic operations use Python `hashlib`/`hmac`/`secrets` via OpenSSL ≥3.0 FIPS provider. SHA-256 used for artifact integrity; HMAC-SHA-256 for session cookie signing; OS CSPRNG for token generation.
- **Zero network at runtime:** Podman `--network=none` enforced; server binds to `127.0.0.1` only.
- **Least privilege:** Rootless Podman execution; profile directory owned by isolated UID with `700` permissions.
- **DISA STIG audit logging:** Delegated to host `auditd`; five required watch rules defined in [docs/deployment_checklist.md](.airgap-translator/docs/deployment_checklist.md).
- **OWASP Top 10:** Input sanitisation strips null bytes, control characters, and shell metacharacters; CSV data treated as string literals only; no dynamic expression evaluation.

See [DOC-07](.airgap-translator/docs/DOC-07-Security-Analysis-and-Compliance.md) and the [standards matrix](.airgap-translator/docs/standards-conformance-matrix.md). Controls are mapped, not claimed: none is Evidenced yet.

---

## Bundled Corpus & Licence Notices

| Artifact | Licence |
|---|---|
| Perseus Digital Library Latin excerpts | CC BY-SA 3.0 |
| Latin Vulgate Bible parallel text | Public Domain |
| Leipzig LatinISE corpus | CC BY |
| Whitaker's Words dictionary data | Public Domain |
| Google mT5-small base weights | Apache 2.0 |
| DejaVu Sans / FreeSerif fonts | GPL with font exception |
| Fine-tuned `mt5-latin` checkpoint | Internal derivative artifact |

---

## Documentation

Full documentation set is under [`.airgap-translator/docs/`](.airgap-translator/docs/README.md). Start with [`docs/README.md`](.airgap-translator/docs/README.md) for the register of DOC-01 to DOC-15 with state. The BRD set and tube map are in [`.airgap-translator/brd/`](.airgap-translator/brd/README.md) and the requirements are in [`prd.md`](prd.md) (section 11).

---

## Implementation Progress

See [`progress.md`](progress.md) for the current phase-by-phase task checklist and build record.
