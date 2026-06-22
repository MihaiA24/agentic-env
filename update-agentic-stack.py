#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Update already installed agent tooling."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from common import cmd_exists, info, ok, run, run_shell, set_verbose, skip, warn

AGENTMEMORY_NPM_PACKAGE = "@agentmemory/agentmemory"
UpdateAction = Callable[[], None]
UpdateStep = tuple[str, str, UpdateAction, str]


def _update(label: str, action: UpdateAction) -> bool:
    info(f"Updating {label}...")
    try:
        action()
    except FileNotFoundError:
        warn(f"{label}: required tool missing")
        return False
    except Exception:
        warn(f"{label}: update failed")
        return False
    ok(f"{label}: updated")
    return True


def _update_if_present(
    label: str,
    dependency: str,
    action: UpdateAction,
    *,
    missing_message: str,
) -> bool:
    if not cmd_exists(dependency):
        skip(missing_message)
        return True
    return _update(label, action)


def _update_hermes() -> None:
    run(["hermes", "update", "--yes"])


def _update_omp() -> None:
    run(["omp", "update"])


def _update_claude() -> None:
    run(["claude", "update"])


def _update_codebase_memory() -> None:
    run(["codebase-memory-mcp", "update"])


def _update_lean_ctx() -> None:
    run(["lean-ctx", "update"])


UPDATE_STEPS: tuple[UpdateStep, ...] = (
    ("Hermes Agent", "hermes", _update_hermes, "Hermes Agent: not installed"),
    ("OMP / Oh My Pi", "omp", _update_omp, "OMP / Oh My Pi: not installed"),
    ("Claude Code", "claude", _update_claude, "Claude Code: not installed"),
    (
        "codebase-memory-mcp",
        "codebase-memory-mcp",
        _update_codebase_memory,
        "codebase-memory-mcp: not installed",
    ),
    ("lean-ctx", "lean-ctx", _update_lean_ctx, "lean-ctx: not installed"),
)


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update installed agentic tooling")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


def _update_codex() -> bool:
    if not cmd_exists("codex"):
        skip("OpenAI Codex CLI: not installed")
        return True
    if not cmd_exists("npm"):
        warn("OpenAI Codex CLI: npm not installed")
        return False
    return _update(
        "OpenAI Codex CLI",
        lambda: run(["npm", "update", "-g", "@openai/codex"]),
    )


def _update_agentmemory() -> bool:
    if not cmd_exists("agentmemory"):
        skip("agentmemory: not installed")
        return True
    if not cmd_exists("npm"):
        warn("agentmemory: npm not installed")
        return False

    # agentmemory's own `upgrade` command prompts to re-run the pinned
    # iii-engine installer and can mutate the current workspace. The stack
    # updater only refreshes the globally installed CLI package.
    return _update(
        "agentmemory CLI",
        lambda: run(["npm", "update", "-g", AGENTMEMORY_NPM_PACKAGE]),
    )


def _update_skills() -> bool:
    if cmd_exists("npm") and cmd_exists("skills"):
        return _update(
            "skills CLI",
            lambda: run(["skills", "update", "-g", "-y"]),
        )
    if cmd_exists("npm"):
        return _update(
            "skills CLI",
            lambda: run_shell("npx --yes skills@latest update -g -y"),
        )
    skip("skills CLI: npm/command missing")
    return True


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)

    ok_all = True
    for label, binary, action, missing in UPDATE_STEPS:
        ok_all = (
            _update_if_present(label, binary, action, missing_message=missing)
            and ok_all
        )

    ok_all = _update_codex() and ok_all
    ok_all = _update_agentmemory() and ok_all
    ok_all = _update_skills() and ok_all

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())