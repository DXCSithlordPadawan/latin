# DOC-07 Security Analysis and Compliance

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Security Authority (deputy: CONFIRM) |
| **Version** | 2.0 draft (supersedes 1.0.0 Baseline in `archive-v1/SECURITY_COMPLIANCE.md`) |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s6, [Standards matrix](standards-conformance-matrix.md), [DOC-01](DOC-01-Architecture-Guide.md) s9 |
| **Status** | Design-time analysis only |

> **This is a design-time analysis, not a penetration test, audit or accreditation.** Every row is **Planned** until it becomes **Evidenced** by a dated file. No claim of FIPS, STIG, CIS or NIST compliance is made. The 1.0.0 document stated these as met; the manifest, quality gate, SLA run and sign-off are all still pending (progress.md).

## 1. Assets and data

| Asset | Sensitivity | Why it matters |
|---|---|---|
| Session token and cookie | High | Whole-UI access |
| Profile databases | Personal (learner names, usage history; children possible) | Privacy, JSP 441 |
| Fine-tuned checkpoint and corpora | Internal | Integrity of translations; poisoning target |
| OCI tarball and release notes | High | Supply chain |
| Config file | Medium | Port, timeout, TTS mode |
| Error log | Low | Truncated user strings |
| Backups | Personal | Same as profile DBs |

## 2. Threat model (STRIDE)

| Threat | Example | Existing control | Gap or plan |
|---|---|---|---|
| Spoofing | Second browser reuses the startup URL | Token and cookie | **G-01**: token re-accepted. Fix: clear token after first use |
| Tampering | Modified checkpoint or font | SHA-256 manifest | **G-02, G-03**: startup check is a stub; build only warns; manifest empty |
| Tampering | Poisoned corpus | Pinned hashes (planned) | Add corpus review and per-source counts (JSP936-QSS-04) |
| Repudiation | "I did not delete that profile" | auditd watch on profile directory | Needs host rule evidence; no in-app log of deletes |
| Information disclosure | Token in logs, history, Referer | 302 strip | Suppress query in access log; add no-referrer header (DOC-03 s4) |
| Information disclosure | Learner data in backup | Mode 700 | Host disk encryption is the operator's duty (PRD s4.5a) |
| Denial of service | Many requests | Single user, loopback | Accepted |
| Elevation of privilege | Path traversal through `slug` | Regex-derived slug on create | **G-07**: delete does not validate |
| CSRF | Page in the same browser posts to the port | None | **G-08** |
| Supply chain | Unpinned pip fallback | None | **G-03** |
| AI-specific | Out-of-design input; wrong Latin presented as right | Sanitiser, 512 cap, fallback marks | G-11: marks unreliable; add "machine translation" label |

## 3. Control mapping named in the PRD

### 3.1 FIPS 140-3 (PRD s6.1)

| Operation | Mechanism | Status | Gap |
|---|---|---|---|
| SHA-256 at build | `hashlib` on OpenSSL FIPS provider | Planned | G-03: assertion prints the version only; the commented line uses `openssl fips-mode-set`, which is OpenSSL 1.x style (CONFIRM for 3.x) |
| SHA-256 at startup | same | Planned | G-02 |
| Token | `secrets.token_hex(16)` | Partly built | Evidenced by code; FIPS validity of the OS CSPRNG is a host claim |
| Cookie signing | Flask `itsdangerous` | Planned | Default digest is SHA-1 in itsdangerous; PRD says HMAC-SHA-256 (CONFIRM and configure) |

Exclusions stand: inference, SQLite, PDF are not cryptographic.

### 3.2 NIST SP 800-53

| Control | Implementation | Status |
|---|---|---|
| AC-3 | UID 10001, directory 700, token file 600 | Partly built |
| AC-17 | Loopback only | Planned (G-10 may stop it working at all) |
| AU-2, AU-9 | Host auditd five watch rules | Planned; paths differ between documents (fixed in the checklist, 2026-11-20) |
| CM-7 | `--network=none`, no CDN | Planned |
| IA-5 | 128-bit token, deleted on shutdown | Partly built (G-01) |
| SI-3 | Malware scan on staging | Planned |
| SI-10 | Sanitiser and 512 cap | Partly built; 512 cap counts whitespace words, not mT5 tokens |
| SR-3, SR-4 | Supply chain, provenance | Planned |

