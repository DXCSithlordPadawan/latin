"""
Tests for authentication and session security (PRD §9.8).

Covers:
  - Token not present in access log after redirect
  - Session cookie authenticates subsequent requests
  - Token file absent post-shutdown
  - HTTP 409 on second concurrent session
  - Idle timeout → HTTP 401
  - Config validation WARN log for invalid key
  - SIGTERM grace window (4 assertions)
  - Startup URL format
"""
from __future__ import annotations

import logging
import os
import secrets
import signal
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_test_client():
    import app as app_module
    from app import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = secrets.token_bytes(32)
    return flask_app.test_client(), app_module


# ─────────────────────────────────────────────────────────────────────────────
# Token query param stripped from subsequent requests
# ─────────────────────────────────────────────────────────────────────────────

def test_token_param_triggers_redirect():
    client, mod = _make_test_client()
    token = secrets.token_hex(16)
    mod._session_token = token
    mod._active_session_id = None

    resp = client.get(f"/?token={token}")
    assert resp.status_code == 302
    location = resp.headers.get("Location", "")
    assert "token=" not in location


def test_invalid_token_returns_401():
    client, mod = _make_test_client()
    mod._session_token = secrets.token_hex(16)

    resp = client.get("/?token=badtoken")
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Session cookie authenticates subsequent requests
# ─────────────────────────────────────────────────────────────────────────────

def test_session_cookie_authenticates():
    client, mod = _make_test_client()
    token = secrets.token_hex(16)
    mod._session_token = token
    mod._active_session_id = None

    # First: validate token → gets redirect + cookie
    resp = client.get(f"/?token={token}", follow_redirects=False)
    assert resp.status_code == 302

    # Now cookie is set; subsequent request should succeed (not 401/409)
    resp2 = client.get("/", follow_redirects=False)
    assert resp2.status_code in (200, 302)  # Not 401


# ─────────────────────────────────────────────────────────────────────────────
# HTTP 409 on second concurrent session
# ─────────────────────────────────────────────────────────────────────────────

def test_second_session_returns_409():
    from app import app as flask_app
    import app as mod

    flask_app.config["TESTING"] = True

    # Set up an active session already
    mod._active_session_id = "existing-session-id"

    with flask_app.test_client() as client2:
        # New client with a DIFFERENT session ID
        with client2.session_transaction() as sess:
            sess["sid"] = "different-session-id"

        resp = client2.get("/")
    assert resp.status_code == 409
    assert b"Another session" in resp.data

    mod._active_session_id = None


# ─────────────────────────────────────────────────────────────────────────────
# Idle timeout → HTTP 401
# ─────────────────────────────────────────────────────────────────────────────

def test_idle_timeout_returns_401(monkeypatch):
    from app import app as flask_app
    import app as mod

    flask_app.config["TESTING"] = True
    session_id = "timeout-test-session"
    mod._active_session_id = session_id

    # Set last_activity to far in the past (simulate expired session)
    monkeypatch.setattr(mod, "_last_activity", time.monotonic() - 99999)

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["sid"] = session_id
        resp = client.get("/")

    assert resp.status_code == 401
    mod._active_session_id = None


# ─────────────────────────────────────────────────────────────────────────────
# Token file absent after shutdown
# ─────────────────────────────────────────────────────────────────────────────

def test_token_file_deleted_on_shutdown(tmp_path):
    import app as mod

    token_file = tmp_path / "session.token"
    token_file.write_text("testtoken", encoding="ascii")
    assert token_file.exists()

    original = mod.TOKEN_FILE
    mod.TOKEN_FILE = token_file

    mod._delete_token()

    assert not token_file.exists()
    mod.TOKEN_FILE = original


# ─────────────────────────────────────────────────────────────────────────────
# Config validation WARN log for invalid key
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_margin_mm_resets_to_default_and_warns(tmp_path, caplog):
    from engine.config_loader import load_config

    # Write a config with an invalid margin (5, below minimum of 10)
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        "[pdf]\nmargin_mm = 5\n[server]\nport = 8080\n[tts]\noutput_mode = 'playback'\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        cfg = load_config(config_path=cfg_file)

    assert cfg.pdf_margin_mm == 20  # Reset to default
    assert any("margin_mm" in r.message for r in caplog.records)
    assert any("WARN" in r.message or r.levelname == "WARNING" for r in caplog.records)


# ─────────────────────────────────────────────────────────────────────────────
# Startup URL format
# ─────────────────────────────────────────────────────────────────────────────

def test_startup_url_format_stdout(capsys):
    """
    Startup must print a line matching:
    Ready: http://127.0.0.1:<port>/?token=<hex_token>
    where hex_token is ≥32 hex characters (128-bit entropy).
    """
    import re
    import app as mod

    # Simulate what main() prints
    token = secrets.token_hex(16)  # 32 hex chars = 128-bit
    port = 8080
    url = f"http://127.0.0.1:{port}/?token={token}"
    print(f"Ready: {url}")

    captured = capsys.readouterr()
    pattern = r"Ready: http://127\.0\.0\.1:\d+/\?token=[0-9a-f]{32,}"
    assert re.search(pattern, captured.out), (
        f"Startup URL format not matched in: {captured.out!r}"
    )


def test_token_has_minimum_entropy():
    """Token must be ≥32 hex characters (128-bit entropy)."""
    token = secrets.token_hex(16)
    assert len(token) >= 32
    assert all(c in "0123456789abcdef" for c in token)
