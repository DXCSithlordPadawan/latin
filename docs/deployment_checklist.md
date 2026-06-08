---
title: Deployment Checklist
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Deployment Checklist

## Pre-Deployment

- [ ] Staging machine malware scan completed; result recorded (tool, version, timestamp, result)
- [ ] OCI image tarball SHA-256 recorded in release notes
- [ ] Physical media write-protected before tarball copy
- [ ] SHA-256 verified on air-gapped host before `podman load`

## auditd Configuration

Run on air-gapped host. All 5 rules must be active.

```bash
cat >> /etc/audit/rules.d/airgap-translator.rules << 'EOF'
-w /usr/bin/podman -p x -k airgap_container
-w /home/appuser/.airgap-translator/profiles/ -p wad -k airgap_profiles
-w /backups/airgap-translator/ -p wa -k airgap_backups
-w /home/appuser/.airgap-translator/session.token -p rwad -k airgap_token
-w /home/appuser/.airgap-translator/config.toml -p wa -k airgap_config
EOF
augenrules --load && service auditd restart
```

Verification (screenshot or log excerpt required for Phase 7 gate):
```bash
auditctl -l | grep airgap
# Must return 5 entries
```
- [ ] auditd rules verified — screenshot attached

## Backup Cron Registration

```crontab
0 2 * * * TZ=UTC cp -a /home/appuser/.airgap-translator/profiles/ \
  /backups/airgap-translator/$(date +\%Y-\%m-\%d)/ && \
  find /backups/airgap-translator/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

Verification (screenshot required for Phase 7 gate):
```bash
crontab -l
# Must show backup entry
```
- [ ] Backup cron verified — screenshot attached

## SLA Verification (Phase 7 — manual, 4-core x86-64 host, no GPU)

Record all measured values below. Any value exceeding its SLA is a defect.

| Operation | SLA | Measured | Pass/Fail | Notes |
|---|---|---|---|---|
| EN→LA translation (512 tokens) | ≤ 5 s | | | |
| LA→EN translation (512 tokens) | ≤ 5 s | | | |
| PDF generation (50 pages) | ≤ 10 s | | | |
| TTS playback start (512 tokens) | ≤ 3 s | | | |
| SQLite proficiency query | ≤ 200 ms | | | |
| Container startup (ready to serve) | ≤ 30 s | | | |

Host spec: ________________  Operator: ________________  Date (UTC): ________________

## Physical Media Post-Transfer

- [ ] Physical medium sanitised (per operator physical security programme) or physically destroyed

## SIGTERM Guidance

Do not issue SIGTERM while the UI displays the "⟳ Processing…" operation status badge. The 5-second grace window may drop in-flight requests. Completed requests within the grace window are served normally.

## Secure Erase Residual Risk

`shred -uz` on Linux overwrites file data before deletion. SSDs with wear-levelling may retain data in unmapped blocks. Mitigate via full-disk encryption at the host OS layer.
