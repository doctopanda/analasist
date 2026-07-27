from __future__ import annotations

import os
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"Abriendo POPIS 5.0 en {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ROOT / "app.py"),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.call(cmd, cwd=str(ROOT), env=os.environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
