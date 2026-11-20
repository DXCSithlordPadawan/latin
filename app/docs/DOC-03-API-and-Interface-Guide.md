# DOC-03 API and Interface Guide

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Architect (deputy: CONFIRM) |
| **Version** | 2.0 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md) s4.7, [DOC-01](DOC-01-Architecture-Guide.md) |
| **Status** | Routes read from `app.py` on 2026-11-20. Not exercised by this document's author |

> All routes are on `http://127.0.0.1:<port>` only. Every route except `static` passes through `auth_middleware`.

## 1. Authentication

| Step | Behaviour in code | PRD requirement | Match |
|---|---|---|---|
| First load | `GET /?token=<hex>` equal to the in-memory token: new session id, cookie set, 302 to the same path without `token` | Same | Yes |
| Wrong token | 401 | 401 | Yes |
| Token again later | Refused with 401: the token is cleared on first use (fixed 2026-11-20, unit test) | Not re-accepted | Yes |
| Cookie | Flask signed session (`sid`) | In-memory cookie, HMAC-SHA-256 | Partly: Flask uses HMAC-SHA-1 or SHA-256 by version (CONFIRM) |
| Second session | 409 text if cookie sid differs from active sid | 409 | Only if the second client has its own cookie, see G-01 |
| Idle | 401 text after `session_timeout_minutes` since last request | Same | Yes (single global timer) |
| Shutting down | 503 | not specified | Extra |
| Access log of the token URL | Not suppressed in code (Werkzeug default logging) | Path only, no query | **Not evidenced** |

## 2. Endpoints

| Method and path | Form fields | Success | Errors | Notes |
|---|---|---|---|---|
| `GET /` | none | HTML index | 401, 409, 503 | |
| `POST /translate` | `text`, `direction` (`en-la` default, `la-en`), `level` 1 to 6, `barbarian` = `1` | HTML result | 400 over 512 tokens (count in body); 500 "Translation failed" | Direction defaults to `en-la` if missing, which differs from "user must choose" |
| `POST /tts` | `text` | 200 text "Audio sent to playback device." or WAV download with timestamped name | none handled | No try or except around synthesis |
| `POST /pdf` | `content_type` (`workbook` default), `text` | `application/pdf`, `workbook.pdf` attachment | none handled | Fixed file name; text is not sanitised here |
| `POST /feedback` | `rating` (`1` or `-1`), `source`, `output`, `direction`, `level` | 200 "OK" | 400 invalid rating; 404 no profile | Source and output cut to 64 characters |
| `GET /about` | none | HTML | | Static licences |
| `GET /profiles` | none | HTML list | | |
| `GET /dashboard` | none | HTML with counts | | Swallows database errors silently |
| `POST /set-level` | `level` 1 to 7 | 302 to `/` | 400, 500 | 7 is Barbarian |
| `POST /profile/create` | `name` (the form used `display_name`, so creation always failed; fixed 2026-11-20) | 302 to `/profiles` | 400, 500 | Name sanitised and cut to 64 |
| `POST /profile/select` | `slug` | 302 to `/` | 400, 404 | Checked against the profile list |
| `POST /profile/delete` | `slug` | 302 to `/profiles` | 400, 500 | Slug format validated; unknown slug is a 400 (G-07 fixed 2026-11-20) |
| `POST /clear-telemetry` | none | 302 to `/dashboard` | 500 | Acts on the session profile |

Added 2026-11-20 (G-09): `POST /profile/rename` (`slug`, `name`), `POST /set-error-mode` (`mode` lenient or strict, saved on the session profile), `GET /import` and `POST /import` (multipart `file`, optional `confirm_large=1`; 400 on a wrong type or an unconfirmed file over 100 MB). Still not present: session start and end history writes.

## 3. Response and error conventions

Plain-text bodies for errors; HTML for pages; no JSON API. Errors never include user text beyond 64 characters in logs.

## 4. Headers and browser protections

**Fixed 2026-11-20 (unit tests):** every response now carries a Content-Security-Policy (`default-src 'self'`, `script-src 'self'`, no framing), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. The text below is the earlier finding, kept for the record.

None of `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy` or `Cache-Control: no-store` is set in code. The token URL could leak through Referer before the redirect completes only if a page loads external content, and none is bundled. Planned: add the four headers (JS guide s7 CSP; OWASP A05).

## 5. CSRF

**Fixed 2026-11-20 (unit tests):** each session has a random `csrf` value; forms include it as `csrf_token`; a POST without a matching value gets 403 after the auth checks. The session cookie is `SameSite=Strict` and `HttpOnly`. Earlier finding follows.

No token on any POST (G-08). Planned: per-session CSRF value in forms, checked server side, plus `SameSite=Strict` on the session cookie.

## 6. Interface to the host

| Interface | Direction | Detail |
|---|---|---|
| stdout `Ready:` line | out | Contains the secret; keep the terminal private |
| `session.token` file | out | 600; deleted on clean shutdown |
| SIGTERM | in | 5-second grace, then token delete and exit 0 |
| Volume `~/.airgap-translator` | both | Profiles, config, token |
| Audio device | out | Needed for `playback` mode |

## Sources

`app.py` read in full 2026-11-20; [PRD](../../prd.md) s4.7, s9.8; Python guide s2 (Flask).
