# DOC-10 User Interface Guide

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Architect (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s4.7, [DOC-02](DOC-02-User-Guide.md), [DOC-03](DOC-03-API-and-Interface-Guide.md) |
| **Status** | Pages named from the `templates/` folder and PRD; layout not inspected in a browser |

> Nothing here has been verified against a running system.

## 1. Pages

| Page | Template | Purpose |
|---|---|---|
| Home (translate) | `index.html` | Direction, level, text, submit |
| Result | `result.html` | Output, fallback marks, thumbs rating, speech and PDF actions |
| Profiles | `profiles.html` | List, create, select, rename, delete |
| Import | `import.html` | Corpus import with chunk summary |
| Dashboard | `dashboard.html` | Counts, Clear Telemetry |
| About and Licences | `about.html` | Version, corpus licences, checkpoint statement |
| Base layout | `base.html` | Header with level selector and status badge, navigation |

## 2. Persistent header

Level selector (levels 1 to 6 and Barbarian), active profile, operation status badge ("Processing"), navigation. Assets are bundled: `static/css/main.css`, `static/js/main.js`. No CDN.

## 3. Accessibility (WCAG 2.1 Level A, PRD s4.7)

| Item | Requirement | Status |
|---|---|---|
| Keyboard operation | Tab order, Enter and Space | Planned: UAT-26 |
| Labels | `label for` or `aria-label` on every control | Planned |
| Alt text | Descriptive or empty for decoration | Planned |
| Contrast | 4.5:1 normal, 3:1 large | Planned: measure `main.css` |
| Language | `lang="en-GB"` | Planned: check `base.html` |
| Error association | `aria-describedby` | Planned |
| JavaScript off | Core flows still work; only TTS controls and the badge need JS | Planned |

## 4. Labelling machine output

Add a visible "Machine translation: check before use" note beside every result and mark `[FALLBACK: x]` in text that is also readable by screen readers (JSP936-HMT-03).

## 5. Open items

Import page, profile rename and the error-mode control were added 2026-11-20 (G-09); their accessibility is not yet audited. The progress file records a WCAG pass; no automated or manual accessibility result is filed.

## Sources

[PRD](../../prd.md) s4.7; `templates/`; `static/`; [progress.md](../../progress.md) Phase 5.