### 3.3 OWASP Top 10

| Risk | Mitigation | Status |
|---|---|---|
| A01 Broken access control | Single session | Partly built (G-01, G-07) |
| A02 Cryptographic failures | See 3.1 | Planned |
| A03 Injection | Sanitiser; parameterised SQL | Partly built; update helper builds column names from an allow-list |
| A04 Insecure design | Air-gap design | Planned; G-10 |
| A05 Misconfiguration | Config validation; no security headers | Partly built |
| A06 Vulnerable components | Pinned wheels | Planned; G-03 |
| A07 Authentication failures | Token, idle timeout | Partly built |
| A08 Software and data integrity | Manifest | Planned; G-02, G-03 |
| A09 Logging and monitoring | UTC log, truncation | Partly built; access log of token URL not suppressed |
| A10 SSRF | No outbound calls | Planned |

### 3.4 CIS Level 2 and DISA STIG

| Item | Status | Note |
|---|---|---|
| Non-root service | Partly built | UID 10001 in Containerfile |
| Minimal packages | Partly built | Includes `libssl-dev` and `python3-pip` at runtime; trim in a multi-stage build |
| Audit logging | Planned | Five rules; verify with `auditctl -l` |
| Network filtering | Planned | `--network=none` |
| HEALTHCHECK | Partly built | Fixed port 8080 |

### 3.5 Language guides

See [standards matrix](standards-conformance-matrix.md) s5.

## 4. Standards conformance

Secure by Design, JSP 936 and JSP 441 rows are in the [standards matrix](standards-conformance-matrix.md). Status counts there are the authoritative figure; none is Evidenced.

## 5. Risk register (first draft)

| ID | Risk | Owner | Rating | Treatment | Review |
|---|---|---|---|---|---|
| R1 | Session takeover by token reuse (G-01) | PL | Medium (fixed in code 2026-11-20; UAT-05 in container Not run) | Run UAT-05 | Quarterly |
| R2 | Unverified model or font loaded (G-02, G-03) | STG | Medium (startup check done; build-side G-03 open) | Fail the build | Quarterly |
| R3 | Unpinned install at build (G-03) | STG | Medium (fallback removed 2026-11-20; hashes not yet generated) | Generate hashes | Quarterly |
| R4 | UI unreachable in the stated run mode (G-10) | ARC | High | Stage 0 spike | Before gate |
| R5 | Misleading fallback marks (G-11) | ARC | Medium (unloaded case fixed; model-score confidence open) | Real confidence; label | Before gate |
| R6 | Profile deletion path traversal (G-07) | PL | Low (fixed in code 2026-11-20) | Keep test | Quarterly |
| R7 | CSRF (G-08) | PL | Low (fixed in code 2026-11-20) | Run UAT-29 in container | Quarterly |
| R8 | Biased or poisoned corpus | RAI | Medium | Bias report; hash pin | Each model refresh |
| R9 | Residual data on SSD after erase | OPR | Low | Disk encryption | Annual |
| R10 | Checksum value substituted in transit | OPR | Medium | Second channel; consider signing (accepted in PRD s7) | Each release |

Owners are CONFIRM; none has accepted.

## 6. Evidence pack (target at the compliance gate)

`auditctl -l` output; `crontab -l` output; JUnit XML from the container run; checksum record; quality-gate record; SLA table; signed risk register; model card; ODD; this matrix with each row's evidence file.

## Verification notes and gaps

Code paths cited were read on 2026-11-20. JavaScript, Bash, `pdf_factory.py` and the TTS export path were not reviewed in depth. Flask and itsdangerous behaviour is from general knowledge and is CONFIRM against the pinned versions.

## Sources

[PRD](../../prd.md) s6, s9.8; `app.py`; `Containerfile`; `engine/db_migrate.py`; `engine/profile_manager.py`; the standards in `aip/standards` as listed in the matrix.
