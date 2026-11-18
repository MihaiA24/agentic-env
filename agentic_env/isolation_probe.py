"""Executed by the isolation checker inside the *same* policy as OMP."""

import errno
import json
import os
import socket
import subprocess
import sys
from pathlib import Path


def main() -> None:
    paths = json.loads(sys.argv[1])
    project = Path(paths["project"])
    assert (project / paths["input"]).read_text() == paths["nonce"]
    (project / paths["output"]).write_text(paths["nonce"])
    print("PASS project read/write", flush=True)

    def denied(label, operation):
        try:
            operation()
        except OSError as exc:
            assert exc.errno in (errno.EACCES, errno.EPERM, errno.ENETUNREACH), (label, exc)
        else:
            raise AssertionError(f"{label}: unexpectedly allowed")
        print(f"PASS {label}", flush=True)

    denied("outside content read", lambda: Path(paths["outside"]).read_bytes())
    denied("outside content write", lambda: Path(paths["outside"]).write_text("modified"))
    denied("symlink escape", lambda: (project / paths["symlink"]).read_bytes())
    def open_for_update(path):
        with Path(path).open("r+b"):
            pass
    denied("policy modification", lambda: open_for_update(paths["policy"]))
    denied("toolchain modification", lambda: open_for_update(paths["omp"]))

    for name in ("AGENTIC_DUMMY_SECRET", "OPENAI_API_KEY", "PROTON_PASS_CLI_PAT", "SSH_AUTH_SOCK",
                 "DBUS_SESSION_BUS_ADDRESS", "GPG_AGENT_INFO", "DISPLAY", "WAYLAND_DISPLAY"):
        assert name not in os.environ, f"inherited authority: {name}"
    print("PASS inherited environment filtering", flush=True)

    def connect_unix():
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(3)
            client.connect(paths["socket"])
    denied("host pathname socket inside writable project", connect_unix)

    for protocol, kind in (("TCP", socket.SOCK_STREAM), ("UDP", socket.SOCK_DGRAM)):
        def connect(kind=kind):
            with socket.socket(socket.AF_INET, kind) as client:
                client.settimeout(3)
                client.connect(("1.1.1.1", 443))
                client.send(b"sandbox-egress-probe")
        denied(f"direct {protocol} egress", connect)

    allowed = subprocess.run(
        ["/usr/bin/curl", "--silent", "--show-error", "--fail", "--max-time", "30",
         "https://registry.npmjs.org/-/ping"], capture_output=True, text=True,
    )
    assert allowed.returncode == 0, allowed.stderr
    json.loads(allowed.stdout)
    print("PASS allowlisted HTTPS", flush=True)
    rejected = subprocess.run(
        ["/usr/bin/curl", "--silent", "--show-error", "--max-time", "15", "https://example.org"],
        capture_output=True, text=True,
    )
    assert rejected.returncode != 0 and "403" in rejected.stderr, rejected.stderr
    print("PASS unapproved HTTPS denied by proxy", flush=True)
    bypass = subprocess.run(
        ["/usr/bin/curl", "--noproxy", "*", "--silent", "--show-error", "--max-time", "5",
         "--resolve", "example.org:443:1.1.1.1", "https://example.org"],
        capture_output=True, text=True,
    )
    assert bypass.returncode == 7, (bypass.returncode, bypass.stderr)
    print("PASS proxy bypass denied", flush=True)

    subprocess.run(["/usr/bin/true"], check=True)
    try:
        blocked = subprocess.run(["/usr/bin/mount", "--version"], capture_output=True, text=True)
    except PermissionError:
        pass
    else:
        assert blocked.returncode != 0, "canonical-path mount executed"
        assert any(word in blocked.stderr.lower() for word in ("denied", "blocked", "permission")), blocked.stderr
    print("PASS canonical-path command denial", flush=True)


if __name__ == "__main__":
    main()
