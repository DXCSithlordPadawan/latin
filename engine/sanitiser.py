"""
Input sanitisation module.

Strips null bytes, C0/C1 control characters, overlong UTF-8 sequences,
and shell metacharacters from all user-supplied strings.

Hard cap: 512 tokens (whitespace-split approximation). Inputs exceeding the
cap are rejected (ValueError) before inference.

CSV import: all cell values are cast to string literals; no formula evaluation.
"""
from __future__ import annotations

import re
import unicodedata

# Shell metacharacters that must never appear in sanitised text
_SHELL_META_RE = re.compile(r"[;&|`$<>\\]")

# Control characters: C0 (U+0000–U+001F) and C1 (U+0080–U+009F), plus DEL (U+007F)
# We keep TAB (U+0009), LF (U+000A), CR (U+000D) as they are legitimate whitespace.
_CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f]", re.UNICODE
)

_TOKEN_HARD_CAP = 512
_CHUNK_SIZE = 50_000          # characters per corpus import chunk
_LARGE_FILE_WARN_BYTES = 100 * 1024 * 1024  # 100 MB


def sanitise_text(text: str) -> tuple[str, bool]:
    """
    Sanitise a user-supplied string.

    Returns (sanitised_text, was_modified).
    Raises TypeError if input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    # Normalise to NFC to eliminate overlong / decomposed form surprises
    try:
        text = unicodedata.normalize("NFC", text)
    except (TypeError, ValueError):
        text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    original = text

    # Strip C0/C1 control characters (keep TAB/LF/CR)
    text = _CONTROL_RE.sub("", text)

    # Strip shell metacharacters
    text = _SHELL_META_RE.sub("", text)

    # Strip null bytes defensively (belt-and-braces — the regex above covers \x00)
    text = text.replace("\x00", "")

    was_modified = text != original
    return text, was_modified


def check_token_count(text: str) -> int:
    """Return approximate whitespace-split token count."""
    return len(text.split())


def enforce_token_cap(text: str) -> str:
    """
    Raise ValueError if text exceeds 512 tokens.

    The error message includes the actual token count so the UI can display it.
    """
    count = check_token_count(text)
    if count > _TOKEN_HARD_CAP:
        raise ValueError(
            f"Input exceeds the 512-token hard cap ({count} tokens). "
            "Please shorten your input and try again."
        )
    return text


def sanitise_and_enforce(text: str) -> str:
    """Sanitise then enforce the token cap. Returns the clean text."""
    clean, _ = sanitise_text(text)
    return enforce_token_cap(clean)


def sanitise_csv_row(row: list) -> list[str]:
    """Cast every CSV cell to a string literal; no formula evaluation."""
    result = []
    for cell in row:
        cell_str = str(cell)
        # Strip leading = + - @ which are formula initiators in spreadsheet apps
        if cell_str and cell_str[0] in ("=", "+", "-", "@"):
            cell_str = "'" + cell_str
        clean, _ = sanitise_text(cell_str)
        result.append(clean)
    return result


def iter_corpus_chunks(text: str):
    """Yield successive 50,000-character chunks from a corpus import string."""
    total = len(text)
    for start in range(0, total, _CHUNK_SIZE):
        yield text[start : start + _CHUNK_SIZE]


def truncate_for_log(value: str, max_len: int = 64) -> str:
    """Truncate a user string for safe inclusion in log output."""
    if len(value) <= max_len:
        return value
    return value[:max_len] + "[…redacted]"
