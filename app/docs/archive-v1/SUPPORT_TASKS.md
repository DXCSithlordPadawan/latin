---
title: Support Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Support Guide

## 1. Common Faults & Resolution

### Container fails to start

| Symptom | Cause | Resolution |
|---|---|---|
| `ERROR: Port 8080 is already in use` | Port conflict | Edit `config.toml` `server.port`; restart |
| `PRAGMA integrity_check` failure on startup | Corrupt profile database | Restore from backup (see §4.8 of PRD) |
| `ERROR: Failed to load translation model` | Checkpoint missing or corrupt | Re-verify `corpus_manifest.lock` checksums; rebuild image |
| Container exits immediately | FIPS assertion failed | Confirm base image has OpenSSL FIPS provider; rebuild |

### Authentication issues

| Symptom | Resolution |
|---|---|
| `HTTP 401` on every request | Token expired (container restarted). Restart container; use new URL from stdout. |
| `HTTP 409 Conflict` | Another browser tab/window has an active session. Close it or restart container. |
| Token URL not printed | Check stdout capture. Ensure container is not running in detached mode silently. |

### Translation errors

| Symptom | Resolution |
|---|---|
| `[FALLBACK: token]` in output | Token below confidence threshold; Whitaker's Words resolved it. Normal behaviour in strict mode. |
| `[UNKNOWN: token]` in output | Strict mode enabled; token unresolved by both model and Whitaker's fallback. |
| Translation times out (>5 s) | Verify host has ≥4 cores free. Check `/logs/error.log` for inference errors. |

## 2. Log Inspection

```bash
# View recent error log entries (inside container)
podman exec <container_id> tail -100 /app/logs/error.log

# View all log rotations
podman exec <container_id> ls -lh /app/logs/
```

All entries are UTC ISO 8601. User strings are truncated to 64 characters.

## 3. Database Diagnostics

```bash
# Run integrity check on a profile database
sqlite3 ~/.airgap-translator/profiles/<slug>.db "PRAGMA integrity_check;"
# Expected output: ok

# Check schema version
sqlite3 ~/.airgap-translator/profiles/<slug>.db "SELECT version FROM schema_version;"
```

## 4. Audit Log Verification

```bash
auditctl -l | grep airgap
# Must return all 5 rules
```

## 5. Escalation Path

1. Collect `/app/logs/error.log` (sanitised — user strings truncated).
2. Collect `auditctl -l` output.
3. Record exact error message and timestamp (UTC).
4. Escalate to project lead with log excerpt and reproduction steps.
