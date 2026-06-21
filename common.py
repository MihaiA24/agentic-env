#!/usr/bin/env python3
"""Shared helpers for agentic env scripts."""
from __future__ import annotations

import shutil
import subprocess
from typing import Iterable

from rich.console import Console
from rich.prompt import Confirm

console = Console()


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
    subprocess.run(list(cmd), check=True)


def run_shell(cmd: str) -> None:
    subprocess.run(["bash", "-lc", cmd], check=True)


def ok(message: str) -> None:
    console.print(f"[green]\u2713[/] {message}")


def skip(message: str) -> None:
    console.print(f"[yellow]-[/] {message}")


def warn(message: str) -> None:
    console.print(f"[red]![/] {message}")
