---
title: API Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# API Guide

All endpoints are served at `http://127.0.0.1:<port>` (loopback only). All requests must present a valid session cookie (obtained by validating the startup token on first load).

## 1. Authentication

### Token Validation (First Load)

```
GET /?token=<hex_token>
```

- Validates token against in-memory value.
- On success: issues session cookie; redirects to `/` (token stripped from URL).
- On failure: `HTTP 401`

### Session Cookie

All subsequent requests are authenticated via the in-memory session cookie. Re-submitting `?token=` after first validation is ignored.

**Second concurrent session:** `HTTP 409 Conflict` with body `Another session is already active.`

**Idle timeout:** `HTTP 401` after `server.session_timeout_minutes` (default 60) with no authenticated requests.

---

## 2. Endpoints

### `GET /`
Serves the translation home page.

---

### `POST /translate`

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Source text (max 512 tokens after sanitisation) |
| `direction` | string | Yes | `en-la` or `la-en` |
| `level` | integer | Conditional | 1–6; required for EN→LA non-barbarian |
| `barbarian` | `"1"` | No | Enable Barbarian Mode (EN→LA only) |

**Responses:**

| Status | Meaning |
|---|---|
| `200` | HTML result page with translation output |
| `400` | Input exceeds 512-token cap (body contains count) |
| `500` | Translation engine error |

---

### `POST /tts`

Synthesise text to speech.

**Form fields:** `text` (string)

**Responses:**

| Mode | Status | Headers | Body |
|---|---|---|---|
| `playback` | `200` | `Content-Type: text/plain` | `"Audio sent to playback device."` |
| `export` | `200` | `Content-Disposition: attachment; filename="tts_<ts>.wav"`, `Content-Type: audio/wav` | WAV bytes |
| `both` | `200` | Same as export | WAV bytes (also plays to device) |

---

### `POST /pdf`

Generate a printable PDF workbook.

**Form fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `content_type` | string | `workbook` | `workbook`, `note_sheet`, or `declension` |
| `text` | string | — | Source text for PDF content |

**Response:** `200`, `Content-Disposition: attachment; filename="workbook.pdf"`, `Content-Type: application/pdf`

---

### `POST /feedback`

Record a translation quality rating.

**Form fields:** `source` (64-char max), `output` (64-char max), `direction`, `level`, `rating` (`"1"` or `"-1"`)

**Responses:** `200 OK` or `400 Bad Request` (invalid rating) or `404` (profile not found)

---

### `GET /profiles`
Profile management page.

### `GET /dashboard`
Adaptive learning dashboard.

### `GET /about`
About & Licences static page.

---

## 3. Error Codes

| HTTP Status | Meaning |
|---|---|
| 400 | Bad request (token cap exceeded, invalid form data) |
| 401 | Unauthenticated or session expired |
| 409 | Second concurrent session attempt |
| 500 | Internal server error (see `/logs/error.log`) |
| 503 | Server shutting down (SIGTERM grace window active) |
