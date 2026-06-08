---
title: Architecture Detail
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Architecture Detail

See `ARCHITECTURE_GUIDE.md` for the primary architecture document including component map, data flow diagrams, and security architecture.

This document records supplementary architectural decisions and constraints.

## 1. Single-Process Model

The application runs as a single Python process (Flask threaded server). The SQLite write queue is implemented as a `threading.Lock` rather than a separate process or async queue, relying on Flask's threaded request handling and the single-writer pattern to avoid `SQLITE_BUSY` contention.

## 2. Model Loading Strategy

The mT5-small checkpoint is loaded into memory at startup (`engine.translation_engine.TranslationEngine.load()`). The first inference request after startup may exceed the 5-second SLA by up to 10 seconds (warm-up exclusion). Subsequent requests operate within SLA.

## 3. No Persistent TTS Files

TTS export mode generates WAV bytes in memory via a temporary file pattern:
1. `pyttsx3.save_to_file()` writes to a temp path.
2. Bytes are read immediately.
3. The temp file is overwritten with zeros and deleted before the HTTP response is returned.

This ensures no WAV file persists on the container filesystem.

## 4. PDF In-Memory Generation

fpdf2's `output()` method writes to a `BytesIO` buffer. The buffer is returned directly as the HTTP response body. No PDF file is written to any path.

## 5. Token Authentication Design

The session token is:
- Generated at startup via `secrets.token_hex(16)` (128-bit entropy).
- Written to `~/.airgap-translator/session.token` (permissions 600).
- Validated exactly once via the `?token=` query parameter.
- After validation, a session cookie is issued and the token parameter is stripped from the URL.
- The token is held in memory only for subsequent validation of the `?token=` parameter (which is not re-accepted after first use).
- Deleted from disk and cleared from memory on shutdown (SIGTERM or normal exit).
