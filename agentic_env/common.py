#!/usr/bin/env python3
"""Shared helpers for agentic env scripts."""
from __future__ import annotations

import shutil
import subprocess
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


def info(message: str) -> None:
    console.print(f"[blue]•[/] {message}")


def ok(message: str) -> None:
    console.print(f"[green]\u2713[/] {message}")


def skip(message: str) -> None:
    console.print(f"[yellow]-[/] {message}")


def warn(message: str) -> None:
    console.print(f"[red]![/] {message}")
