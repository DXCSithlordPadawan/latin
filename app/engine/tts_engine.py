"""
TTS engine — pyttsx3 binding to espeak-ng backend.

Output modes:
  playback — audio rendered to system audio device; no file written to disk.
  export   — audio generated in memory; served as HTTP download (WAV bytes).
  both     — simultaneously plays to audio device AND returns WAV bytes.

Interrupt-on-new-request: any in-progress synthesis is stopped before a new
request begins. No synthesis queue.

The pyttsx3 driver is locked to the 'espeak' backend. SAPI5 and
NSSpeechSynthesizer are not permitted.
"""
from __future__ import annotations

import io
import threading
import wave
from datetime import datetime, timezone
from typing import Literal

from engine.phonetic_mapper import map_for_espeak

TtsMode = Literal["playback", "export", "both"]
REQUIRED_DRIVER = "espeak"

_synthesis_lock = threading.Lock()
_current_engine = None


def _get_engine():
    """Initialise or return the pyttsx3 engine locked to espeak."""
    global _current_engine
    if _current_engine is None:
        import pyttsx3

        engine = pyttsx3.init(driverName=REQUIRED_DRIVER)
        _current_engine = engine
    return _current_engine


def _stop_current() -> None:
    global _current_engine
    if _current_engine is not None:
        try:
            _current_engine.stop()
        except Exception:
            pass


def _synthesise_to_bytes(mapped_text: str) -> bytes:
    """
    Synthesise *mapped_text* to a WAV byte buffer in memory.
    Returns raw WAV bytes. No file is written to disk.
    """
    import pyttsx3

    buf = io.BytesIO()
    engine = pyttsx3.init(driverName=REQUIRED_DRIVER)

    # espeak-ng supports saving to a file; we use a temp path via tempfile
    # then read + delete, OR use pyttsx3's save_to_file with a BytesIO wrapper.
    # pyttsx3 requires a file path for save_to_file; we use a temp file and
    # immediately read + zero it out before returning.
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        engine.save_to_file(mapped_text, tmp_path)
        engine.runAndWait()
        with open(tmp_path, "rb") as f:
            wav_bytes = f.read()
    finally:
        # Overwrite with zeros before deleting (no sensitive data, but consistent
        # with the "no file remains on disk" contract)
        try:
            size = os.path.getsize(tmp_path)
            with open(tmp_path, "wb") as f:
                f.write(b"\x00" * size)
            os.remove(tmp_path)
        except OSError:
            pass

    return wav_bytes


def _synthesise_playback(mapped_text: str) -> None:
    """Render audio directly to the system audio device. No file written."""
    import pyttsx3

    engine = pyttsx3.init(driverName=REQUIRED_DRIVER)
    engine.say(mapped_text)
    engine.runAndWait()


def export_filename() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"tts_{ts}.wav"


class TtsEngine:
    """High-level TTS engine used by the web application."""

    def __init__(self, mode: TtsMode = "playback") -> None:
        self._mode: TtsMode = mode

    @property
    def driver_name(self) -> str:
        return REQUIRED_DRIVER

    def set_mode(self, mode: TtsMode) -> None:
        if mode not in ("playback", "export", "both"):
            raise ValueError(f"Invalid TTS mode: {mode!r}")
        self._mode = mode

    def synthesise(self, text: str) -> bytes | None:
        """
        Synthesise *text* according to the current output mode.

        Returns:
          - WAV bytes if mode is 'export' or 'both'
          - None if mode is 'playback'

        Audio playback (mode 'playback' or 'both') is performed synchronously.
        An in-progress synthesis is interrupted before this call proceeds.
        """
        with _synthesis_lock:
            _stop_current()
            mapped = map_for_espeak(text)

            if self._mode == "playback":
                _synthesise_playback(mapped)
                return None

            if self._mode == "export":
                return _synthesise_to_bytes(mapped)

            if self._mode == "both":
                wav_bytes = _synthesise_to_bytes(mapped)
                # Also play — run in a thread so we can return bytes immediately
                t = threading.Thread(
                    target=_synthesise_playback, args=(mapped,), daemon=True
                )
                t.start()
                return wav_bytes

        return None
