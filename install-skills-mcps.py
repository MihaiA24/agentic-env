#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Install mattpocock skills and MCP tooling."""

from __future__ import annotations

import argparse
import sys

from common import ask, cmd_exists, ok, run, run_shell, skip, warn


def _install_skills(_: bool) -> bool:
    if not cmd_exists("npm"):
        warn("npm is required to install mattpocock skills")
        return False

    run(["npx", "--yes", "skills@latest", "add", "mattpocock/skills"])
    ok("mattpocock skills: installed")
    return True


def _install_codebase_memory(with_ui: bool) -> bool:
    if not cmd_exists("curl"):
        warn("curl is required to install codebase-memory-mcp")
        return False

    base = (
        "https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh"
    )
    run_shell(f"curl -fsSL {base} | bash" + (" -s -- --ui" if with_ui else ""))
    ok("codebase-memory-mcp: installed" + (" (with UI)" if with_ui else ""))
    return True


def _install_lean_ctx(non_interactive: bool) -> bool:
    if not cmd_exists("curl"):
        warn("curl is required to install lean-ctx")
        return False

    run_shell("curl -fsSL https://leanctx.com/install.sh | sh")
    ok("lean-ctx: installed")

    if cmd_exists("lean-ctx") and ask(
        "Run lean-ctx setup now", default=True, non_interactive=non_interactive
    ):
        run(["lean-ctx", "setup"])
        ok("lean-ctx: setup run")
    else:
        skip("lean-ctx setup: skipped")

    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install mattpocock skills and MCP tools"
    )
    parser.add_argument(
        "--all-skills", action="store_true", help="Install all skills without prompting"
    )
    parser.add_argument(
        "--all-mcps", action="store_true", help="Install all MCPs without prompting"
    )
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    non_interactive = bool(args.yes)

    do_skills = bool(args.all_skills or non_interactive)
    do_codebase = bool(args.all_mcps or non_interactive)
    do_lean = bool(args.all_mcps or non_interactive)

    if not do_skills and not do_codebase and not do_lean:
        do_skills = ask(
            "Install mattpocock skills", default=False, non_interactive=non_interactive
        )
        do_codebase = ask(
            "Install MCP: codebase-memory-mcp",
            default=False,
            non_interactive=non_interactive,
        )
        do_lean = ask(
            "Install MCP: lean-ctx", default=False, non_interactive=non_interactive
        )

    if do_skills:
        _install_skills(non_interactive)
    else:
        skip("mattpocock skills: skipped")

    if do_codebase:
        with_ui = ask(
            "Install codebase-memory-mcp with UI",
            default=True,
            non_interactive=non_interactive,
        )
        _install_codebase_memory(with_ui)
    else:
        skip("codebase-memory-mcp: skipped")

    if do_lean:
        _install_lean_ctx(non_interactive)
    else:
        skip("lean-ctx: skipped")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
