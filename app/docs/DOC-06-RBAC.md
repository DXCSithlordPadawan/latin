# DOC-06 RBAC

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Security Authority (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [DOC-05](DOC-05-RACI.md), [DOC-07](DOC-07-Security-Analysis-and-Compliance.md) |
| **Status** | Design. The application has **no user accounts**; separation comes from the OS and the process |

> Nothing here has been verified against a running system.

## 1. Where access is enforced

| Layer | Mechanism | Evidence |
|---|---|---|
| Host | Operator account runs Podman rootless; physical access controls | Operator's programme (not in this repo) |
| Container | UID 10001, group 0 [Containerfile] | Planned: show `podman top` output |
| Files | Profile directory 700, profile file 600, token 600 [code] | Planned: `ls -l` capture |
| Application | One token, one session cookie, one active session [code, with G-01] | UAT-05, UAT-06 |
| Profiles | Convention only: every learner shares the container UID and the one session | By design (PRD s4.5a) |

## 2. Roles

| Role | Description |
|---|---|
| Operator | Deploys, configures, backs up, restores |
| Learner | Uses the web UI inside the one session |
| Staging Engineer | Runs corpus fetch, fine-tune, quality gate, image build on the connected staging machine; no access to the air-gapped host |
| Project Lead | Approves baselines and re-training |
| Security Authority | Independent reviewer; owns the risk register and compliance sign-off |
| Support Lead | Diagnoses and escalates; no change rights beyond the Operator's runbook |
| Responsible AI owner | Accountable for the model information package and AI risk decisions |

## 3. Permission matrix

| Action | OPR | LRN | STG | PL | SEC | SUP | RAI |
|---|---|---|---|---|---|---|---|
| Load OCI image, run container | Y | N | N | N | N | N | N |
| Edit `config.toml` | Y | N | N | N | N | N | N |
| Register auditd rules and cron | Y | N | N | N | N | N | N |
| Use web UI | Y | Y | N | Y | N | N | N |
| Create profile | Y | Y | N | Y | N | N | N |
| Delete profile | Y | Y (own, convention) | N | Y | N | N | N |
| Clear telemetry | Y | Y (own) | N | Y | N | N | N |
| Read backups | Y | N | N | N | N | Y | N |
| Run fetch, fine-tune, quality gate | N | N | Y | Y | N | N | N |
| Edit `corpus_manifest.lock` | N | N | Y | Y | C | N | N |
| Approve baseline documents | N | N | N | Y | Y | N | N |
| Accept AI risk and model release | N | N | N | C | C | N | Y |
| Review risk register | N | N | N | C | Y | N | N |

Y allowed · N not allowed · C consulted.

## 4. Known weaknesses

1. A Learner can delete any profile, not only their own, because there is no per-profile login. The "own only" rule is convention (PRD s4.5a, sequential use).
2. `/profile/delete` does not check that the slug is a known profile (DOC-01 G-07).
3. Anyone with the host account that runs Podman can read the profile files; protection is the host account, not the app.
4. The `Ready:` line contains the secret; whoever can read the terminal or `podman logs` can take the session (G-01).

## Sources

1.0.0 RBAC (`archive-v1/RBAC.md`); `app.py`; `profile_manager.py`; Secure by Design roles (SBD-GOV, SBD-PLN) in `aip/standards`.
