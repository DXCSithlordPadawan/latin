---
title: Adaptive Learning SQLite Schema
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Adaptive Learning SQLite Schema

Each user profile is stored as an isolated SQLite database at:
`~/.airgap-translator/profiles/<slug>.db`

File permissions: `600` (owner read/write only). Parent directory: `700`.

## Tables

### `schema_version`
Single-row table recording the current schema version integer.
| Column | Type | Notes |
|---|---|---|
| `version` | INTEGER NOT NULL | Current schema version |

### `profile_meta`
Single-row table (id=1) for profile settings.
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Always 1 |
| `profile_slug` | TEXT NOT NULL | URL-safe slug |
| `display_name` | TEXT NOT NULL | Human-readable name |
| `created_at` | TEXT NOT NULL | UTC ISO 8601 |
| `last_login` | TEXT | UTC ISO 8601 or NULL |
| `selected_level` | INTEGER DEFAULT 1 | 1–6 or 7 (Barbarian) |
| `barbarian_mode` | INTEGER DEFAULT 0 | 0/1 boolean |
| `tts_output_mode` | TEXT DEFAULT 'playback' | playback/export/both |
| `error_mode` | TEXT DEFAULT 'lenient' | lenient/strict |

### `word_friction`
Records vocabulary items causing repeated translation failures.
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `word` | TEXT NOT NULL | Latin or English word |
| `direction` | TEXT NOT NULL | en-la or la-en |
| `fail_count` | INTEGER DEFAULT 1 | |
| `last_seen` | TEXT NOT NULL | UTC ISO 8601 |

### `session_history`
Records session start/end and request counts.
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `session_start` | TEXT NOT NULL | UTC ISO 8601 |
| `session_end` | TEXT | UTC ISO 8601 or NULL |
| `request_count` | INTEGER DEFAULT 0 | |

### `translation_feedback`
Thumbs-up/thumbs-down ratings for translation quality.
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `source_text` | TEXT NOT NULL | Truncated to 64 chars |
| `output_text` | TEXT NOT NULL | Truncated to 64 chars |
| `direction` | TEXT NOT NULL | en-la or la-en |
| `level` | TEXT NOT NULL | 1–6 or barbarian |
| `rating` | INTEGER NOT NULL | +1 or -1 |
| `recorded_at` | TEXT NOT NULL | UTC ISO 8601 |

### `proficiency`
Per-word correct/incorrect counts for adaptive targeting.
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `word` | TEXT NOT NULL UNIQUE | |
| `direction` | TEXT NOT NULL | |
| `correct_count` | INTEGER DEFAULT 0 | |
| `incorrect_count` | INTEGER DEFAULT 0 | |
| `last_reviewed` | TEXT | UTC ISO 8601 or NULL |

### `error_records`
Application error log entries (user strings truncated to 64 chars).
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `error_code` | TEXT NOT NULL | |
| `message` | TEXT NOT NULL | Truncated to 64 chars |
| `context` | TEXT | Optional additional context |
| `recorded_at` | TEXT NOT NULL | UTC ISO 8601 |

## Write Concurrency

All writes are serialised through a single `threading.Lock` (`_WRITE_LOCK` in `engine/profile_manager.py`). Concurrent reads are permitted without locking.
