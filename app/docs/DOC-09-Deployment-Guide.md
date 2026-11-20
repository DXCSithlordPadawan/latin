# DOC-09 Deployment Guide

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Operator with Project Lead (deputy: CONFIRM) |
| **Version** | 2.0 draft (supersedes 1.0.0 `archive-v1/DEPLOYMENT_GUIDE.md`) |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s6.2, s7, [Checklist](deployment_checklist.md), [DOC-11](DOC-11-Podman-Container-Build-Guide.md) |
| **Status** | Procedure only. **No image has been built and nothing has been deployed** |

> Nothing here has been verified against a running system. Step 6 (run line) contains an unresolved conflict, DOC-01 G-10.

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Host | 4-core x86-64, no GPU needed; Linux with Podman (rootless), auditd, cron |
| Disk | Image about 2 to 4 GB (CONFIRM), plus profiles and 7 daily backups |
| Audio | A sound device if `playback` mode is used |
| Media | Write-protected USB or write-once optical |
| Browser | Firefox ESR or Chromium on the same host |

## 2. Prepare the host (once)

1. Create the data directory with mode 700: `~/.airgap-translator/profiles/`.
2. Copy `config/config.toml.example` to `~/.airgap-translator/config.toml` and review each key.
3. Register the five auditd rules (section 5).
4. Register the backup cron entry (section 5).

## 3. Receive the image

1. Receive tarball and release notes on the write-protected medium. Receive the SHA-256 value by a **second channel** where chain of custody is weak (PRD s7 residual risk).
2. `sha256sum airgap-translator-<version>.tar`; compare. **Stop on any mismatch** and tell the Security Authority.
3. `podman load -i airgap-translator-<version>.tar`.
4. Sanitise or destroy the medium per the physical security programme.

## 4. Pre-upgrade (not first install)

Confirm the newest backup is under 24 hours old; otherwise copy `~/.airgap-translator/profiles/` to `/backups/airgap-translator/pre-upgrade/` first.

## 5. auditd and backup

Rules (host paths; adjust `<home>` to the Operator's home, never `/root` unless run as root):

```
-w /usr/bin/podman -p x -k airgap_container
-w <home>/.airgap-translator/profiles/ -p wad -k airgap_profiles
-w /backups/airgap-translator/ -p wa -k airgap_backups
-w <home>/.airgap-translator/session.token -p rwad -k airgap_token
-w <home>/.airgap-translator/config.toml -p wa -k airgap_config
```

`auditctl -l | grep airgap` must show five lines. Keep the output as evidence.

Backup cron and verification are in [deployment_checklist.md](deployment_checklist.md).

## 6. Run

PRD form (shown with the conflict marked):

```bash
podman run --rm --network=none \
  -v ~/.airgap-translator:/home/appuser/.airgap-translator:Z \
  -p 127.0.0.1:8080:8080 \        # CONFLICT: ports cannot be published to a container with no network (G-10, verify)
  airgap-translator:<version>
```

Stage 0 spike (task in the BRD): prove one working way for a host browser to reach the app while keeping the container off any external network. Candidate approaches to test, not to assume: a private internal Podman network with no outbound route and the app bound to the container interface; or a Unix socket with a host proxy. Record the winning command here and in DOC-11.

## 7. Verify

| Check | Expected |
|---|---|
| stdout | One `Ready:` line with a 32-hex-character token |
| Browser | Page loads; address bar shows no token |
| `ls -l ~/.airgap-translator` | `session.token` mode 600 while running; gone after stop |
| Health | `podman healthcheck run` exit 0 |
| SLA table | Filled in the checklist |

## 8. Stop

`podman stop` sends SIGTERM; 5-second grace; token file deleted; exit 0. Do not stop while the UI shows "Processing".

## 9. Rollback

Retag or relaunch the previous image. If a migration ran, restore the pre-upgrade backup first.

## 10. Known gaps

Run line unproven (G-10); no measured SLA; image size and `wheels/` and model directories are absent from the repo, so no image can be built yet (G-12).

## Sources

[PRD](../../prd.md) s6.2, s7; [README](../../README.md); `Containerfile`; [deployment_checklist.md](deployment_checklist.md).
