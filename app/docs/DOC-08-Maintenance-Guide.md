# DOC-08 Maintenance Guide

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Support Lead (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s4.8, s7, [DOC-09](DOC-09-Deployment-Guide.md) |
| **Status** | Schedule only. No task has been run on a deployed host |

> Nothing here has been verified against a running system.

## 1. Schedule

| Frequency | Task | Owner | Evidence |
|---|---|---|---|
| Daily (automatic) | Backup cron copies the profile directory at 02:00 | Operator | Snapshot folder with that date |
| Weekly | Check latest backup is under 24 hours old; scan `error.log` for ERROR and WARN | Operator | Dated note |
| Weekly | `auditctl -l` shows five `airgap_*` rules | Operator | Output saved |
| Monthly | Restore one backup to a scratch location and run `PRAGMA integrity_check` | Operator | Result note |
| Monthly | Review feedback and fallback counts for drift against the ODD (JSP936-OPS-04) | Responsible AI owner | Review note |
| Quarterly | Security risk register review (SBD-RSK-05); standards matrix status review | Security Authority | Minutes |
| Quarterly | Check base image and Python wheel advisories on the staging machine | Staging Engineer | Advisory note |
| Per release | Full test run, SLA table, checksum record, auditd and cron evidence | Project Lead | Gate pack |
| Annual | Disk encryption and secure-erase residual-risk check; media sanitisation records | Operator | Record |

## 2. Backup retention

PRD s4.8: keep the 7 most recent daily snapshots. The 1.0.0 cron deleted by directory age (`-mtime +7`), which can keep fewer or more than 7 snapshots if a day is missed or the clock moves. The deployment checklist now deletes all but the newest 7 by name. Verify after the first week.

## 3. Log rotation

`logs/error.log` rotates at 10 MB with 3 backups [code]. Host auditd rotation is the host's.

## 4. Upgrade and rollback

Follow [DOC-09](DOC-09-Deployment-Guide.md) s6. Keep the previous image tag until the new one has run a week. If a migration ran, rolling back the image does not undo it; restore the pre-upgrade backup first.

## 5. Model refresh

Triggers and steps are in [PRD](../../prd.md) s7.1 and [DOC-12](DOC-12-Staging-Model-Build-Guide.md). A refreshed model needs a new image, a new quality-gate record and a model-card update (JSP936-MDL-01, MDL-02).

## 6. Data retention and disposal

Telemetry stays until the learner clears it. Delete overwrites the file once and removes it. On SSDs this is not a guaranteed erase; rely on full-disk encryption (INF-LC-01).

## 7. Known gaps

No cron or auditd rule has been installed anywhere; the monthly restore test has never run; owners are CONFIRM.

## Sources

[PRD](../../prd.md) s4.8, s7; [deployment_checklist.md](deployment_checklist.md); `app.py` logging setup.
