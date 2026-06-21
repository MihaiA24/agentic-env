#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Install local agent CLIs."""
from __future__ import annotations

import argparse
import sys

from common import ask, cmd_exists, cmd_works, run, run_shell, ok, warn, skip


def _install_hermes(non_interactive: bool) -> bool:
    if cmd_exists("hermes") and not ask("Reinstall Hermes Agent", default=False, non_interactive=non_interactive):
        skip("Hermes Agent: skipped")
        return False

    if not cmd_exists("curl"):
        warn("curl is required to install Hermes Agent")
        return False

    run_shell("curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash")
    ok("Hermes Agent: installed")
    return True


def _install_omp(non_interactive: bool) -> bool:
    if cmd_exists("omp"):
        if cmd_works("omp"):
            if not ask(
                "Reinstall OMP / Oh My Pi", default=False, non_interactive=non_interactive
            ):
                skip("OMP / Oh My Pi: skipped")
                return False
        else:
            warn("OMP / Oh My Pi exists but appears broken; reinstalling")

    if not cmd_exists("curl"):
        warn("curl is required to install OMP / Oh My Pi")
        return False

    run_shell("curl -fsSL https://omp.sh/install | sh")
    ok("OMP / Oh My Pi: installed")
    return True


def _install_codex(non_interactive: bool) -> bool:
    if not cmd_exists("npm"):
        warn("npm is required to install OpenAI Codex CLI")
        return False

    if cmd_exists("codex") and not ask("Reinstall OpenAI Codex CLI", default=False, non_interactive=non_interactive):
        skip("OpenAI Codex CLI: skipped")
        return False

    run(["npm", "install", "-g", "@openai/codex"])
    ok("OpenAI Codex CLI: installed")
    return True


def _install_claude(non_interactive: bool) -> bool:
    if cmd_exists("claude") and not ask("Reinstall Claude Code", default=False, non_interactive=non_interactive):
        skip("Claude Code: skipped")
        return False

    if not cmd_exists("curl"):
        warn("curl is required to install Claude Code")
        return False

    run_shell("curl -fsSL https://claude.ai/install.sh | bash")
    ok("Claude Code: installed")
    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Hermes/OMP/Codex/Claude")
    parser.add_argument("--all", action="store_true", help="Install all tools without prompting")
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    non_interactive = bool(args.yes)

    if args.all or non_interactive:
        do_all = True
    else:
        do_all = ask("Install all agent CLIs", default=True, non_interactive=False)

    if do_all:
        do_hermes = do_omp = do_codex = do_claude = True
    else:
        do_hermes = ask("Install Hermes Agent", default=False, non_interactive=non_interactive)
        do_omp = ask("Install OMP / Oh My Pi", default=False, non_interactive=non_interactive)
        do_codex = ask("Install OpenAI Codex CLI", default=False, non_interactive=non_interactive)
        do_claude = ask("Install Claude Code", default=False, non_interactive=non_interactive)

    if do_hermes:
        _install_hermes(non_interactive)
    else:
        skip("Hermes Agent: skipped")

    if do_omp:
        _install_omp(non_interactive)
    else:
        skip("OMP / Oh My Pi: skipped")

    if do_codex:
        _install_codex(non_interactive)
    else:
        skip("OpenAI Codex CLI: skipped")

    if do_claude:
        _install_claude(non_interactive)
    else:
        skip("Claude Code: skipped")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
