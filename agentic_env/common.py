#!/usr/bin/env python3
"""Shared helpers for agentic env scripts."""

import contextlib
import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
from typing import Iterable

from rich.console import Console
from rich.prompt import Confirm

console = Console()
_VERBOSE_OUTPUT = False


def set_verbose(enabled: bool) -> None:
    global _VERBOSE_OUTPUT
    _VERBOSE_OUTPUT = bool(enabled)


def _run(cmd: Iterable[str]) -> subprocess.CompletedProcess[str]:
    command = list(cmd)
    if _VERBOSE_OUTPUT:
        result = subprocess.run(command, check=False, text=True)
    else:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
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


def cmd_works(name: str, args: Iterable[str] = ("--help",), timeout_sec: int = 2) -> bool:
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
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = response.read()
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
        _run(script_command)
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


def info(message: str) -> None:
    console.print(f"[blue]•[/] {message}")


def ok(message: str) -> None:
    console.print(f"[green]\u2713[/] {message}")


def skip(message: str) -> None:
    console.print(f"[yellow]-[/] {message}")


def warn(message: str) -> None:
    console.print(f"[red]![/] {message}")

