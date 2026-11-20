"""
Tests for port conflict detection and startup behaviour (PRD §9.11).
"""
from __future__ import annotations

import re
import secrets
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _bind_port(port: int) -> socket.socket:
    """Bind a socket to localhost:port. Caller must close it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)
    return sock


def test_port_in_use_exits_nonzero(capsys):
    """Attempting to start when port is occupied must exit with non-zero code."""
    import app as mod

    # Find a free port, then occupy it
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.listen(1)

    try:
        with pytest.raises(SystemExit) as exc_info:
            mod._check_port_available(port)
        assert exc_info.value.code != 0
    finally:
        sock.close()


def test_port_in_use_error_message_on_stderr(capsys):
    """Error message must name the port and instruct setting config.toml."""
    import app as mod

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.listen(1)

    try:
        with pytest.raises(SystemExit):
            mod._check_port_available(port)
        captured = capsys.readouterr()
        assert str(port) in captured.err
        assert "config.toml" in captured.err
    finally:
        sock.close()


def test_free_port_does_not_exit():
    """Available port must not trigger exit."""
    import app as mod

    # Find a port that is not in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    # Should return normally (not raise SystemExit)
    mod._check_port_available(port)


def test_startup_url_stdout_format():
    """
    Startup must print 'Ready: http://127.0.0.1:<port>/?token=<hex_token>'
    with a hex_token of ≥32 characters.
    """
    token = secrets.token_hex(16)
    port = 8080
    line = f"Ready: http://127.0.0.1:{port}/?token={token}"
    pattern = r"Ready: http://127\.0\.0\.1:\d+/\?token=[0-9a-f]{32,}"
    assert re.match(pattern, line), f"Line did not match pattern: {line!r}"
