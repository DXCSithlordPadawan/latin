---
title: Deployment Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Deployment Guide

## 1. Prerequisites

| Requirement | Specification |
|---|---|
| Host OS | Linux (RHEL 9 / Ubuntu 22.04 LTS recommended); x86-64 |
| CPU | 4-core x86-64 minimum |
| RAM | 8 GB minimum |
| Storage | 20 GB free for container image + profile databases + backups |
| Podman | ≥ 4.0, rootless mode configured |
| Network | None required at runtime (air-gapped) |
| `auditd` | Installed and running before deployment |

## 2. Physical Media Handling

Before copying the OCI tarball to transfer media:

1. **Write-protect** the USB device (hardware write-protect switch) before copying.
2. **Malware scan** the tarball on the staging machine. Record: tool name, version, timestamp, result.
3. After import on the air-gapped host, **verify SHA-256** against the release notes value.
4. After successful import and verification, **sanitise or destroy** the physical medium.

## 3. First Deployment

```bash
# 1. Verify tarball integrity (compare against release notes SHA-256)
sha256sum airgap-translator-1.0.0.tar

# 2. Import container image
podman load -i airgap-translator-1.0.0.tar

# 3. Create profile and config directories
mkdir -p ~/.airgap-translator/profiles
chmod 700 ~/.airgap-translator

# 4. Copy reference config
cp /app/config/config.toml.example ~/.airgap-translator/config.toml
chmod 600 ~/.airgap-translator/config.toml

# 5. Configure auditd (see Section 4)

# 6. Configure backup cron (see Section 5)

# 7. Run the container (rootless, no network)
podman run --rm --network=none \
  -v ~/.airgap-translator:/home/appuser/.airgap-translator:Z \
  -p 127.0.0.1:8080:8080 \
  airgap-translator:1.0.0

# 8. Copy the printed URL from stdout and open in Firefox ESR or Chromium
# Example: Ready: http://127.0.0.1:8080/?token=<hex_token>
```

## 4. auditd Configuration

Add to `/etc/audit/rules.d/airgap-translator.rules`:

```
-w /usr/bin/podman -p x -k airgap_container
-w /home/appuser/.airgap-translator/profiles/ -p wad -k airgap_profiles
-w /backups/airgap-translator/ -p wa -k airgap_backups
-w /home/appuser/.airgap-translator/session.token -p rwad -k airgap_token
-w /home/appuser/.airgap-translator/config.toml -p wa -k airgap_config
```

Reload: `augenrules --load && service auditd restart`
Verify: `auditctl -l` — all five entries must be present.

## 5. Backup Cron Registration

Add to root crontab (`crontab -e`):

```cron
# Adjust TZ= to match host timezone if not UTC
0 2 * * * TZ=UTC cp -a /home/appuser/.airgap-translator/profiles/ \
  /backups/airgap-translator/$(date +\%Y-\%m-\%d)/ && \
  find /backups/airgap-translator/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

Verify: `crontab -l` — backup entry must be present.

## 6. Upgrade Procedure

1. Confirm most recent backup is < 24 hours old. If not, run a manual backup first.
2. Stop the running container.
3. Import new image: `podman load -i airgap-translator-<new_version>.tar`
4. Verify SHA-256 against release notes before import.
5. Update launch script to reference new image tag.
6. Restart container. Confirm startup log shows no migration errors.

## 7. Rollback

1. Stop the container.
2. If schema migration was applied, restore pre-upgrade backup (see §4.8 Restore Procedure in PRD).
3. Update launch script to reference previous image tag.
4. Restart.

## 8. Secure Erase — Residual Risk Note

Secure erasure of profile databases (`shred -uz` on Linux) overwrites file data before deletion but cannot guarantee removal of all data from SSDs with wear-levelling. This residual risk is mitigated by full-disk encryption at the host OS layer. Operators are responsible for enabling FDE.
