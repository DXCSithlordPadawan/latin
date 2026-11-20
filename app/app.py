"""
Main application entry point.

Flask server bound to 127.0.0.1 only.
Session token authentication with single-session enforcement.
SIGTERM grace window of 5 seconds.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import secrets
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from engine.config_loader import load_config
from engine.tts_engine import TtsEngine, export_filename

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
AIRGAP_DIR = Path.home() / ".airgap-translator"
PROFILES_DIR = AIRGAP_DIR / "profiles"
TOKEN_FILE = AIRGAP_DIR / "session.token"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── Logging (UTC ISO 8601; user strings truncated to 64 chars) ─────────────
_log_formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
_log_formatter.converter = time.gmtime  # Force UTC

_file_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "error.log", maxBytes=10 * 1024 * 1024, backupCount=3
)
_file_handler.setFormatter(_log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler])
log = logging.getLogger("app")

# ── Config ─────────────────────────────────────────────────────────────────
cfg = load_config()

# ── Flask app ──────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = secrets.token_bytes(32)
app.config.update(SESSION_COOKIE_SAMESITE="Strict", SESSION_COOKIE_HTTPONLY=True)

# ── Session token ─────────────────────────────────────────────────────────
_session_token: str | None = None
_active_session_id: str | None = None
_session_lock = threading.Lock()
_last_activity: float = time.monotonic()

# ── Shutdown state ────────────────────────────────────────────────────────
_shutting_down = False
_grace_deadline: float | None = None


def _generate_token() -> str:
    return secrets.token_hex(16)  # 128-bit entropy


def _write_token(token: str) -> None:
    AIRGAP_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token, encoding="ascii")
    TOKEN_FILE.chmod(0o600)


def _delete_token() -> None:
    global _session_token
    _session_token = None
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def _check_port_available(port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        result = sock.connect_ex(("127.0.0.1", port))
        if result == 0:
            print(
                f"ERROR: Port {port} is already in use on 127.0.0.1. "
                f"Set a different port in config.toml (server.port) and restart.",
                file=sys.stderr,
            )
            sys.exit(1)
    finally:
        sock.close()


# ── Authentication middleware ──────────────────────────────────────────────

@app.before_request
def auth_middleware():
    global _active_session_id, _last_activity, _session_token

    if _shutting_down:
        abort(503)

    # Unauthenticated paths
    if request.endpoint in ("static",):
        return

    # Token validation on first load
    token_param = request.args.get("token")
    if token_param:
        # Single use (PRD 4.7, G-01): the token is consumed by the first valid request,
        # so a second browser holding the URL gets 401 and cannot replace the session.
        with _session_lock:
            valid = _session_token is not None and secrets.compare_digest(token_param, _session_token)
            if valid:
                _session_token = None
                session_id = secrets.token_hex(8)
                _active_session_id = session_id
        if valid:
            # Valid token — issue session cookie and redirect without token param
            session["sid"] = session_id
            _last_activity = time.monotonic()
            # Redirect to same path without token param (strip from URL/logs)
            clean_url = request.path
            if request.query_string:
                params = {
                    k: v
                    for k, v in request.args.items()
                    if k != "token"
                }
                if params:
                    from urllib.parse import urlencode
                    clean_url += "?" + urlencode(params)
            log.info("Token validated; session started.")
            return redirect(clean_url, code=302)
        else:
            abort(401)

    # Subsequent requests — validate session cookie
    sid = session.get("sid")
    if not sid:
        abort(401)

    with _session_lock:
        if sid != _active_session_id:
            # Second concurrent session attempt
            return Response(
                "Another session is already active. Close the existing session or restart the container.",
                status=409,
                content_type="text/plain",
            )

    # Idle timeout check
    timeout_secs = cfg.server_session_timeout_minutes * 60
    if time.monotonic() - _last_activity > timeout_secs:
        session.clear()
        with _session_lock:
            _active_session_id = None
        return Response(
            "Session expired due to inactivity. Restart the container to obtain a new token.",
            status=401,
            content_type="text/plain",
        )

    _last_activity = time.monotonic()


# ── CSRF and response headers (G-08, FR-UI-12) ─────────────────────────────

@app.before_request
def csrf_check():
    """Every state-changing request must carry the per-session CSRF value (runs after auth)."""
    if request.method in ("GET", "HEAD", "OPTIONS") or request.endpoint == "static":
        return
    want = session.get("csrf", "")
    sent = request.form.get("csrf_token", "")
    if not want or not secrets.compare_digest(sent, want):
        abort(403)


@app.context_processor
def _inject_csrf():
    def csrf_token() -> str:
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]
    return {"csrf_token": csrf_token}


@app.after_request
def _security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ── SIGTERM handler ────────────────────────────────────────────────────────

def _handle_sigterm(signum, frame):
    global _shutting_down, _grace_deadline
    log.info("SIGTERM received; entering 5-second grace window.")
    _shutting_down = True
    _grace_deadline = time.monotonic() + 5

    def _shutdown_after_grace():
        time.sleep(5)
        _delete_token()
        log.info("Grace window elapsed; shutting down.")
        os._exit(0)

    t = threading.Thread(target=_shutdown_after_grace, daemon=True)
    t.start()


signal.signal(signal.SIGTERM, _handle_sigterm)


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", config=cfg)


@app.route("/translate", methods=["POST"])
def translate():
    from engine.sanitiser import sanitise_text, enforce_token_cap
    from engine.translation_engine import TranslationEngine

    text = request.form.get("text", "")
    direction = request.form.get("direction", "en-la")
    level = request.form.get("level")
    barbarian = request.form.get("barbarian") == "1"

    clean, modified = sanitise_text(text)
    try:
        enforce_token_cap(clean)
    except ValueError as exc:
        return Response(str(exc), status=400, content_type="text/plain")

    # Engine is a module-level singleton initialised at startup
    engine = _get_translation_engine()
    try:
        level_int = int(level) if level and not barbarian else None
        result = engine.translate(clean, direction=direction, level=level_int, barbarian=barbarian,
                                  strict=_profile_strict())
    except Exception as exc:
        log.error("Translation error: %s", str(exc)[:64])
        return Response("Translation failed. See error log.", status=500, content_type="text/plain")

    return render_template(
        "result.html",
        source=clean,
        output=result.text,
        direction=direction,
        level=result.level,
        used_fallback=result.used_fallback,
        modified_by_sanitiser=modified,
    )


@app.route("/tts", methods=["POST"])
def tts():
    from engine.sanitiser import sanitise_text

    text = request.form.get("text", "")
    clean, _ = sanitise_text(text)

    tts_engine = _get_tts_engine()
    wav_bytes = tts_engine.synthesise(clean)

    if wav_bytes is None:
        return Response("Audio sent to playback device.", status=200, content_type="text/plain")

    filename = export_filename()
    return Response(
        wav_bytes,
        status=200,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "audio/wav",
        },
    )


@app.route("/pdf", methods=["POST"])
def pdf():
    from engine.pdf_factory import PdfFactory

    content_type = request.form.get("content_type", "workbook")
    source_text = request.form.get("text", "")

    factory = PdfFactory(
        paper_size=cfg.pdf_paper_size,
        margin_mm=cfg.pdf_margin_mm,
    )
    pdf_bytes = factory.generate(content_type=content_type, text=source_text)

    return Response(
        pdf_bytes,
        status=200,
        headers={
            "Content-Disposition": 'attachment; filename="workbook.pdf"',
            "Content-Type": "application/pdf",
        },
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    from engine.sanitiser import truncate_for_log
    import sqlite3
    from datetime import datetime, timezone

    slug = session.get("profile_slug", "default")
    rating = request.form.get("rating")  # "1" or "-1"
    source = request.form.get("source", "")
    output = request.form.get("output", "")
    direction = request.form.get("direction", "en-la")
    level = request.form.get("level", "4")

    if rating not in ("1", "-1"):
        return Response("Invalid rating.", status=400, content_type="text/plain")

    from engine.profile_manager import _db_path, _open_profile, _WRITE_LOCK

    db_path = _db_path(slug)
    if not db_path.exists():
        return Response("Profile not found.", status=404, content_type="text/plain")

    conn = _open_profile(db_path)
    with _WRITE_LOCK:
        conn.execute(
            "INSERT INTO translation_feedback "
            "(source_text, output_text, direction, level, rating, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                truncate_for_log(source),
                truncate_for_log(output),
                direction,
                level,
                int(rating),
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        conn.commit()
    conn.close()
    return Response("OK", status=200, content_type="text/plain")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profiles")
def profiles():
    from engine.profile_manager import CORRUPT_PROFILES, list_profiles
    return render_template("profiles.html", profiles=list_profiles(), corrupt=sorted(CORRUPT_PROFILES))


@app.route("/dashboard")
def dashboard():
    from engine.profile_manager import _db_path
    import sqlite3

    slug = session.get("profile_slug", "default")
    stats: dict = {}
    db = _db_path(slug)
    if db.exists():
        try:
            conn = sqlite3.connect(str(db))
            stats["translations"] = conn.execute(
                "SELECT COUNT(*) FROM translation_feedback"
            ).fetchone()[0]
            stats["sessions"] = conn.execute(
                "SELECT COUNT(*) FROM session_history"
            ).fetchone()[0]
            conn.close()
        except Exception:
            pass
    return render_template("dashboard.html", stats=stats)


@app.route("/set-level", methods=["POST"])
def set_level():
    from engine.profile_manager import update_profile_meta

    slug = session.get("profile_slug", "default")
    level_raw = request.form.get("level", "")
    try:
        level_int = int(level_raw)
        if level_int < 1 or level_int > 7:
            raise ValueError
    except ValueError:
        return Response("Invalid level.", status=400, content_type="text/plain")

    try:
        update_profile_meta(slug, selected_level=level_int)
    except Exception as exc:
        log.error("set_level error: %s", str(exc)[:64])
        return Response("Failed to update level.", status=500, content_type="text/plain")

    session["selected_level"] = level_int
    return redirect(url_for("index"))


@app.route("/profile/create", methods=["POST"])
def profile_create():
    from engine.profile_manager import create_profile
    from engine.sanitiser import sanitise_text

    display_name_raw = request.form.get("name", "")
    name, _ = sanitise_text(display_name_raw)
    name = name.strip()[:64]
    if not name:
        return Response("Profile name required.", status=400, content_type="text/plain")

    try:
        slug = create_profile(name)
    except Exception as exc:
        log.error("profile_create error: %s", str(exc)[:64])
        return Response("Failed to create profile.", status=500, content_type="text/plain")

    session["profile_slug"] = slug
    return redirect(url_for("profiles"))


@app.route("/profile/select", methods=["POST"])
def profile_select():
    from engine.profile_manager import list_profiles

    slug = request.form.get("slug", "")
    if not slug:
        return Response("Slug required.", status=400, content_type="text/plain")

    known = {p["slug"] for p in list_profiles()}
    if slug not in known:
        return Response("Profile not found.", status=404, content_type="text/plain")

    session["profile_slug"] = slug
    return redirect(url_for("index"))


@app.route("/profile/delete", methods=["POST"])
def profile_delete():
    from engine.profile_manager import delete_profile, list_profiles

    slug = request.form.get("slug", "")
    if not slug:
        return Response("Slug required.", status=400, content_type="text/plain")

    try:
        delete_profile(slug)
    except ValueError:
        return Response("Invalid profile identifier.", status=400, content_type="text/plain")
    except Exception as exc:
        log.error("profile_delete error: %s", str(exc)[:64])
        return Response("Failed to delete profile.", status=500, content_type="text/plain")

    if session.get("profile_slug") == slug:
        session.pop("profile_slug", None)

    return redirect(url_for("profiles"))


def _profile_strict() -> bool:
    """Profile error mode (PRD 4.8): True when the active profile is set to strict."""
    from engine.profile_manager import get_profile_meta
    try:
        return get_profile_meta(session.get("profile_slug", "default")).get("error_mode") == "strict"
    except Exception:
        return False


@app.route("/profile/rename", methods=["POST"])
def profile_rename():
    from engine.profile_manager import rename_profile
    from engine.sanitiser import sanitise_text

    slug = request.form.get("slug", "")
    name = sanitise_text(request.form.get("name", ""))[0].strip()[:64]
    if not slug or not name:
        return Response("Slug and name required.", status=400, content_type="text/plain")
    try:
        rename_profile(slug, name)
    except ValueError:
        return Response("Invalid profile identifier.", status=400, content_type="text/plain")
    except FileNotFoundError:
        return Response("Profile not found.", status=404, content_type="text/plain")
    except Exception as exc:
        log.error("profile_rename error: %s", str(exc)[:64])
        return Response("Failed to rename profile.", status=500, content_type="text/plain")
    return redirect(url_for("profiles"))


@app.route("/set-error-mode", methods=["POST"])
def set_error_mode():
    from engine.profile_manager import update_profile_meta

    mode = request.form.get("mode", "")
    if mode not in ("lenient", "strict"):
        return Response("Invalid mode.", status=400, content_type="text/plain")
    try:
        update_profile_meta(session.get("profile_slug", "default"), error_mode=mode)
    except Exception as exc:
        log.error("set_error_mode error: %s", str(exc)[:64])
        return Response("Failed to update error mode.", status=500, content_type="text/plain")
    return redirect(url_for("dashboard"))


@app.route("/import", methods=["GET", "POST"])
def corpus_import():
    from engine.importer import ImportRejected, import_corpus
    from engine.morphological import get_analyser

    if request.method == "GET":
        return render_template("import.html", summary=None, error=None)
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return render_template("import.html", summary=None, error="Choose a file."), 400
    try:
        summary = import_corpus(
            session.get("profile_slug", "default"), upload.stream, upload.filename, get_analyser(),
            confirmed_large=request.form.get("confirm_large") == "1", size_bytes=request.content_length,
        )
    except ImportRejected as exc:
        return render_template("import.html", summary=None, error=str(exc)), 400
    except ValueError:
        return render_template("import.html", summary=None, error="Invalid profile."), 400
    return render_template("import.html", summary=summary, error=None)


@app.route("/clear-telemetry", methods=["POST"])
def clear_telemetry():
    from engine.profile_manager import clear_telemetry as _clear

    slug = session.get("profile_slug", "default")
    try:
        _clear(slug)
    except Exception as exc:
        log.error("clear_telemetry error: %s", str(exc)[:64])
        return Response("Failed to clear telemetry.", status=500, content_type="text/plain")

    return redirect(url_for("dashboard"))


# ── Module-level engine singletons ─────────────────────────────────────────

_translation_engine: "TranslationEngine | None" = None
_tts_engine_instance: TtsEngine | None = None


def _get_translation_engine():
    global _translation_engine
    if _translation_engine is None:
        from engine.translation_engine import TranslationEngine
        _translation_engine = TranslationEngine(verify_checksum=True)
        try:
            _translation_engine.load()
        except Exception as exc:
            # Missing model or failed checksum: the engine stays unloaded and requests fail (G-02).
            log.error("Translation engine not loaded: %s", str(exc)[:64])
    return _translation_engine


def _get_tts_engine() -> TtsEngine:
    global _tts_engine_instance
    if _tts_engine_instance is None:
        _tts_engine_instance = TtsEngine(mode=cfg.tts_output_mode)
    return _tts_engine_instance


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    global _session_token

    _check_port_available(cfg.server_port)

    from engine.profile_manager import check_profiles
    corrupt = check_profiles()  # integrity check then migrate every existing profile (G-06)
    if corrupt:
        log.error("Corrupt profile database(s): %s. Restore from backup.", ",".join(corrupt)[:64])
        print(f"WARNING: integrity check failed for profile(s): {', '.join(corrupt)}. Restore from backup.", file=sys.stderr)

    token = _generate_token()
    _session_token = token
    _write_token(token)

    url = f"http://127.0.0.1:{cfg.server_port}/?token={token}"
    print(f"Ready: {url}", flush=True)
    log.info("Server starting on port %d", cfg.server_port)

    app.run(
        host=cfg.server_bind,
        port=cfg.server_port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )

    _delete_token()


if __name__ == "__main__":
    main()
