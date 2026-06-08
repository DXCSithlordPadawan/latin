---
title: UI Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# UI Guide

## 1. Page Inventory

| Page | URL | Description |
|---|---|---|
| Home / Translate | `/` | Translation input/output; feedback controls; TTS; PDF |
| Profiles | `/profiles` | Profile list, create, delete |
| Dashboard | `/dashboard` | Adaptive learning data; Clear Telemetry |
| About / Licences | `/about` | App version; corpus licences |

## 2. Persistent Header Controls

The following controls appear on every page:

| Control | Type | Behaviour |
|---|---|---|
| Level selector | `<select>` | Changes active output level immediately on submit; no confirmation |
| Operation status badge | `<span>` (JS) | Shows "⟳ Processing…" during in-flight requests; absent when JS disabled |
| Navigation links | `<a>` | Translate / Profiles / Dashboard / About |

## 3. Translate Page Controls

| Control | Element | `aria-label` |
|---|---|---|
| Direction selector | `<select name="direction">` | "Translation direction" |
| Source text | `<textarea name="text">` | Labelled via `<label for>` |
| Barbarian Mode checkbox | `<input type="checkbox">` | "Enable Barbarian Mode" |
| Translate button | `<button type="submit">` | "Translate text" |
| Thumbs-up | `<button type="submit" name="rating" value="1">` | "Rate translation helpful" |
| Thumbs-down | `<button type="submit" name="rating" value="-1">` | "Rate translation unhelpful" |
| Listen (TTS) | `<button type="submit">` | "Listen to translation (text-to-speech)" |
| Download PDF | `<button type="submit">` | "Download translation as PDF workbook" |

## 4. WCAG 2.1 Level A Conformance

| Item | Implementation |
|---|---|
| Keyboard navigation | All interactive controls reachable via Tab / Shift-Tab; Enter / Space activation |
| Labels | All inputs have `<label for>` or `aria-label` |
| Alt text | Non-decorative images carry descriptive `alt`; decorative carry `alt=""` |
| Colour contrast | Foreground/background ratio ≥ 4.5:1 for normal text; ≥ 3:1 for large text |
| Language declaration | `<html lang="en-GB">` on all pages |
| Error association | Error messages linked via `aria-describedby` |
| Live regions | Operation status badge uses `aria-live="polite"` |

## 5. JavaScript Behaviour

TTS playback controls are the only feature requiring JavaScript. All core workflows (translation, PDF generation, profile management, level switching) function with JavaScript disabled.

The operation status badge requires JavaScript; when JS is disabled it is absent. Operators should judge operation duration from server response time.

## 6. Browser Support

Designed and tested against Firefox ESR (current) and Chromium/Chrome (current stable). No polyfills for IE, Edge Legacy, or browsers released before 2020.
