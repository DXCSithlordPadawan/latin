---
title: User Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# User Guide

## 1. Getting Started

Open the URL printed to the terminal when the container starts:

```
Ready: http://127.0.0.1:8080/?token=<hex_token>
```

Copy the full URL (including the token) and paste it into Firefox ESR or Chromium. You will be redirected to the home page and a session cookie will be set.

## 2. Translating Text

1. On the **Translate** page, choose a direction: **English → Latin** or **Latin → English**.
2. Type or paste your text into the source text box (maximum 512 tokens).
3. Select your desired **Output Level** from the header selector (Level 1–6 or Barbarian Mode).
4. Click **Translate**.
5. The translation appears below the form.

## 3. Output Levels

| Level | Name | Suitable For |
|---|---|---|
| 1 | Beginner | Ages 2–4; single-clause SVO sentences |
| 2 | Elementary | Ages 5–6; compound sentences |
| 3 | Primary | Ages 7–8; simple subordinate clauses |
| 4 | Intermediate | Ages 8–12; multi-clause, perfect/imperfect |
| 5 | Secondary | Ages 12–16; complex rhetorical nesting |
| 6 | Advanced | Adults; Golden Age prose (Cicero/Caesar) |
| — | Barbarian Mode | Any; fragmented imperatives, broken inflections |

The current level is always shown in the page header and can be changed at any time without navigating away.

## 4. Feedback

After each translation, use the **👍** or **👎** buttons to rate the quality. Ratings are stored per profile and used to target weak vocabulary in future PDF exercises.

## 5. Text-to-Speech (TTS)

Click **🔊 Listen** to hear the translation spoken using Classical Latin phonetics (espeak-ng). The audio mode is set per profile:

- **Playback** — audio plays through the system audio device (default).
- **Export** — audio is downloaded as a `.wav` file.
- **Both** — audio plays and is downloaded simultaneously.

Change the TTS mode in your profile settings.

## 6. Downloading Workbook PDFs

Click **📄 Download Workbook PDF** after any translation to generate a printable A4 exercise sheet. Three layout types are available:

- **Workbook** — source text with alternating handwriting space below each line.
- **Note Sheet** — two-column layout with a notes margin.
- **Declension Matrix** — empty case grid for vocabulary practice.

## 7. Profile Management

Access **Profiles** from the navigation bar to:
- Create a new profile (each learner should have their own profile).
- Switch between profiles.
- Delete a profile (irreversible; data is securely erased).

## 8. Adaptive Learning Dashboard

The **Dashboard** shows:
- Words causing repeated translation failures (word friction).
- Your translation feedback ratings history.
- A **Clear Telemetry** button to reset all adaptive data for your profile.

## 9. Session & Security

- Sessions expire after 60 minutes of inactivity (configurable).
- Only one browser session is active at a time.
- The session token is invalidated when the container stops.
- No data leaves the host at runtime.
