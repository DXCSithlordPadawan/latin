# DOC-05 RACI

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Project Lead (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [BRD personas](../brd/latin_personas.md), [standards matrix](standards-conformance-matrix.md) |
| **Status** | Proposed; no role is named or has accepted |

> Nothing here has been verified against a running system.

## Legend

R responsible · A accountable (exactly one per row) · C consulted · I informed. Columns: **LRN** Learner, **OPR** Operator, **STG** Staging Engineer, **PL** Project Lead, **SEC** Security Authority (independent of PL), **SUP** Support Lead, **RAI** Responsible AI owner (the JSP 936 RAISO role, proposed), **ARC** Architect.

| Activity | LRN | OPR | STG | PL | SEC | SUP | RAI | ARC |
|---|---|---|---|---|---|---|---|---|
| Corpus acquisition and filtering | I | I | R | A | C | I | C | I |
| Data provenance and licence record | I | I | R | C | C | I | A | I |
| Model fine-tuning | I | I | R | A | I | I | C | C |
| Quality gate run | I | I | R | A | C | I | C | I |
| Quality gate escalation (3 failures) | I | I | C | A/R | I | I | C | C |
| Model information package (model card) | I | I | R | C | I | I | A | C |
| Bias and out-of-design checks | I | I | R | C | I | I | A | C |
| OCI image build | I | I | R | A | C | I | I | C |
| Checksum recording | I | I | R | A | C | I | I | I |
| Malware scan and media write-protect | I | R | C | A | C | I | I | I |
| Host deployment | I | R | I | A | C | C | I | C |
| auditd rules and cron registration | I | R | I | A | C | C | I | I |
| Day-to-day use | R | C | I | I | I | C | I | I |
| Profile management | R | C | I | I | I | C | I | I |
| Backup verification | I | R | I | A | I | C | I | I |
| Log review | I | R | I | A | C | C | I | I |
| Container upgrade | I | R | C | A | C | C | I | C |
| Model refresh decision | I | I | C | A/R | I | I | C | C |
| Security risk register and quarterly review | I | C | C | R | A | I | C | C |
| Compliance gate sign-off | I | C | C | R | A | C | C | C |
| Document baseline approval | I | C | C | A | R | C | C | R |
| Incident escalation | I | R | C | A | C | R | I | I |

Exactly one A per row except rows marked A/R where the same role holds both.

## Competence (SBD-PLN-06, JSP936-GOV)

Names, qualifications and deputies are **CONFIRM** for every role. No appointment record exists (SBD-GOV-01, JSP936-GOV-01).

## Sources

Role set from the 1.0.0 RACI and RBAC (`archive-v1/`); SbD and JSP 936 role requirements in `aip/standards`.
