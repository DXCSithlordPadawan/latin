# DOC-13 User Acceptance Tests

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Project Lead with Support Lead |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s9, [DOC-14](DOC-14-EAIT.md), [BRD requirements](../brd/latin_reqs.md) |
| **Status** | No acceptance test has been executed in a container. Every case shows **Not run** until a dated evidence file exists in the gate pack |

> Nothing here has been verified against a running system. The 176 pytest cases are unit-level and are listed in DOC-14; they do not replace these.

| UAT | Requirement | Steps | Expected | Result |
|---|---|---|---|---|
| UAT-01 | FR-TRN-01, FR-RDG-01 | Translate a known EN sentence at each of levels 1 to 6 and Barbarian | Output differs by level; Barbarian shows broken cases and imperatives | Not run |
| UAT-02 | FR-TRN-05 | Translate a Latin sentence LA to EN | UK English spelling; no fallback marks for known words | Not run |
| UAT-03 | FR-ING-01, FR-TRN-07 | Submit 513 tokens | Refused with count; no partial output | Not run |
| UAT-04 | FR-ING-01 | Submit text with null, control and shell characters | Removed; "input sanitised" shown; no error | Not run |
| UAT-05 | FR-UI-03 | Open the startup URL, then request it again from a second browser | Second use refused or ignored; first session unaffected | Not run (code fixed 2026-11-20, unit test passes) |
| UAT-06 | FR-UI-04 | Present a valid cookie from a second client while one is active | HTTP 409; first session intact | Not run |
| UAT-07 | FR-UI-05 | Wait past the timeout with no requests | HTTP 401 | Not run |
| UAT-08 | FR-UI-02 | Start with the port busy | Exit non-zero with the stated message | Not run |
| UAT-09 | FR-UI-07 | SIGTERM during a long request | In-grace requests complete; others reset; exit 0; token file gone | Not run |
| UAT-10 | FR-TRN-04 | Translate with the Whitaker bundle present | Only unknown words carry `[FALLBACK:]` | Not run (unloaded-dictionary case fixed 2026-11-20; needs a real model and data) |
| UAT-11 | FR-TRN-03, FR-OPS-01 | Flip one byte in the checkpoint and start | Startup refuses and says why | Not run (code fixed 2026-11-20, unit test passes) |
| UAT-12 | FR-TTS-03 | Speak "Roma", "Marcus", "Caesar" | Long vowels held; hard C; audible check | Not run |
| UAT-13 | FR-TTS-02 | Export mode | WAV download with timestamp name; no file in the container | Not run |
| UAT-14 | FR-PDF-01, FR-PDF-02, FR-PDF-03 | Generate three layouts; set Letter | Macrons render; Letter size; no file on disk | Not run |
| UAT-15 | FR-PRF-02 | Create then delete a profile; try slug `../x` | File erased; traversal refused | Not run (traversal code fixed 2026-11-20, unit test passes) |
| UAT-16 | FR-ADL-05 | Clear telemetry on profile A | A emptied; B unchanged | Not run |
| UAT-17 | FR-ADL-04 | Thumbs up and down | `+1` and `-1` rows with 64-character truncation | Not run |
| UAT-18 | FR-ADL-02 | Start with a version N-1 DB, a future-version DB, and a failing script | Migrates; refuses; rolls back with no change | Not run (code fixed 2026-11-20, unit test passes) |
| UAT-19 | FR-ERR-03 | Corrupt a profile file and start | Integrity failure; restore prompt; no crash | Not run (code fixed 2026-11-20, unit test passes) |
| UAT-20 | FR-OPS-01 | Build with FIPS missing, a changed artifact, and no wheelhouse | Each build fails | Not run (code fixed 2026-11-20, static tests pass; no image built) |
| UAT-21 | FR-OPS-06 | Reach the UI from the host browser using the documented run line | Page loads with the container off any external network | Not run (G-10) |
| UAT-22 | FR-OPS-04 | `auditctl -l` | Five `airgap_*` rules | Not run |
| UAT-23 | FR-ERR-04 | Run cron; keep 7; restore one profile | 7 snapshots; restore starts clean | Not run |
| UAT-24 | NFR-01 to NFR-06 | Fill the SLA table on the target host | Every value within SLA | Not run |
| UAT-25 | FR-STG-03 | Quality gate on the staged checkpoint | Spot-check >= 40/50 and chrF >= 45 both ways | Not run |
| UAT-26 | NFR-11 | Keyboard-only run of every page; label and contrast check | Level A items pass | Not run |
| UAT-27 | FR-ERR-01 | Set strict mode and translate with an unknown word | `[UNKNOWN: word]`; no partial output | Not run (code added 2026-11-20, unit tests pass) |
| UAT-28 | FR-ING-02, FR-ING-04 | Import a 120 MB file | Prompt first; chunks counted; failure keeps committed chunks | Not run (G-09) |
| UAT-29 | FR-UI-12 | Post without a CSRF value | Refused | Not run (code fixed 2026-11-20, unit test passes) |
| UAT-30 | FR-STD-02 | Check the model card, ODD and bias note exist and are reviewed | Present, dated, owner named | Not run |

## Sources

[PRD](../../prd.md) s9; [DOC-01](DOC-01-Architecture-Guide.md) s9.
