---
title: Security & Compliance
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Security & Compliance

## 1. FIPS 140-3 Compliance Matrix

| Operation | Where Used | Algorithm | FIPS-Validated Module |
|---|---|---|---|
| Artifact integrity verification (build time) | `corpus_manifest.lock` SHA-256 checks during OCI image build | SHA-256 | Python `hashlib` via OpenSSL FIPS provider (OpenSSL ≥ 3.0) |
| Artifact integrity verification (startup) | Checkpoint and font file SHA-256 re-verification | SHA-256 | Python `hashlib` via OpenSSL FIPS provider |
| Session token generation | `session.token` written at startup (128-bit entropy) | CSPRNG → hex | Python `secrets.token_hex()` backed by OS CSPRNG (`/dev/urandom`) |
| Session cookie integrity | HTTP session cookie signing by Flask | HMAC-SHA-256 | Python `hmac` via OpenSSL FIPS provider |
| Backup integrity (optional) | Manual post-backup checksum | SHA-256 | Host `sha256sum` (outside container scope) |

**Exclusions:** Neural inference (mT5-small), SQLite storage, and PDF rendering do not use cryptographic primitives and are outside FIPS scope.

## 2. NIST SP 800-53 Controls

| Control | Implementation |
|---|---|
| AC-3 Access Enforcement | Rootless UID 10001; profile dir permissions 700; session token 600 |
| AC-17 Remote Access | No remote access; server binds to 127.0.0.1 only |
| AU-2 Audit Events | Delegated to host `auditd` (5 required watch rules — see §6.2) |
| AU-9 Protection of Audit Information | auditd log integrity is the host operator's responsibility |
| CM-7 Least Functionality | `--network=none`; no external services; no dynamic imports at runtime |
| IA-5 Authenticator Management | 128-bit CSPRNG token; deleted on shutdown; no reuse across restarts |
| SC-8 Transmission Confidentiality | Loopback only; no TLS required (no network exposure) |
| SI-3 Malicious Code Protection | Malware scan of OCI tarball on staging machine before transfer |
| SI-10 Information Input Validation | Sanitiser strips null bytes, control chars, shell metacharacters; 512-token hard cap |

## 3. OWASP Top 10 Protections

| Risk | Mitigation |
|---|---|
| A01 Broken Access Control | Single-session loopback token auth; HTTP 409 on concurrent session |
| A02 Cryptographic Failures | HMAC-SHA-256 session cookies; SHA-256 artifact integrity; CSPRNG tokens |
| A03 Injection | Input sanitiser strips null bytes / control chars / shell metacharacters; CSV formula stripping |
| A04 Insecure Design | Air-gap design; no external dependencies at runtime |
| A05 Security Misconfiguration | Config validation at startup; invalid values reset to safe defaults with WARN log |
| A06 Vulnerable Components | All dependencies pinned and bundled in container; no runtime downloads |
| A07 Auth Failures | Token deleted on shutdown; idle timeout; single concurrent session |
| A08 Software Integrity | SHA-256 checksums in `corpus_manifest.lock`; verified at build time and startup |
| A09 Logging Failures | Rotating error log (10 MB × 3); UTC ISO 8601 timestamps; user strings truncated to 64 chars |
| A10 SSRF | No outbound network connections; `--network=none` enforced |

## 4. CIS Benchmark Level 2

| CIS Control | Implementation |
|---|---|
| 1.1 OS Patching | Base image Ubuntu 22.04 LTS; patched before OCI image build |
| 4.1 Non-root Services | Container runs as UID 10001 (non-root) |
| 5.1 Minimal Software | Only required packages installed; no development tools in production image |
| 6.1 Audit Logging | Host auditd; 5 required rules (see §6.2 of PRD) |
| 9.1 Network Filtering | `--network=none`; loopback-only binding |

## 5. DISA STIG Required auditd Rules

The following host-level audit rules must be active before the Phase 7 compliance gate.
Register them in `/etc/audit/rules.d/airgap-translator.rules`:

```
-w /usr/bin/podman -p x -k airgap_container
-w /root/.airgap-translator/profiles/ -p wad -k airgap_profiles
-w /backups/airgap-translator/ -p wa -k airgap_backups
-w /root/.airgap-translator/session.token -p rwad -k airgap_token
-w /root/.airgap-translator/config.toml -p wa -k airgap_config
```

Verify with: `auditctl -l` — all five entries must be present.
