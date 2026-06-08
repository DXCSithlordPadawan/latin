---
title: Maintenance Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Maintenance Guide

## 1. Daily

- [ ] Confirm backup cron completed successfully: `ls -lhd /backups/airgap-translator/$(date +%Y-%m-%d)/`
- [ ] Check error log for overnight warnings: `tail -50 /app/logs/error.log`

## 2. Weekly

- [ ] Verify all 5 auditd rules are active: `auditctl -l | grep airgap`
- [ ] Confirm 7-day backup retention policy is running (old snapshots removed): `ls /backups/airgap-translator/`
- [ ] Check container image for any known CVEs on staging machine (offline scan tooling)

## 3. Monthly

- [ ] Review error log rotation: confirm log files do not exceed 3 rotations × 10 MB
- [ ] Verify profile database integrity: `sqlite3 <slug>.db "PRAGMA integrity_check;"`
- [ ] Review word-friction dashboard for anomalies indicating corpus quality issues
- [ ] Confirm backup restore procedure works: restore a test profile from backup, verify integrity_check passes

## 4. Quarterly

- [ ] Review `corpus_manifest.lock` — confirm checkpoint version and chrF scores remain above thresholds
- [ ] Assess whether a model refresh is required (see PRD §7.1 trigger conditions)
- [ ] Review DISA STIG compliance — re-run auditd rule check; review access logs
- [ ] Confirm OCI image tag is current; plan upgrade if a newer build exists on staging
- [ ] Review and update documentation if any procedures have changed

## 5. Log Rotation Policy

Logs are rotated automatically by the Python `RotatingFileHandler`:
- Maximum size per file: **10 MB**
- Maximum rotations retained: **3** (plus the active log = 4 files total)
- Rotation naming: `error.log`, `error.log.1`, `error.log.2`, `error.log.3`

No manual intervention is required for log rotation.

## 6. Backup Verification Procedure

```bash
# 1. Identify most recent backup
BACKUP_DATE=$(ls /backups/airgap-translator/ | sort | tail -1)
echo "Most recent backup: $BACKUP_DATE"

# 2. Copy to temp location
cp /backups/airgap-translator/$BACKUP_DATE/<slug>.db /tmp/verify_backup.db

# 3. Run integrity check
sqlite3 /tmp/verify_backup.db "PRAGMA integrity_check;"
# Expected: ok

# 4. Remove temp copy
rm /tmp/verify_backup.db
```
