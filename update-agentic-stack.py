#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Update already installed agent tooling."""
from __future__ import annotations

import argparse
import sys

from common import cmd_exists, run, run_shell, ok, set_verbose, skip, warn


def _update(label: str, action) -> bool:
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


def _update_if_present(label: str, dependency: str, action, *, missing_message: str) -> None:
    if cmd_exists(dependency):
        _update(label, action)
    else:
        skip(missing_message)


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update installed agentic tooling")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)
    for label, binary, action, missing in (
        ("Hermes Agent", "hermes", lambda: run(["hermes", "update"]), "Hermes Agent: not installed"),
        ("OMP / Oh My Pi", "omp", lambda: run(["omp", "update"]), "OMP / Oh My Pi: not installed"),
        ("Claude Code", "claude", lambda: run_shell("curl -fsSL https://claude.ai/install.sh | bash"), "Claude Code: not installed"),
        ("codebase-memory-mcp", "codebase-memory-mcp", lambda: run(["codebase-memory-mcp", "update"]), "codebase-memory-mcp: not installed"),
        ("lean-ctx", "lean-ctx", lambda: run(["lean-ctx", "update"]), "lean-ctx: not installed"),
        ("agentmemory", "agentmemory", lambda: run(["agentmemory", "upgrade"]), "agentmemory: not installed"),
    ):
        _update_if_present(label, binary, action, missing_message=missing)

    if cmd_exists("codex"):
        if cmd_exists("npm"):
            _update("OpenAI Codex CLI", lambda: run(["npm", "update", "-g", "@openai/codex"]))
        else:
            skip("OpenAI Codex CLI: npm not installed")
    else:
        skip("OpenAI Codex CLI: not installed")

    if cmd_exists("npm") and cmd_exists("skills"):
        _update("skills CLI", lambda: run(["skills", "update", "-g", "-y"]))
    elif cmd_exists("npm"):
        _update("skills CLI", lambda: run_shell("npx --yes skills@latest update -g -y"))
    else:
        skip("skills CLI: npm/command missing")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())