# DOC-14 Engineering Automated Integration Tests (EAIT)

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Architect (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s9, [DOC-13](DOC-13-User-Acceptance-Tests.md) |
| **Status** | The unit suite exists and was run on 2026-11-20. Layers 2 to 4 are specified only |

> Nothing here has been verified in a container.

## 1. Test layers

| Layer | Needs | Status |
|---|---|---|
| 1 Offline unit (pytest) | Python only | **Built.** 176 passed, 1 deselected (`slow`), 0 failed, in 15.75 s on Python 3.12.9 on Windows, run 2026-11-20 by the author of this set. The progress file reports the same count on 2026-06-08. After Stage 0 (2026-11-20) the suite is 210 passed and no xfails after the fourth round (adds `tests/test_stage1_routes.py`) (the Containerfile checks are static text tests, not a build); gap tests are in `tests/test_gaps_stage0.py` |
| 2 In-container | Built image | Specified |
| 3 Target host | Host with audio and auditd | Specified |
| 4 Fault injection | Image plus scripts | Specified |

## 2. Layer 1 modules

| Module | Covers |
|---|---|
| `test_translation_engine.py` | Prefix types, confidence gate, Barbarian, slow chrF test |
| `test_reading_age.py` | Level specs and mid-session switch |
| `test_input_sanitisation.py` | Null, control, shell characters; cap; CSV |
| `test_pdf.py` | Layouts, paper size, headers, no file written |
| `test_tts.py` | Macron, hard consonant, diphthong, modes |
| `test_auth_session.py` | Token, cookie, 409, idle, SIGTERM |
| `test_adaptive_learning.py` | Telemetry, feedback, clear |
| `test_error_handling.py` | Lenient and strict, truncation |
| `test_port_startup.py` | Busy port, Ready line |
| `test_schema_migration.py` | N-1, future version, failing script |
| `test_container_integrity.py` | SHA-256 logic, manifest, spot-check count |

Known test limits: the engine tests inject a mock model; the TTS tests mock synthesis; the FreeSerif macron assertion skips if the font is missing. The 176 passes therefore say nothing about the real model, audio or fonts.

## 3. Tests to add (G list)

| New test | Closes |
|---|---|
| Token reuse after first load is refused and the 409 holds | G-01, UAT-05 |
| Startup refuses a changed checkpoint and a changed font | G-02, UAT-11 |
| Migration failure leaves the version and data unchanged | G-05, UAT-18 |
| Existing profile with a corrupt file is caught at startup | G-06, UAT-19 |
| `slug` with `../` is refused on delete | G-07, UAT-15 |
| POST without CSRF value is refused | G-08, UAT-29 |
| Missing Whitaker data does not mark every word as fallback | G-11, UAT-10 |
| Static check of the Containerfile: no `|| pip install`, no `|| echo` after the checksum step | G-03 (done 2026-11-20) |

## 4. Static and security checks (Layer 1 additions)

`ruff` or `flake8`; `bandit` on `app.py` and `engine/`; `pip-audit` against the wheelhouse on staging; `shellcheck` on `fetch_corpus.sh` (Bash guide s9); a test that no `render_template_string` or `eval` use exists. Tool availability on the staging machine is unverified.

## 5. CI

No CI product is chosen. Until then the single command runs on the staging machine before release: `pytest --junitxml=docs/test_results/results.xml` and, for the compliance run, `pytest -m slow`.

## Sources

`tests/` file list; `pytest.ini`; a pytest run on 2026-11-20; [progress.md](../../progress.md).
