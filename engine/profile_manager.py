"""
User profile management.

Profiles are isolated SQLite databases stored at:
  ~/.airgap-translator/profiles/<slug>.db

Supports create, select, rename, delete (with secure erase).
"""
from __future__ import annotations

import os
import platform
import re
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from engine.db_migrate import run_migrations

_PROFILES_DIR_DEFAULT = Path.home() / ".airgap-translator" / "profiles"
_WRITE_LOCK = threading.Lock()


def _profiles_dir() -> Path:
    d = _PROFILES_DIR_DEFAULT
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]", "_", name.lower().strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:64] or "profile"


def _db_path(slug: str) -> Path:
    return _profiles_dir() / f"{slug}.db"


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _open_profile(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_profile(display_name: str) -> str:
    """Create a new profile; returns its slug."""
    slug = _slugify(display_name)
    db_path = _db_path(slug)
    if db_path.exists():
        raise ValueError(f"Profile '{slug}' already exists.")
    run_migrations(db_path)
    db_path.chmod(0o600)
    conn = _open_profile(db_path)
    with _WRITE_LOCK:
        conn.execute(
            "INSERT INTO profile_meta (id, profile_slug, display_name, created_at) "
            "VALUES (1, ?, ?, ?)",
            (slug, display_name, _now_utc()),
        )
        conn.commit()
    conn.close()
    return slug


def list_profiles() -> list[dict]:
    """Return list of {slug, display_name, last_login} for all profiles."""
    profiles = []
    for db_file in sorted(_profiles_dir().glob("*.db")):
        slug = db_file.stem
        try:
            conn = sqlite3.connect(str(db_file))
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT display_name, last_login FROM profile_meta LIMIT 1"
            ).fetchone()
            conn.close()
            if row:
                profiles.append(
                    {
                        "slug": slug,
                        "display_name": row["display_name"],
                        "last_login": row["last_login"],
                    }
                )
        except sqlite3.Error:
            profiles.append({"slug": slug, "display_name": slug, "last_login": None})
    return profiles


def rename_profile(slug: str, new_display_name: str) -> None:
    db_path = _db_path(slug)
    if not db_path.exists():
        raise FileNotFoundError(f"Profile '{slug}' not found.")
    conn = _open_profile(db_path)
    with _WRITE_LOCK:
        conn.execute(
            "UPDATE profile_meta SET display_name = ? WHERE id = 1",
            (new_display_name,),
        )
        conn.commit()
    conn.close()


def delete_profile(slug: str) -> None:
    """Securely erase and delete the profile database."""
    db_path = _db_path(slug)
    if not db_path.exists():
        raise FileNotFoundError(f"Profile '{slug}' not found.")
    _secure_erase(db_path)


def _secure_erase(path: Path) -> None:
    if platform.system() == "Linux":
        try:
            subprocess.run(["shred", "-uz", str(path)], check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
    # Fallback: overwrite with null bytes then remove
    size = path.stat().st_size
    with open(path, "wb") as f:
        f.write(b"\x00" * size)
    os.remove(path)


def get_profile_meta(slug: str) -> dict:
    db_path = _db_path(slug)
    if not db_path.exists():
        raise FileNotFoundError(f"Profile '{slug}' not found.")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM profile_meta LIMIT 1").fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Profile '{slug}' has no metadata row.")
    return dict(row)


def update_profile_meta(slug: str, **fields) -> None:
    allowed = {
        "selected_level", "barbarian_mode", "tts_output_mode", "error_mode", "last_login"
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    db_path = _db_path(slug)
    conn = _open_profile(db_path)
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with _WRITE_LOCK:
        conn.execute(
            f"UPDATE profile_meta SET {set_clause} WHERE id = 1",
            list(updates.values()),
        )
        conn.commit()
    conn.close()


def clear_telemetry(slug: str) -> None:
    """Permanently delete all telemetry for the active profile."""
    db_path = _db_path(slug)
    conn = _open_profile(db_path)
    with _WRITE_LOCK:
        conn.execute("DELETE FROM session_history")
        conn.execute("DELETE FROM word_friction")
        conn.execute("DELETE FROM translation_feedback")
        conn.execute("DELETE FROM proficiency")
        conn.execute("DELETE FROM error_records")
        conn.commit()
    conn.close()
