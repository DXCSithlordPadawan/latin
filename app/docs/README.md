# Solution Documents (DOC-01 to DOC-15)

**Author:** Iain Reid · **Classification:** INTERNAL · **Version:** 2.0 draft · **Date:** 2026-11-20

Index of the solution documentation suite. It replaces the 1.0.0 set (marked Baseline on 2026-06-08), which is kept unchanged in [archive-v1/](archive-v1/) for comparison. The suite follows the layout of the AIP pcn005 document set and the standards in `aip/standards`.

> Nothing here has been verified against a running system or a built container. The only executed check is the unit suite (176 passed on 2026-11-20, Python 3.12.9, Windows). Controls are **Planned** until a dated file makes them **Evidenced**.

| DOC | Document | Owner | State |
|---|---|---|---|
| 01 | [Architecture Guide](DOC-01-Architecture-Guide.md) (includes gap list G-01 to G-14) | Architect | Draft 2.0 |
| 02 | [User Guide (Learner)](DOC-02-User-Guide.md) | Support Lead | Draft 2.0 |
| 03 | [API and Interface Guide](DOC-03-API-and-Interface-Guide.md) | Architect | Draft 2.0 |
| 04 | [Support Tasks](DOC-04-Support-Tasks.md) | Support Lead | Draft 2.0 |
| 05 | [RACI](DOC-05-RACI.md) | Project Lead | Draft 2.0; no role named |
| 06 | [RBAC](DOC-06-RBAC.md) | Security Authority | Draft 2.0 |
| 07 | [Security Analysis and Compliance](DOC-07-Security-Analysis-and-Compliance.md) | Security Authority | Draft 2.0 |
| 08 | [Maintenance Guide](DOC-08-Maintenance-Guide.md) | Support Lead | Draft 2.0 |
| 09 | [Deployment Guide](DOC-09-Deployment-Guide.md) | Operator | Draft 2.0; run line unresolved |
| 10 | [User Interface Guide](DOC-10-User-Interface-Guide.md) | Architect | Draft 2.0 |
| 11 | [Podman Container Build Guide](DOC-11-Podman-Container-Build-Guide.md) | Staging Engineer | Draft 2.0; findings |
| 12 | [Staging Machine and Model Build Guide](DOC-12-Staging-Model-Build-Guide.md) | Staging Engineer | Draft 2.0 |
| 13 | [User Acceptance Tests](DOC-13-User-Acceptance-Tests.md) | Project Lead | 30 cases, all Not run |
| 14 | [EAIT](DOC-14-EAIT.md) | Architect | Layer 1 built |
| 15 | [Artifact Collection Guide](DOC-15-Artifact-Collection-Guide.md) | Staging Engineer | Draft 2.0 |
| — | [Standards conformance matrix](standards-conformance-matrix.md) | Security Authority | Draft 2.0 |
| — | [Component register](component-register.md) and [12 component documents](components/README.md) | Architect | Generated |

## Supporting technical documents (kept from 1.0.0, status reset to Draft)

[adaptive_learning_schema.md](adaptive_learning_schema.md) · [input_sanitization_policy.md](input_sanitization_policy.md) · [finetuning_procedure.md](finetuning_procedure.md) (build record template) · [fips_verification.md](fips_verification.md) · [deployment_checklist.md](deployment_checklist.md) · `test_results/results.xml` (JUnit XML dated 2026-06-08) · `latin.json` (79 KB, purpose unknown, G-14)

## Mapping to the PRD s10 document list

| PRD s10 name | Now |
|---|---|
| DOCUMENTATION_INDEX | This file |
| ARCHITECTURE_GUIDE | DOC-01 |
| RBAC, RACI | DOC-06, DOC-05 |
| SECURITY_COMPLIANCE | DOC-07 and the standards matrix |
| DEPLOYMENT_GUIDE | DOC-09 |
| USER_GUIDE, UI_GUIDE, API_GUIDE | DOC-02, DOC-10, DOC-03 |
| SUPPORT_TASKS, MAINTENANCE_GUIDE | DOC-04, DOC-08 |
| CONTAINER_BUILD_GUIDE | DOC-11 |
| (new) | DOC-12 staging and model build, DOC-13 UAT, DOC-14 EAIT, DOC-15 artifact collection |

## Deviations from the reference set

- DOC-12 is the staging machine and model build, not an LXC or VM template guide; there is no template.
- The reference set's EAIT is mostly specified-only; here Layer 1 exists as the pytest suite.
- File names `DOC-nn-...` replace the upper-case names of 1.0.0; PRD s10 is updated to match.
- Status words are Draft, Review, Approved, Baseline (PRD s10) for documents, and Planned, Partly built, Evidenced, N/A for controls.

## Known gaps across the suite

No role is named; ports, sizes and times beyond the PRD are CONFIRM; no image, checkpoint or deployment exists; JavaScript, Bash and PDF code were not reviewed in depth; Mermaid is not rendered in a viewer.

## Sources

[PRD](../../prd.md); [progress](../../progress.md); `aip/standards` library; the pcn005 document set layout.
