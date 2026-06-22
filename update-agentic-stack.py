#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Update already installed agent tooling."""
from __future__ import annotations

import argparse
import sys

from common import cmd_exists, info, ok, run, set_verbose, skip, warn

AGENTMEMORY_NPM_PACKAGE = "@agentmemory/agentmemory"
UPDATE_STEPS: tuple[tuple[str, str, list[str], str], ...] = (
    (
        "Hermes Agent",
        "hermes",
        ["hermes", "update", "--yes"],
        "Hermes Agent: not installed",
    ),
    ("OMP / Oh My Pi", "omp", ["omp", "update"], "OMP / Oh My Pi: not installed"),
    ("Claude Code", "claude", ["claude", "update"], "Claude Code: not installed"),
    (
        "codebase-memory-mcp",
        "codebase-memory-mcp",
        ["codebase-memory-mcp", "update"],
        "codebase-memory-mcp: not installed",
    ),
    ("lean-ctx", "lean-ctx", ["lean-ctx", "update"], "lean-ctx: not installed"),
)


def _update(label: str, command: list[str]) -> bool:
    info(f"Updating {label}...")
    try:
        run(command)
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
    command: list[str],
    *,
    missing_message: str,
) -> bool:
    if not cmd_exists(dependency):
        skip(missing_message)
        return True
    return _update(label, command)


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
    return _update("OpenAI Codex CLI", ["npm", "update", "-g", "@openai/codex"])


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
        ["npm", "update", "-g", AGENTMEMORY_NPM_PACKAGE],
    )


def _update_skills() -> bool:
    if cmd_exists("skills"):
        return _update("skills CLI", ["skills", "update", "-g", "-y"])
    if cmd_exists("npm"):
        return _update(
            "skills CLI",
            ["npx", "--yes", "skills@latest", "update", "-g", "-y"],
        )
    skip("skills CLI: npm/command missing")
    return True


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)

    ok_all = True
    for label, binary, command, missing in UPDATE_STEPS:
        ok_all = (
            _update_if_present(label, binary, command, missing_message=missing)
            and ok_all
        )

    ok_all = _update_codex() and ok_all
    ok_all = _update_agentmemory() and ok_all
    ok_all = _update_skills() and ok_all

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
