---
title: Fine-Tuning Procedure
version: 1.0.0
status: Draft
last_updated: 2026-06-08
---

# Fine-Tuning Procedure

## 1. Staging Machine Specification

| Parameter | Requirement |
|---|---|
| OS | Ubuntu 22.04 LTS (x86-64) or Windows 10/11 + WSL2 Ubuntu 22.04 |
| Python | 3.11.x (pinned in `scripts/requirements-staging.txt`) |
| RAM | Minimum 16 GB; 32 GB recommended |
| Storage | Minimum 20 GB free |
| GPU | Optional. NVIDIA GPU with ≥ 8 GB VRAM accelerates fine-tuning. |
| Estimated time (CPU-only) | **8–14 hours** for 3 epochs over full corpus |
| Estimated time (GPU 8 GB VRAM) | **45–90 minutes** for 3 epochs |
| Network | Required during corpus fetch only; may be disconnected before fine-tuning |

## 2. Step-by-Step Procedure

1. Install staging dependencies: `pip install -r scripts/requirements-staging.txt`
2. Run `bash scripts/fetch_corpus.sh` to download corpus artifacts and mT5-small base weights.
3. Run `python scripts/prepare_training_data.py` to apply filtering rules, align pairs, tokenise, output training splits.
4. Review filtering counts logged by `prepare_training_data.py` and record in §4 below.
5. Run `python scripts/finetune_mt5.py` to execute supervised fine-tuning.
6. Run quality gate: `python scripts/verify_checkpoint.py` (spot-check) and `python scripts/eval_chrf.py` (chrF).
7. Record results in §5 below.
8. Update `corpus_manifest.lock` with SHA-256 checksums and quality gate results.
9. Package checkpoint for physical media transfer.

## 3. Corpus Filtering Rules

| Source | Filtering Rule |
|---|---|
| Latin Vulgate Bible | Exclude deuterocanonical books and post-4th-century CE additions. Jerome's 4th-century CE Latin is accepted. Post-Carolingian variants excluded. |
| Leipzig LatinISE | Exclude texts dated > 300 CE. Undated texts included only if author is verifiably Classical. |
| Perseus Digital Library | No additional filtering; selected excerpts are already Classical (Cicero, Caesar, Vergil, Livy, Ovid, Tacitus). |

## 4. Filtering Counts Record

_To be completed by Staging Engineer after running `scripts/prepare_training_data.py`._

| Source | Retained Pairs | Excluded Pairs | Notes |
|---|---|---|---|
| Vulgate | PENDING | PENDING | |
| Leipzig LatinISE | PENDING | PENDING | |
| Perseus Digital Library | PENDING | 0 | No filtering applied |
| **Total** | **PENDING** | **PENDING** | |

## 5. Quality Gate Log

_To be completed by Staging Engineer after each training run._

| Run | Date (UTC) | Operator | Spot-Check (pass/50) | chrF EN→LA | chrF LA→EN | Result |
|---|---|---|---|---|---|---|
| 1 | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

## 6. Model Quality Escalation Log

_Completed only if two consecutive runs fail either gate sub-check._

| Escalation Date | Failing Direction(s) | Action Taken | Authorised By |
|---|---|---|---|
| — | — | — | — |
