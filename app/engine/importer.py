"""
Corpus import (PRD 4.3, FR-ING-02/03/04).

Reads .txt, .md or .csv in sequential 50,000-character chunks, sanitises each chunk, and commits
each chunk to the profile database independently. A failure reports the chunk number and keeps
the chunks already committed.

What is stored: every distinct Latin-looking word in the chunk that the Whitaker dictionary does
not know is added to `word_friction` (direction 'la-en'). If the dictionary data is not loaded
nothing is recorded (we cannot tell known from unknown) and the result says so.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from typing import Iterator

from engine.sanitiser import _CHUNK_SIZE, _LARGE_FILE_WARN_BYTES, sanitise_csv_row, sanitise_text

ALLOWED_EXTENSIONS = (".txt", ".md", ".csv")
LARGE_FILE_BYTES = _LARGE_FILE_WARN_BYTES
_WORD_RE = re.compile(r"[A-Za-zāēīōūĀĒĪŌŪ]{2,}")


class ImportRejected(ValueError):
    """The file type or size is not acceptable (message is safe to show)."""


def check_upload(filename: str, size_bytes: int | None, confirmed_large: bool) -> str:
    """Return the lower-case extension, or raise ImportRejected."""
    name = (filename or "").lower()
    ext = next((e for e in ALLOWED_EXTENSIONS if name.endswith(e)), "")
    if not ext:
        raise ImportRejected("Only .txt, .md and .csv files can be imported.")
    if size_bytes is not None and size_bytes > LARGE_FILE_BYTES and not confirmed_large:
        raise ImportRejected(
            "This file is over 100 MB and will take a long time. Tick the confirmation box and submit again."
        )
    return ext


def iter_chunks(stream, ext: str) -> Iterator[str]:
    """Yield text chunks of at most about 50,000 characters."""
    text = io.TextIOWrapper(stream, encoding="utf-8", errors="replace", newline="")
    if ext == ".csv":
        buf, size = [], 0
        for row in csv.reader(text):
            line = " ".join(sanitise_csv_row(row))
            buf.append(line)
            size += len(line) + 1
            if size >= _CHUNK_SIZE:
                yield "\n".join(buf)
                buf, size = [], 0
        if buf:
            yield "\n".join(buf)
    else:
        while True:
            chunk = text.read(_CHUNK_SIZE)
            if not chunk:
                break
            # never split a word across two chunks: read on to the next whitespace (bounded)
            extra = 0
            while chunk[-1:] and not chunk[-1].isspace() and extra < 200:
                more = text.read(1)
                if not more:
                    break
                chunk += more
                extra += 1
            yield chunk


def import_corpus(slug: str, stream, filename: str, analyser, confirmed_large: bool = False, size_bytes: int | None = None) -> dict:
    """Import one file into the profile `slug`. Returns a summary dict."""
    from engine.profile_manager import _WRITE_LOCK, _db_path, _open_profile

    ext = check_upload(filename, size_bytes, confirmed_large)
    db = _db_path(slug)
    if not db.exists():
        raise ImportRejected("Profile not found.")
    summary = {"chunks_committed": 0, "words_recorded": 0, "failed_chunk": None, "dictionary_loaded": analyser.loaded}
    n = 0
    try:
        for raw in iter_chunks(stream, ext):
            n += 1
            clean, _ = sanitise_text(raw)
            unknown: dict[str, int] = {}
            if analyser.loaded:
                for w in _WORD_RE.findall(clean):
                    w = w.lower()
                    if not analyser.is_known(w):
                        unknown[w] = unknown.get(w, 0) + 1
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            conn = _open_profile(db)
            try:
                with _WRITE_LOCK:
                    for w, c in unknown.items():
                        cur = conn.execute(
                            "UPDATE word_friction SET fail_count = fail_count + ?, last_seen = ? "
                            "WHERE word = ? AND direction = 'la-en'", (c, now, w))
                        if cur.rowcount == 0:
                            conn.execute(
                                "INSERT INTO word_friction (word, direction, fail_count, last_seen) "
                                "VALUES (?, 'la-en', ?, ?)", (w, c, now))
                    conn.commit()
            finally:
                conn.close()
            summary["chunks_committed"] = n
            summary["words_recorded"] += len(unknown)
    except ImportRejected:
        raise
    except Exception as exc:  # report the chunk, keep what is committed
        summary["failed_chunk"] = n
        summary["error"] = str(exc)[:64]
    summary["chunks_total"] = n
    return summary
