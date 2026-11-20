---
title: Documentation Index
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Documentation Index

Master register of all project documents. All documents located under `docs/` unless noted.

| # | Document | Filename | Version | Status | Description |
|---|---|---|---|---|---|
| 1 | Documentation Index | `DOCUMENTATION_INDEX.md` | 1.0.0 | Baseline | This file — authoritative register of all document status |
| 2 | Architecture Guide | `ARCHITECTURE_GUIDE.md` | 1.0.0 | Baseline | System architecture, component descriptions, data flows, Mermaid diagrams |
| 3 | RBAC | `RBAC.md` | 1.0.0 | Baseline | Role definitions, permission matrix, access control policy |
| 4 | RACI | `RACI.md` | 1.0.0 | Baseline | Responsibility assignment matrix for all project roles and activities |
| 5 | Security & Compliance | `SECURITY_COMPLIANCE.md` | 1.0.0 | Baseline | NIST SP 800-53, OWASP Top 10, CIS Benchmark Level 2, DISA STIG, FIPS 140-3 mapping |
| 6 | Deployment Guide | `DEPLOYMENT_GUIDE.md` | 1.0.0 | Baseline | Step-by-step air-gapped host deployment including auditd and backup cron |
| 7 | User Guide | `USER_GUIDE.md` | 1.0.0 | Baseline | End-user guide covering all application features |
| 8 | UI Guide | `UI_GUIDE.md` | 1.0.0 | Baseline | Interface reference: pages, controls, navigation, WCAG notes |
| 9 | API Guide | `API_GUIDE.md` | 1.0.0 | Baseline | Endpoint reference: request/response formats, error codes, authentication |
| 10 | Support Guide | `SUPPORT_TASKS.md` | 1.0.0 | Baseline | Support runbook: diagnostics, fault resolution, escalation |
| 11 | Maintenance Guide | `MAINTENANCE_GUIDE.md` | 1.0.0 | Baseline | Scheduled maintenance procedures (daily/weekly/monthly/quarterly) |
| 12 | Container Build Guide | `CONTAINER_BUILD_GUIDE.md` | 1.0.0 | Baseline | OCI image build, FIPS assertion, SHA-256 verification, image tagging |

### Supporting Technical Documents

| Document | Filename | Description |
|---|---|---|
| Fine-Tuning Procedure | `finetuning_procedure.md` | Corpus filtering records, training procedure, quality gate log |
| FIPS Verification | `fips_verification.md` | OpenSSL FIPS provider build assertion procedure |
| Deployment Checklist | `deployment_checklist.md` | auditd rules, backup cron, media handling, SLA verification |
| Architecture Detail | `architecture.md` | Extended component-level architecture notes |
| Adaptive Learning Schema | `adaptive_learning_schema.md` | Full SQLite schema documentation |
| Input Sanitisation Policy | `input_sanitization_policy.md` | Sanitisation rules, token cap, CSV policy |
| Test Results | `test_results/results.xml` | JUnit XML report — Phase 7 compliance run |
