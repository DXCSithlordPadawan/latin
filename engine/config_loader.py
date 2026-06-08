"""
Config loader — reads config.toml and validates all keys.

Invalid or out-of-range values are silently reset to defaults.
A WARN entry is written to the logger for each invalid value.
If config.toml is absent or unparseable, all defaults are applied.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # fallback wheel
    except ImportError:
        tomllib = None  # type: ignore

log = logging.getLogger("config")

CONFIG_PATH_DEFAULT = Path(__file__).parent.parent / "config" / "config.toml"


@dataclass
class AppConfig:
    server_port: int = 8080
    server_session_timeout_minutes: int = 60
    pdf_paper_size: str = "A4"
    pdf_margin_mm: int = 20
    tts_output_mode: str = "playback"


_DEFAULTS = AppConfig()

_VALIDATORS: dict[str, tuple[Any, Any]] = {
    # key: (type_or_none, validator_fn_or_none)
}


def _validate_port(v: Any) -> int:
    v = int(v)
    if not (1024 <= v <= 65535):
        raise ValueError(f"port must be 1024–65535, got {v}")
    return v


def _validate_session_timeout(v: Any) -> int:
    v = int(v)
    if not (5 <= v <= 1440):
        raise ValueError(f"session_timeout_minutes must be 5–1440, got {v}")
    return v


def _validate_paper_size(v: Any) -> str:
    v = str(v)
    if v not in ("A4", "Letter"):
        raise ValueError(f"pdf.paper_size must be 'A4' or 'Letter', got {v!r}")
    return v


def _validate_margin_mm(v: Any) -> int:
    v = int(v)
    if not (10 <= v <= 40):
        raise ValueError(f"pdf.margin_mm must be 10–40, got {v}")
    return v


def _validate_tts_mode(v: Any) -> str:
    v = str(v)
    if v not in ("playback", "export", "both"):
        raise ValueError(f"tts.output_mode must be 'playback', 'export', or 'both', got {v!r}")
    return v


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or CONFIG_PATH_DEFAULT
    raw: dict = {}

    if path.exists():
        try:
            if tomllib is None:
                raise ImportError("tomllib not available")
            with open(path, "rb") as f:
                raw = tomllib.load(f)
        except Exception as exc:
            log.warning("WARN: config.toml could not be parsed (%s); using defaults.", exc)

    cfg = AppConfig()

    def get(section: str, key: str, validator, default):
        val = raw.get(section, {}).get(key, default)
        try:
            return validator(val)
        except Exception as exc:
            log.warning(
                "WARN: config key %s.%s value %r is invalid; using default %r. (%s)",
                section, key, val, default, exc,
            )
            return default

    cfg.server_port = get("server", "port", _validate_port, _DEFAULTS.server_port)
    cfg.server_session_timeout_minutes = get(
        "server", "session_timeout_minutes",
        _validate_session_timeout, _DEFAULTS.server_session_timeout_minutes
    )
    cfg.pdf_paper_size = get("pdf", "paper_size", _validate_paper_size, _DEFAULTS.pdf_paper_size)
    cfg.pdf_margin_mm = get("pdf", "margin_mm", _validate_margin_mm, _DEFAULTS.pdf_margin_mm)
    cfg.tts_output_mode = get("tts", "output_mode", _validate_tts_mode, _DEFAULTS.tts_output_mode)

    return cfg
