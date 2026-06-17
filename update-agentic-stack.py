#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Update already installed agent tooling."""
from __future__ import annotations

import argparse
import sys

from common import cmd_exists, run, run_shell, ok, skip, warn


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


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Update installed agentic tooling").parse_args(argv or sys.argv[1:])

    if cmd_exists("hermes"):
        _update("Hermes Agent", lambda: run(["hermes", "update"]))
    else:
        skip("Hermes Agent: not installed")

    if cmd_exists("omp"):
        if cmd_exists("bun"):
            _update("OMP / Oh My Pi", lambda: run(["bun", "install", "-g", "@oh-my-pi/pi-coding-agent"]))
        else:
            _update("OMP / Oh My Pi", lambda: run_shell("curl -fsSL https://omp.sh/install | sh"))
    else:
        skip("OMP / Oh My Pi: not installed")

    if cmd_exists("codex"):
        if cmd_exists("npm"):
            _update("OpenAI Codex CLI", lambda: run(["npm", "update", "-g", "@openai/codex"]))
        else:
            skip("OpenAI Codex CLI: npm not installed")
    else:
        skip("OpenAI Codex CLI: not installed")

    if cmd_exists("claude"):
        _update("Claude Code", lambda: run_shell("curl -fsSL https://claude.ai/install.sh | bash"))
    else:
        skip("Claude Code: not installed")

    if cmd_exists("npm") and cmd_exists("skills"):
        _update("skills CLI", lambda: run(["skills", "update", "-g", "-y"]))
    elif cmd_exists("npm"):
        _update("skills CLI", lambda: run_shell("npx --yes skills@latest update -g -y"))
    else:
        skip("skills CLI: npm/command missing")

    if cmd_exists("codebase-memory-mcp"):
        _update("codebase-memory-mcp", lambda: run(["codebase-memory-mcp", "update"]))
    else:
        skip("codebase-memory-mcp: not installed")

    if cmd_exists("lean-ctx"):
        _update("lean-ctx", lambda: run(["lean-ctx", "update"]))
    else:
        skip("lean-ctx: not installed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
