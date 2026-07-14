"""Install local agent CLIs."""
from __future__ import annotations

import argparse
import sys

from .common import (
    ask,
    cmd_exists,
    cmd_works,
    info,
    ok,
    run,
    run_remote_script,
    set_verbose,
    skip,
    warn,
)
from .remote_install_contract import validate_remote_contract
from .stack_metadata import (
    AGENTS_INSTALL_REMOTE_CONTRACT,
    CLAUDE_INSTALL_SHA256,
    CLAUDE_INSTALL_URL,
    HERMES_INSTALL_SHA256,
    HERMES_INSTALL_URL,
    OMP_INSTALL_SHA256,
    OMP_INSTALL_URL,
    OPENAI_CODEX_PACKAGE,
)

_REMOTE_INSTALL_CONTRACT = AGENTS_INSTALL_REMOTE_CONTRACT


def _validate_remote_contract() -> bool:
    return validate_remote_contract(_REMOTE_INSTALL_CONTRACT, scope="agentic-install-agents")


def _install_hermes(non_interactive: bool) -> bool:
    if cmd_exists("hermes") and not ask(
        "Reinstall Hermes Agent", default=False, non_interactive=non_interactive
    ):
        skip("Hermes Agent: skipped")
        return True

    info("Installing Hermes...")
    if not run_remote_script(
        label="Hermes installer",
        url=HERMES_INSTALL_URL,
        expected_sha256=HERMES_INSTALL_SHA256,
        interpreter="bash",
    ):
        return False
    ok("Hermes Agent: installed")
    return True


def _install_omp(non_interactive: bool) -> bool:
    if cmd_exists("omp"):
        if cmd_works("omp"):
            if not ask(
                "Reinstall OMP / Oh My Pi", default=False, non_interactive=non_interactive
            ):
                skip("OMP / Oh My Pi: skipped")
                return True
        else:
            warn("OMP / Oh My Pi exists but appears broken; reinstalling")

    info("Installing OMP / Oh My Pi...")
    if not run_remote_script(
        label="OMP installer",
        url=OMP_INSTALL_URL,
        expected_sha256=OMP_INSTALL_SHA256,
        interpreter="sh",
    ):
        return False
    ok("OMP / Oh My Pi: installed")
    return True


def _install_codex(non_interactive: bool) -> bool:
    if not cmd_exists("npm"):
        warn("npm is required to install OpenAI Codex CLI")
        return False

    if cmd_exists("codex") and not ask(
        "Reinstall OpenAI Codex CLI", default=False, non_interactive=non_interactive
    ):
        skip("OpenAI Codex CLI: skipped")
        return True

    info("Installing OpenAI Codex CLI...")
    run(["npm", "install", "-g", OPENAI_CODEX_PACKAGE])
    ok("OpenAI Codex CLI: installed")
    return True


def _install_claude(non_interactive: bool) -> bool:
    if cmd_exists("claude") and not ask(
        "Reinstall Claude Code", default=False, non_interactive=non_interactive
    ):
        skip("Claude Code: skipped")
        return True

    info("Installing Claude Code...")
    if not run_remote_script(
        label="Claude installer",
        url=CLAUDE_INSTALL_URL,
        expected_sha256=CLAUDE_INSTALL_SHA256,
        interpreter="bash",
    ):
        return False
    ok("Claude Code: installed")
    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Hermes/OMP/Codex/Claude. Returns non-zero on any selected-step failure."
    )
    parser.add_argument("--all", action="store_true", help="Install all tools without prompting")
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    parser.add_argument(
        "--verify-remote-contract",
        action="store_true",
        help="Validate remote install contract entries and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes)

    if not _validate_remote_contract():
        return 1

    if args.verify_remote_contract:
        ok("agentic-install-agents: remote contract check passed")
        return 0

    if args.all:
        do_all = True
    else:
        do_all = ask(
            "Install all agent CLIs",
            default=not non_interactive,
            non_interactive=non_interactive,
        )

    if do_all:
        do_hermes = do_omp = do_codex = do_claude = True
    else:
        do_hermes = ask("Install Hermes Agent", default=False, non_interactive=non_interactive)
        do_omp = ask("Install OMP / Oh My Pi", default=False, non_interactive=non_interactive)
        do_codex = ask("Install OpenAI Codex CLI", default=False, non_interactive=non_interactive)
        do_claude = ask("Install Claude Code", default=False, non_interactive=non_interactive)

    ok_all = True
    if do_hermes:
        ok_all = _install_hermes(non_interactive) and ok_all
    else:
        skip("Hermes Agent: skipped")

    if do_omp:
        ok_all = _install_omp(non_interactive) and ok_all
    else:
        skip("OMP / Oh My Pi: skipped")

    if do_codex:
        ok_all = _install_codex(non_interactive) and ok_all
    else:
        skip("OpenAI Codex CLI: skipped")

    if do_claude:
        ok_all = _install_claude(non_interactive) and ok_all
    else:
        skip("Claude Code: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
