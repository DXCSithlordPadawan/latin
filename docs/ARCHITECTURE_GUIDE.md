---
title: Architecture Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Architecture Guide

## 1. System Overview

The Air-Gapped Latin Translator is a self-contained, offline application providing bidirectional UK English ↔ Classical Latin translation with adaptive learning, PDF workbook generation, and Classical Latin TTS synthesis.

All components run inside a single rootless Podman container. The container operates with `--network=none`; no data leaves the host at runtime.

## 2. Component Map

| Component | Module | Responsibility |
|---|---|---|
| Config Loader | `engine/config_loader.py` | Parse `config.toml`, validate keys, apply defaults |
| Input Sanitiser | `engine/sanitiser.py` | Strip control chars, null bytes, shell metacharacters; enforce 512-token cap |
| Prefix Router | `engine/prefix_router.py` | Build mT5 multi-task prefix strings |
| Reading Age Adapter | `engine/reading_age.py` | Level 1–6 spec metadata and prefix age tags |
| Translation Engine | `engine/translation_engine.py` | Orchestrate full translation pipeline; load checkpoint |
| Barbarian Mode | `engine/barbarian.py` | Barbarian prefix builder and post-processor |
| Morphological Analyser | `engine/morphological.py` | Whitaker's Words fallback; confidence-gated annotation |
| LA→EN Pipeline | `engine/la_en_pipeline.py` | Tokenise → principal-parts → mT5 decode → UK English normalise |
| Output Post-Processor | `engine/output_postprocessor.py` | SOV hint, UK English spelling normalisation |
| Phonetic Mapper | `engine/phonetic_mapper.py` | Macron resolution, hard consonants, diphthongs → espeak-ng annotations |
| TTS Engine | `engine/tts_engine.py` | pyttsx3/espeak-ng; playback/export/both modes |
| PDF Factory | `engine/pdf_factory.py` | fpdf2 workbook/note_sheet/declension generation |
| DB Migration Runner | `engine/db_migrate.py` | Schema versioning, sequential migration, rollback |
| Profile Manager | `engine/profile_manager.py` | Profile CRUD, secure erase, telemetry clear |
| Web Application | `app.py` | Flask loopback server, auth, session management, routes |

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Raw Local File / Terminal Input] --> B[Input Sanitisation Buffer]
    B --> C{Direction & Mode Matrix}
    C -->|EN→LA standard| D[Reading Age Prefix Builder]
    C -->|EN→LA barbarian| E[Barbarian Prefix Builder]
    C -->|LA→EN| F[Morphological Pre-processor\nWhitaker's Words principal-parts lookup]
    D --> G[mT5-small Fine-tuned Checkpoint\n/app/models/mt5-latin/]
    E --> G
    F --> G
    G --> H{Confidence ≥ 0.6?}
    H -->|Yes| I[Output Post-processor\nUK English normalisation / SOV enforcement]
    H -->|No| J[Whitaker's Words Morphological Fallback]
    J --> I
    I --> K[Adaptive Learning Engine]
    K <--> L[(SQLite State Database\nper-profile isolated — ACL protected)]
    L --> M[Local Web UI\nFlask — 127.0.0.1 only]
    K --> N[Phonetic Mapper\nClassical Latin orthographic mapping]
    K --> O[PDF Layout Factory\nfpdf2 + FreeSerif font]
    N --> P[Offline TTS — pyttsx3 / espeak-ng]
    O --> Q[PDF bytes → HTTP download response]
```

## 4. Security Architecture

```mermaid
graph LR
    Browser["Firefox ESR / Chromium\n127.0.0.1 only"] -->|HMAC-SHA-256 cookie| Server["Flask Server\n127.0.0.1:8080"]
    Server --> Auth["Session Token\n128-bit CSPRNG\n~/.airgap-translator/session.token\nperm 600"]
    Server --> DB["SQLite Profile DB\n~/.airgap-translator/profiles/<slug>.db\nperm 600, dir 700"]
    Server --> Model["mT5-small Checkpoint\n/app/models/mt5-latin/\nSHA-256 verified at startup"]
    Container["Podman Container\nrootless UID 10001\n--network=none"] -.->|isolates| Server
```

## 5. Storage Layout

```
~/.airgap-translator/
├── config.toml                  # Operator configuration (700 dir, 600 file)
├── session.token                # Deleted on shutdown (600)
└── profiles/
    └── <slug>.db                # Per-profile SQLite (700 dir, 600 file)

/backups/airgap-translator/      # Host-level cron backup target
└── YYYY-MM-DD/
    └── <slug>.db

/app/logs/
└── error.log                    # Rotating log (max 10 MB × 3 rotations)
```

## 6. Authentication Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Flask Server
    B->>S: GET /?token=<hex_token>
    S->>S: Validate token against in-memory value
    S->>B: HTTP 302 → / (no token in URL)
    Note over S: Log path only — token stripped from access log
    S->>B: Set session cookie (HMAC-SHA-256)
    B->>S: GET / (cookie)
    S->>S: Validate session cookie
    S->>B: HTTP 200 — page served
```
