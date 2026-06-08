---
title: RACI Matrix
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# RACI Matrix

R = Responsible · A = Accountable · C = Consulted · I = Informed

| Activity | Operator | Learner | Staging Engineer | Project Lead |
|---|---|---|---|---|
| Corpus acquisition & filtering | I | — | R | A |
| Model fine-tuning | I | — | R | A |
| Quality gate execution | I | — | R | A |
| Quality gate escalation (≥2 failures) | — | — | C | A/R |
| OCI image build | I | — | R | A |
| SHA-256 checksum recording | I | — | R | A |
| Physical media transfer | R | — | C | A |
| Air-gapped host deployment | R | — | — | A |
| auditd rule configuration | R | — | — | A |
| Backup cron registration | R | — | — | A |
| Day-to-day application use | C | R | — | I |
| Profile creation / management | C | R | — | I |
| Telemetry review | C | R | — | I |
| Error log monitoring | R | I | — | A |
| Database backup verification | R | — | — | A |
| Container upgrade | R | I | C | A |
| Model refresh trigger decision | I | — | C | A/R |
| Compliance gate sign-off (Phase 7) | C | — | C | A/R |
| Documentation baseline approval | C | — | C | A/R |
| Incident escalation | R | I | C | A |
