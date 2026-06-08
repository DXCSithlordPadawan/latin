---
title: RBAC — Role-Based Access Control
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# RBAC

## 1. Role Definitions

| Role | Description |
|---|---|
| **Operator** | Deploys and maintains the container on the air-gapped host. Responsible for auditd rules, backup cron, and physical media handling. |
| **Learner** | End user of the application. Creates and manages their own profile; uses translation, TTS, and PDF features. |
| **Staging Engineer** | Operates the network-connected staging machine for corpus fetch and model fine-tuning. No access to air-gapped host at runtime. |
| **Project Lead** | Approves baseline documentation; authorises re-training after quality gate failures; reviews compliance gate. |

## 2. Permission Matrix

| Action | Operator | Learner | Staging Engineer | Project Lead |
|---|---|---|---|---|
| Deploy OCI image to air-gapped host | ✅ | ❌ | ❌ | ✅ |
| Configure `config.toml` | ✅ | ❌ | ❌ | ✅ |
| Register auditd rules | ✅ | ❌ | ❌ | ✅ |
| Configure backup cron | ✅ | ❌ | ❌ | ✅ |
| Access web UI (translation, TTS, PDF) | ✅ | ✅ | ❌ | ✅ |
| Create / delete profiles | ✅ | ✅ (own only) | ❌ | ✅ |
| Clear telemetry | ✅ | ✅ (own profile) | ❌ | ✅ |
| Run corpus fetch + fine-tuning | ❌ | ❌ | ✅ | ✅ |
| Update `corpus_manifest.lock` | ❌ | ❌ | ✅ | ✅ |
| Approve baseline documentation | ❌ | ❌ | ❌ | ✅ |
| Escalate quality gate failure | ❌ | ❌ | ✅ | ✅ |

## 3. Access Control Implementation

- The web UI enforces a **single active session** via an in-memory token (128-bit CSPRNG).
- Profile databases are owned by the container's isolated UID (10001) with `700` directory permissions.
- No OS-level user accounts are created for Learners; all profiles share the container UID.
- The Operator is responsible for physical access controls to the air-gapped host.
