"""Install local agent CLIs."""
from __future__ import annotations

import argparse
import sys

from .common import ask, cmd_exists, cmd_works, run, run_shell, ok, set_verbose, skip, warn, info
from .remote_install_contract import REMOTE_KIND_NPM, REMOTE_KIND_SCRIPT, validate_remote_contract

_HERMES_INSTALL_URL = "https://hermes-agent.nousresearch.com/install.sh"
_OMP_INSTALL_URL = "https://omp.sh/install"
_CLAUDE_INSTALL_URL = "https://claude.ai/install.sh"
_OPENAI_CODEX_PACKAGE = "@openai/codex@0.144.1"

_REMOTE_INSTALL_CONTRACT = {
    "hermes": {
        "label": "Hermes installer script",
        "reference": _HERMES_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": False,
        "reason": "No versioned hermes bootstrap script is published.",
    },
    "omp": {
        "label": "OMP / Oh My Pi installer script",
        "reference": _OMP_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": False,
        "reason": "No versioned omp installer script is published.",
    },
    "codex": {
        "label": "OpenAI Codex npm package",
        "reference": _OPENAI_CODEX_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
    },
    "claude": {
        "label": "Claude installer script",
        "reference": _CLAUDE_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": False,
        "reason": "No versioned Claude installer script is published.",
    },
}


def _validate_remote_contract() -> bool:
    return validate_remote_contract(_REMOTE_INSTALL_CONTRACT, scope="agentic-install-agents")


def _install_hermes(non_interactive: bool) -> bool:
    if cmd_exists("hermes") and not ask("Reinstall Hermes Agent", default=False, non_interactive=non_interactive):
        skip("Hermes Agent: skipped")
        return True

    if not cmd_exists("curl"):
        warn("curl is required to install Hermes Agent")
        return False

    info("Installing Hermes...")
    run_shell(f"curl -fsSL {_HERMES_INSTALL_URL} | bash")
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

    if not cmd_exists("curl"):
        warn("curl is required to install OMP / Oh My Pi")
        return False

    info("Installing OMP / Oh My Pi...")
    run_shell(f"curl -fsSL {_OMP_INSTALL_URL} | sh")
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
    run(["npm", "install", "-g", _OPENAI_CODEX_PACKAGE])
    ok("OpenAI Codex CLI: installed")
    return True


def _install_claude(non_interactive: bool) -> bool:
    if cmd_exists("claude") and not ask("Reinstall Claude Code", default=False, non_interactive=non_interactive):
        skip("Claude Code: skipped")
        return True

    if not cmd_exists("curl"):
        warn("curl is required to install Claude Code")
        return False

    info("Installing Claude Code...")
    run_shell(f"curl -fsSL {_CLAUDE_INSTALL_URL} | bash")
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
