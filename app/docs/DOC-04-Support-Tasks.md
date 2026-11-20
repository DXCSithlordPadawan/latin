# DOC-04 Support Tasks

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Support Lead (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s4.7, s4.8, [DOC-08](DOC-08-Maintenance-Guide.md) |
| **Status** | Runbook drafted from the code; no fault has been reproduced |

> Support works on the air-gapped host only. No remote tooling. Do not copy learner text into tickets.

## 1. Diagnostics

| Task | Command or step | Healthy result |
|---|---|---|
| Is it up | `podman ps`; look for the image tag | Running, healthy |
| Health | `podman healthcheck run <name>` | Exit 0 (TCP connect on 8080; HEALTHCHECK has port fixed at 8080 even if `server.port` changes) |
| Startup line | `podman logs <name>` | One `Ready: http://127.0.0.1:<port>/?token=...` line |
| Error log | `logs/error.log` in the container (UTC, 10 MB x 3) | No ERROR since last start |
| Profile database | `sqlite3 <slug>.db "PRAGMA integrity_check"` | `ok` |
| Schema version | `sqlite3 <slug>.db "SELECT version FROM schema_version"` | Equals target (1) |
| Permissions | `ls -ld ~/.airgap-translator ~/.airgap-translator/profiles` | 700, owner is the container UID mapping |

## 2. Faults and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| "Port N is already in use" and exit 1 | Another process on that port | Change `server.port` in `config.toml`, restart. No automatic fallback |
| 401 on every page | Token wrong or idle timeout passed | Restart container; use the new `Ready:` line |
| 409 Conflict | Another live session | Close it or restart (note G-01: a repeat token link also takes over) |
| 503 | Shutting down | Wait, then restart |
| 400 "Input exceeds the 512-token hard cap" | Input too long | Shorten input |
| Every Latin word shows `[FALLBACK: ...]` | Whitaker data missing from the image (G-11) | Rebuild image with `data/whitakers_words`; check [DOC-15](DOC-15-Artifact-Collection-Guide.md) |
| "Translation failed" 500 | Model not loaded or checkpoint missing | Check log for "Failed to load translation model"; check `models/mt5-latin` |
| PDF shows boxes for macrons | FreeSerif missing (`static/fonts`) | Rebuild image with the font |
| No sound in `playback` | No audio device passed to the container | Pass the device, or use `export` |
| Exit with "schema version N is newer" | Database from a newer image | Restore the pre-upgrade backup or run the newer image |
| Exit with "integrity check failed" | Corrupt file | Restore from backup (section 3) |
| Browser cannot reach the app | Port publishing with `--network=none` (G-10) | Escalate; record the exact `podman run` line |

## 3. Restore a profile

1. Stop the container.
2. Pick the snapshot under `/backups/airgap-translator/<date>/`.
3. Copy `<slug>.db` over `~/.airgap-translator/profiles/<slug>.db`.
4. Set owner and mode (`700` directory, `600` file).
5. Start the container; confirm no integrity error at startup.

## 4. Escalation

| Level | Who | When |
|---|---|---|
| 1 | Operator | Everything above |
| 2 | Project Lead | Defect against an SLA, any suspected token leak, any failed checksum |
| 3 | Security Authority | Suspected tampering of media, media hash mismatch, any auditd gap |

## 5. Records

Keep a dated note of each fault: UTC time, symptom, action, result. These feed the evidence for SbD-TLM-02 (reassessment) in the [standards matrix](standards-conformance-matrix.md).

## Sources

[PRD](../../prd.md) s4.7, s4.8; `app.py`; `engine/db_migrate.py`; `Containerfile` HEALTHCHECK.
