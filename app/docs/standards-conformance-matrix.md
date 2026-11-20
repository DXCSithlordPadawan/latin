# Standards Conformance Matrix

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Security Authority (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [AIP standards library](../../../aip/standards/README.md), [DOC-07](DOC-07-Security-Analysis-and-Compliance.md) |
| **Status** | Design-time mapping. Every row is **Planned** until a dated file makes it **Evidenced**. No claim of compliance, accreditation or assurance is made |

> The standards are internal engineering summaries (AIP library, November 2026), not the controlled documents. JSP 936 and Secure by Design apply to a **MOD capability or supplier**. Nothing in this repository says this tool is one, so each row is applied as **voluntary good practice** (OD-S1). If it becomes a MOD deliverable, the rows become obligations and the Medium and Low confidence standards must be re-read from controlled text.

## 1. Which standards apply

Using the decision flow in the standards README:

| Standard | Applies? | Reason | Confidence of source |
|---|---|---|---|
| Python, JavaScript, ANSI SQL, Bash security guides | **Yes** | Code in `app.py`, `engine/`, `scripts/`, `static/js/main.js`, SQLite, `fetch_corpus.sh` | Guides |
| NIST SP 800-53, OWASP Top 10, CIS L2, DISA STIG, FIPS 140-3 | **Yes** (PRD s6) | Stated in the PRD | PRD |
| Secure by Design (ISN 2023/09) | **Voluntary** | Principles are sound for any air-gapped tool | High |
| JSP 936 Dependable AI | **Voluntary** | The mT5 model is AI; the use is educational, not defence capability | High |
| JSP 441 Information and data management | **Voluntary** | Learner data and corpus provenance | Medium |
| Def Stan 05-138, JSP 440 or 604 | **No** | No MOD contract or network connection stated | n/a |
| FedRAMP | **No** | Not a cloud service | n/a |
| Def Stan 00-055, 00-056 | **No** | No safety function | n/a |
| JSP 939, DMSP 03-050 | **No** | Not a model or simulation of a defence system | n/a |

Open decision **OD-S1**: confirm whether the tool is ever delivered to the MOD. Until then all "Voluntary" rows are good practice.

## 2. Secure by Design (SBD)

Status words: Planned, Partly built, Evidenced, N/A. "Partly built" means code or a document exists but no dated evidence file does.

| ID | Requirement (short) | Status | What exists | What would evidence it |
|---|---|---|---|---|
| SBD-GOV-01 | SRO appointed | Planned | No appointment | Appointment record |
| SBD-GOV-03 | Risk appetite published | Planned | None | Risk appetite statement |
| SBD-CTX-01 | Context, purpose, mode of operation | Partly built | PRD s3, DOC-01 s1 | Reviewed context document |
| SBD-CTX-02 | Initial cyber risk assessment | Partly built | [DOC-07](DOC-07-Security-Analysis-and-Compliance.md) STRIDE | Reviewed assessment |
| SBD-PLN-02 | Security activities and testing approach | Partly built | DOC-13, DOC-14 | Signed security plan |
| SBD-PLN-04 | Risks in a register | Partly built | DOC-07 s5 | Register with owners |
| SBD-PLN-05 | Handover pack | Planned | DOC suite | Pack delivered to Operator |
| SBD-PLN-06 | Staff qualified | Planned | Roles in DOC-05 | Competence records |
| SBD-RSK-01 | Risk managed through life | Planned | DOC-08 quarterly review | Review minutes |
| SBD-RSK-03 | Owner per risk, controls | Partly built | DOC-07 s5 (owners CONFIRM) | Register with named owners |
| SBD-RSK-05 | Review at least quarterly | Planned | DOC-08 | First review minutes |
| SBD-CTL-01 | NCSC good design, approved patterns | Partly built | Loopback, no network, least privilege | Design record |
| SBD-CTL-02 | Compromise hard, detection easy, impact small | Partly built | `--network=none`, auditd rules, rootless | Test results |
| SBD-CTL-03 | Controls proportionate | Partly built | DOC-07 | Control justification |
| SBD-SUP-01 | Supply chain in procurement | Partly built | Licence table, SHA-256 manifest (all PENDING) | Filled manifest, SBOM |
| SBD-ASR-01 | Mitigated before data used | Planned | Phase 7 gate | Gate pack |
| SBD-ASR-02 | V&V at design points | Planned | DOC-13, DOC-14 | V&V records |
| SBD-ASR-03 | Acceptance tests cover security | Partly built | Auth, sanitiser, migration tests (176 pass on 2026-11-20, Python 3.12, Windows) | Run in container on target |
| SBD-ASR-04 | Non-conformances closed | Planned | DOC-01 s9 list G-01 to G-14 | Closed defect log |
| SBD-ASR-05 | Findings shared with assessors | Planned | None | Findings log |
| SBD-ASR-06 | Repeatable security testing | Partly built | pytest | CI or scripted gate (OD-07) |
| SBD-TLM-01 | Through-life plan | Partly built | DOC-08 | Approved plan |
| SBD-TLM-02 | Reassessment on change | Planned | DOC-04 s5 records | Reassessment records |
| SBD-GOV-02, 04, 05, 06; SBD-CTX-03; SBD-PLN-01, 03; SBD-RSK-02, 04; SBD-SUP-02 | Programme and contract items | N/A until OD-S1 closes | | |

## 3. JSP 936 Dependable AI

| ID | Requirement (short) | Status | What exists | What would evidence it |
|---|---|---|---|---|
| JSP936-GOV-01 | Named RAISO per AI project | Planned | "Responsible AI owner" role in DOC-05 | Named appointment |
| JSP936-RSK-01 | Ethical risk assessment at outset and on change | Planned | None | Assessment and change log |
| JSP936-RSK-06 | Rationale for AI over other technology | Planned | PRD s4.1 states mT5 is the backbone | Decision record |
| JSP936-ETH-01 | Who is affected; impact per group | Planned | Learners, including children (levels 1 to 3) | Impact assessment |
| JSP936-ETH-02 | Human involvement and accountability | Planned | User chooses direction and level | Responsibility statement |
| JSP936-ETH-04 | Bias in data and model | Planned | Corpus filtering rules (PRD s4.2a) | Bias report on the corpus (Christian text from the Vulgate; period filter) |
| JSP936-ETH-05 | Redress where wellbeing affected | Planned | Thumbs rating only | Redress route |
| JSP936-REL-01 | Operating context (ODD) | Planned | PRD s4.1, s4.2 imply it | ODD document: languages, register, token cap, levels |
| JSP936-REL-02 | Performance targets shown | Planned | Spot-check 40/50 and chrF >= 45 defined | Gate results (none yet) |
| JSP936-REL-03 | Response to out-of-design inputs | Partly built | 512 cap, sanitiser, fallback marks | Robustness tests |
| JSP936-REL-04 | Threat analysis incl. supply chain, data | Partly built | DOC-07 STRIDE | Added ML-specific threats (poisoned corpus) |
| JSP936-REL-05 | Failure modes and residual risk | Partly built | DOC-07 | FMEA-style table |
| JSP936-LCY-04 | Architecture traceable to failure modes | Partly built | DOC-01 | Traceability |
| JSP936-LCY-05 | Justify frameworks and libraries | Planned | `requirements-staging.txt` | Selection record |
| JSP936-DAT-01 | Separate training, test and verification data | Partly built | spot_check.tsv, validation_split.tsv | Dataset register, no overlap proof |
| JSP936-DAT-02 | Provenance recorded | Partly built | Licence table | Manifest filled; per-source counts |
| JSP936-DAT-03 | Data under configuration management | Partly built | `corpus_manifest.lock` | Filled manifest |
| JSP936-MDL-01 | Model information package | Planned | None | Model card (assumptions, weaknesses, ODD) |
| JSP936-MDL-02 | Risk owner satisfied before re-use or retrain | Planned | Escalation rule in PRD s4.2a | Sign-off |
| JSP936-VV-01 | V&V across the ODD | Planned | Quality gate | Per-level results |
| JSP936-VV-02 | Regression on update | Planned | Model refresh steps (PRD s7.1) | Regression results |
| JSP936-OPS-04 | Monitor against ODD | Partly built | Fallback and feedback data | Monitoring review in DOC-08 |
| JSP936-OPS-05 | Controlled change for modifiable AI | Partly built | No runtime training; adaptive layer does not retrain weights | Statement in model card |
| JSP936-HMT-03 | Label AI-based output | Planned | `[FALLBACK:]` marks only | UI label "machine translation" (DOC-10) |
| JSP936-QSS-04 | Secure by Design, data poisoning | Planned | Hash-pinned corpus | Poisoning section in DOC-07 |
| JSP936-SUP-02, SUP-03 | Third-party components and provenance | Partly built | Licence table | Entries with source and hash |
| JSP936-AST-01 | Assurance includes ODD excursions | Planned | None | Assurance case |
| JSP936-TLR-01 | Record tailoring where a requirement is not met | Partly built | This matrix | Signed tailoring record |
| Other JSP936 rows | Governance, annual statement, DAU referral, safety, HFI | N/A until OD-S1 closes | | |

## 4. JSP 441 information and data management

| ID | Requirement (short) | Status | Notes |
|---|---|---|---|
| INF-GOV-02 | Named owner per information asset | Planned | Assets: profile DBs, corpus, checkpoint |
| INF-LC-01 | Manage through life incl. disposal | Partly built | Secure erase on delete; SSD residual risk documented |
| INF-QUA-01 | Information quality measured | Partly built | chrF gate |
| INF-PRV-01 | Privacy | Partly built | Learner names stored; PRD says truncation for logs; no privacy impact record |
| INF-RSK-01 | Risks to information and tools | Partly built | DOC-07 |
| INF-MET-01 | MOD metadata attributes | N/A until OD-S1 closes | |

## 5. Language and platform guides

Section numbers are those of the guides in `aip/standards`.

| Guide | Applies to | Checked areas | Status |
|---|---|---|---|
| Python s1, s2 (Flask), s5 checklist | `app.py`, `engine/*.py`, `scripts/*.py` | Input validation, secrets and tokens, subprocess use (`shred` call uses a list, no shell), logging, cookie flags, CSRF, security headers, pinned dependencies | Partly built; CSRF, headers and pinning are open (G-08, DOC-03 s4, G-03) |
| ANSI SQL s3, s8, s9, s13 | `engine/migrations/001.sql`, `profile_manager.py`, `app.py` | Parameterised queries (yes in code read); dynamic SQL in `update_profile_meta` builds column names from an allow-list; error disclosure; sensitive data | Partly built |
| JavaScript s2, s4, s7 | `static/js/main.js`, templates | DOM sinks, CSP, no CDN | Not reviewed: only the file size is known; Planned |
| Bash s3 to s6, s9 | `scripts/fetch_corpus.sh`, Containerfile steps | Quoting, injection, temp files, ShellCheck | Not reviewed; Planned |
| NIST 800-53, OWASP Top 10, CIS L2, DISA STIG, FIPS 140-3 | Whole product | Mapped in DOC-07 s3 | Planned |

## 6. Open decisions

| ID | Question | Effect |
|---|---|---|
| OD-S1 | Is the tool ever a MOD deliverable or used by a MOD supplier? | Makes the Voluntary rows into obligations and brings in Def Stan 05-138 |
| OD-S2 | Who is the Responsible AI owner and the SRO? | JSP936-GOV-01, SBD-GOV-01 |
| OD-S3 | Is the learner age range (2 to 4) acceptable for an AI translator without adult supervision? | Ethics rows ETH-01 and ETH-05 |

## Verification notes and gaps

Standards read from the AIP summaries only; JSP 440, 901, 906, 920 and the Def Stan 00-055 and 00-056 text were not read by the library. Confidence by document is in the standards README. Row status was set by reading code, not by running controls in a container.

## References

[Standards library README](../../../aip/standards/README.md); [Secure_by_Design_Standard.md](../../../aip/standards/Secure_by_Design_Standard.md); [JSP936_Dependable_AI_Standard.md](../../../aip/standards/JSP936_Dependable_AI_Standard.md); [JSP441_Information_Data_Management_Standard.md](../../../aip/standards/JSP441_Information_Data_Management_Standard.md); language guides in the same folder.
