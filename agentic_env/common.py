#!/usr/bin/env python3
"""Shared helpers for agentic env scripts."""

import contextlib
import hashlib
import io
import os
import shutil
import tarfile
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable

from rich.console import Console
from rich.prompt import Confirm

console = Console()
_VERBOSE_OUTPUT = False


def set_verbose(enabled: bool) -> None:
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = bool(enabled)


def _run(
    cmd: Iterable[str], cwd: str | None = None
) -> subprocess.CompletedProcess[str]:
    command = list(cmd)
    if _VERBOSE_OUTPUT:
        result = subprocess.run(command, check=False, text=True, cwd=cwd)
    else:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
        )

    if result.returncode != 0:
        if result.stdout:
            warn(result.stdout.rstrip())
        if result.stderr:
            warn(result.stderr.rstrip())
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout, stderr=result.stderr
        )
    return result


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def cmd_works(
    name: str, args: Iterable[str] = ("--help",), timeout_sec: int = 2
) -> bool:
    try:
        subprocess.run(
            [name, *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_sec,
        )
        return True
    except Exception:
        return False


def cmd_version_matches(
    name: str, fragments: Iterable[str], args: Iterable[str] = ("--version",)
) -> bool:
    try:
        result = subprocess.run(
            [name, *args],
            check=True,
            capture_output=True,
            text=True,
            # Cold-start venv CLIs (hermes) need ~10s on first run.
            timeout=60,
        )
    except Exception:
        return False
    output = result.stdout + result.stderr
    return all(fragment in output for fragment in fragments)


def ask(prompt: str, *, default: bool, non_interactive: bool) -> bool:
    if non_interactive:
        return default
    return Confirm.ask(f"[cyan]?[/] {prompt}", default=default)


def run(cmd: Iterable[str]) -> None:
    _run(cmd)


def run_shell(cmd: str) -> None:
    _run(["bash", "-lc", cmd])


def _is_valid_sha256(value: str | None) -> bool:
    if not value:
        return False
    return len(value) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in value)


def _fetch_url(url: str, timeout_sec: int) -> bytes:
    # Some CDNs (omp.sh, claude.ai) reject the default Python-urllib UA with 403.
    request = urllib.request.Request(url, headers={"User-Agent": "agentic-env/1.0"})
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        return response.read()


def run_remote_script(
    *,
    label: str,
    url: str,
    expected_sha256: str | None,
    interpreter: str,
    interpreter_args: list[str] | None = None,
    timeout_sec: int = 30,
) -> bool:
    """Download and execute a remote installer script with optional checksum pinning."""
    try:
        payload = _fetch_url(url, timeout_sec)
    except Exception as exc:
        warn(f"{label}: failed to download installer script: {exc}")
        return False

    if expected_sha256 is not None:
        if not _is_valid_sha256(expected_sha256):
            warn(f"{label}: invalid sha256 checksum in contract: {expected_sha256}")
            return False
        actual = hashlib.sha256(payload).hexdigest()
        if actual.lower() != expected_sha256.lower():
            warn(f"{label}: installer checksum mismatch for {url}")
            warn(f"{label}: expected {expected_sha256}, got {actual}")
            return False

    fd, script_path = tempfile.mkstemp(prefix="agentic-install-", suffix=".sh")
    script_command = [interpreter, script_path]
    if interpreter_args:
        script_command.extend(interpreter_args)

    try:
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
        os.chmod(script_path, 0o700)
        # Neutral cwd: installers must not inherit our project context
        # (e.g. Hermes runs `uv venv --python 3.11`, which refuses under a
        # pyproject that pins requires-python >= 3.12).
        _run(script_command, cwd=str(Path.home()))
    except subprocess.CalledProcessError:
        warn(f"{label}: installer script execution failed")
        return False
    except Exception as exc:
        warn(f"{label}: installer script execution failed: {exc}")
        return False
    finally:
        with contextlib.suppress(OSError):
            os.remove(script_path)

    return True


def install_pinned_binary_archive(
    *, label: str, binary: str, url: str, expected_sha256: str, timeout_sec: int = 60
) -> bool:
    """Install one checksum-pinned binary from a release tarball."""
    try:
        payload = _fetch_url(url, timeout_sec)
    except Exception as exc:
        warn(f"{label}: failed to download release: {exc}")
        return False

    actual = hashlib.sha256(payload).hexdigest()
    if (
        not _is_valid_sha256(expected_sha256)
        or actual.lower() != expected_sha256.lower()
    ):
        warn(f"{label}: release checksum mismatch for {url}")
        warn(f"{label}: expected {expected_sha256}, got {actual}")
        return False

    install_dir = Path.home() / ".local" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)
    destination = install_dir / binary
    temporary: str | None = None
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            members = [
                member
                for member in archive.getmembers()
                if member.isfile() and PurePosixPath(member.name).name == binary
            ]
            if len(members) != 1:
                warn(
                    f"{label}: release archive must contain exactly one {binary} binary"
                )
                return False
            source = archive.extractfile(members[0])
            if source is None:
                warn(f"{label}: cannot read {binary} from release archive")
                return False
            fd, temporary = tempfile.mkstemp(prefix=f".{binary}.", dir=install_dir)
            with os.fdopen(fd, "wb") as target:
                shutil.copyfileobj(source, target)
        os.chmod(temporary, 0o755)
        os.replace(temporary, destination)
        temporary = None
    except Exception as exc:
        warn(f"{label}: failed to install release: {exc}")
        return False
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.remove(temporary)

    return True


def info(message: str) -> None:
    console.print(f"[blue]•[/] {message}")


def ok(message: str) -> None:
    console.print(f"[green]\u2713[/] {message}")


def skip(message: str) -> None:
    console.print(f"[yellow]-[/] {message}")


def warn(message: str) -> None:
    console.print(f"[red]![/] {message}")
