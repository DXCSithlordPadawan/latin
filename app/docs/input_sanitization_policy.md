# Input Sanitisation Policy

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Security Authority (deputy: CONFIRM) |
| **Version** | 2.0 draft (1.0.0 text retained; Baseline status withdrawn) |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md), [DOC-01](DOC-01-Architecture-Guide.md), [standards matrix](standards-conformance-matrix.md) |
| **Status** | Policy; code in engine/sanitiser.py |

> Nothing here has been verified against a running system.

## 1. Sanitisation Rules (engine/sanitiser.py)

All user-supplied strings are processed through `sanitise_text()` before any use in the application.

| Rule | Implementation | Rationale |
|---|---|---|
| Null byte removal | `text.replace("\x00", "")` + regex | Prevents null-byte injection |
| C0 control character removal | Regex `[\x00-\x08\x0b\x0c\x0e-\x1f]` | Prevents control sequence injection |
| C1 control character removal | Regex `[\x80-\x9f]` | Prevents Unicode control injection |
| DEL (U+007F) removal | Regex `\x7f` | |
| TAB / LF / CR preserved | Not matched by control regex | Legitimate whitespace |
| Shell metacharacter removal | Regex `[;&\|` + `$<>\\]` | Prevents shell injection in log entries |
| NFC normalisation | `unicodedata.normalize("NFC", text)` | Eliminates overlong UTF-8 / decomposed forms |

## 2. Token Hard Cap

- **Limit:** 512 whitespace-split tokens
- **Enforcement:** `enforce_token_cap()` called before any inference request
- **Rejection behaviour:** `ValueError` raised with the message `"Input exceeds the 512-token hard cap (<N> tokens)."`; no partial translation returned
- **User visibility:** The UI renders the error message inline; the user must shorten their input

## 3. Corpus Import Policy

- Files are processed in **50,000-character sequential chunks**
- Files > 100 MB trigger a confirmation prompt before import begins
- Each chunk is sanitised independently before database insertion
- A failure mid-file is reported with the chunk number; already-committed chunks are not rolled back

## 4. CSV Import Policy

- All cell values are cast to string literals via `str(cell)`
- Leading `=`, `+`, `-`, `@` characters (spreadsheet formula initiators) are prefixed with `'` to prevent formula evaluation if exported to a spreadsheet application
- No formula evaluation is performed; no dynamic expression evaluation occurs anywhere in the application

## 5. Log Content Truncation

All user-supplied strings included in log entries are truncated to a maximum of **64 characters** and suffixed with `[…redacted]` if truncation occurs. This applies to all log levels (debug, info, warning, error).

Implementation: `engine/sanitiser.truncate_for_log(value, max_len=64)`
