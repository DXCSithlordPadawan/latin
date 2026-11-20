# Spike: run line reachability (FEAT-01, G-10)

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Operator (deputy: CONFIRM) |
| **Version** | 0.1 draft |
| **Date** | 2026-11-20 |
| **Governing documents** | [DOC-09](DOC-09-Deployment-Guide.md) s6, [DOC-01](DOC-01-Architecture-Guide.md) G-10 |
| **Status** | **Not run.** This machine has no Podman, Docker or WSL distribution, so the spike must be run on a Linux host with rootless Podman |

> Question: can a browser on the host reach the app while the container has no route to any external network? The three options below are candidates to test, not known to work.

## Pass test (same for every option)

1. `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/` from the host returns 401 (login required), not a connection error.
2. Inside the container, `python3.11 -c "import socket; socket.create_connection(('1.1.1.1',53),2)"` fails.
3. The `Ready:` URL opens in the host browser.
4. Record `podman --version`, host OS, and the exact command.

## Option A: the PRD line (expected to fail)

```bash
podman run --rm --network=none -p 127.0.0.1:8080:8080 airgap-translator:test
```
Record the exact error. Expectation: Podman refuses to publish ports with no network.

## Option B: internal network, app bound to the container interface

```bash
podman network create --internal airgap-int
podman run --rm --network=airgap-int -p 127.0.0.1:8080:8080 airgap-translator:test
```
Needs the app to bind the container address (not 127.0.0.1): set `server.bind = "0.0.0.0"` (key added 2026-11-20, default `127.0.0.1`; using it means changing PRD FR-UI-01, which forbids it), and a check that `--internal` really blocks outbound traffic (pass test step 2). Publishing ports on an internal network may also be refused; record it.

## Option C: Unix socket and a host-side forwarder

App listens on a Unix socket in the mounted volume; a host process (for example `socat TCP-LISTEN:8080,bind=127.0.0.1,fork UNIX-CONNECT:<socket>`) forwards loopback traffic. Keeps `--network=none`. Needs the Flask server run behind a socket-capable server (for example gunicorn) and `socat` on the host.

## Decision record

| Option | Works | Blocks outbound | Extra parts | Chosen |
|---|---|---|---|---|
| A | | | none | |
| B | | | `server.bind` key | |
| C | | | socat, gunicorn | |

After the decision: update DOC-09 s6, DOC-11, the README quick start, PRD FR-OPS-06, UAT-21, and make the HEALTHCHECK read the configured port.

## Sources

Podman documentation for `--network`, `network create --internal` and `-p` (to be read on the host before the run; not fetched here).
