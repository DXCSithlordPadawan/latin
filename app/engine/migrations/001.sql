-- Migration 001 — Initial schema
-- Creates schema_version table and all profile tables.
-- Applied by engine/db_migrate.py on first startup against a new database.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Schema version tracking (single row)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
INSERT INTO schema_version (version) VALUES (1);

-- User profile metadata (one row per profile database — this IS the profile db)
CREATE TABLE IF NOT EXISTS profile_meta (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    profile_slug  TEXT NOT NULL,
    display_name  TEXT NOT NULL,
    created_at    TEXT NOT NULL,  -- UTC ISO 8601
    last_login    TEXT,
    selected_level INTEGER NOT NULL DEFAULT 1,  -- 1–6 or 7=Barbarian
    barbarian_mode INTEGER NOT NULL DEFAULT 0,   -- 0/1 boolean
    tts_output_mode TEXT NOT NULL DEFAULT 'playback',
    error_mode    TEXT NOT NULL DEFAULT 'lenient'  -- 'lenient' or 'strict'
);

-- Word friction / vocabulary difficulty telemetry
CREATE TABLE IF NOT EXISTS word_friction (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    word          TEXT NOT NULL,
    direction     TEXT NOT NULL,  -- 'en-la' or 'la-en'
    fail_count    INTEGER NOT NULL DEFAULT 1,
    last_seen     TEXT NOT NULL   -- UTC ISO 8601
);
CREATE INDEX IF NOT EXISTS idx_word_friction_word ON word_friction(word);

-- Session interaction history
CREATE TABLE IF NOT EXISTS session_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_start TEXT NOT NULL,  -- UTC ISO 8601
    session_end   TEXT,
    request_count INTEGER NOT NULL DEFAULT 0
);

-- Translation feedback ratings (thumbs-up / thumbs-down)
CREATE TABLE IF NOT EXISTS translation_feedback (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_text   TEXT NOT NULL,   -- truncated to 64 chars
    output_text   TEXT NOT NULL,   -- truncated to 64 chars
    direction     TEXT NOT NULL,   -- 'en-la' or 'la-en'
    level         TEXT NOT NULL,   -- '1'–'6' or 'barbarian'
    rating        INTEGER NOT NULL, -- +1 or -1
    recorded_at   TEXT NOT NULL    -- UTC ISO 8601
);

-- Proficiency metrics per vocabulary item
CREATE TABLE IF NOT EXISTS proficiency (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    word          TEXT NOT NULL UNIQUE,
    direction     TEXT NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    incorrect_count INTEGER NOT NULL DEFAULT 0,
    last_reviewed TEXT  -- UTC ISO 8601
);
CREATE INDEX IF NOT EXISTS idx_proficiency_word ON proficiency(word);

-- Error records
CREATE TABLE IF NOT EXISTS error_records (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    error_code    TEXT NOT NULL,
    message       TEXT NOT NULL,   -- user string content truncated to 64 chars
    context       TEXT,
    recorded_at   TEXT NOT NULL    -- UTC ISO 8601
);
