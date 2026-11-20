"""Container health check: connect to the configured port (replaces the fixed 8080, DOC-11)."""
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.config_loader import load_config  # noqa: E402


def main() -> int:
    port = load_config().server_port
    try:
        socket.create_connection(("127.0.0.1", port), 2).close()
        return 0
    except OSError:
        return 1


if __name__ == "__main__":
    sys.exit(main())
