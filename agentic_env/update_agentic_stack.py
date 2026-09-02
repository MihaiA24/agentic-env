"""Update already installed agent tooling."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from . import install_agents, install_skills_mcps
from .common import (
    cmd_exists,
    cmd_version_matches,
    info,
    ok,
    run,
    set_verbose,
    skip,
    warn,
)
from .remote_install_contract import validate_remote_contract
from .stack_metadata import (
    AGENTMEMORY_NPM_PACKAGE,
    SKILLS_CLI_PACKAGE,
    STACK_VERSION_FRAGMENTS,
    UPDATE_REMOTE_CONTRACT,
)

_REMOTE_INSTALL_CONTRACT = UPDATE_REMOTE_CONTRACT


def _update(label: str, installer: Callable[[], bool]) -> bool:
    info(f"Converging {label}...")
    try:
        if not installer():
            warn(f"{label}: convergence failed")
            return False
    except Exception:
        warn(f"{label}: convergence failed")
        return False
    ok(f"{label}: curated version installed")
    return True


def _update_if_present(label: str, binary: str, installer: Callable[[], bool]) -> bool:
    if not cmd_exists(binary):
        skip(f"{label}: not installed")
        return True
    return _update(label, installer)


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update installed agentic tooling")
    parser.add_argument(
        "--verify-remote-contract",
        action="store_true",
        help="Validate remote update references and exit",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show full command output"
    )
    return parser.parse_args(argv)


def _update_codex() -> bool:
    return _update_if_present(
        "OpenAI Codex CLI", "codex", lambda: install_agents._install_codex(True)
    )


def _update_agentmemory() -> bool:
    if not cmd_exists("agentmemory"):
        skip("agentmemory: not installed")
        return True
    if cmd_version_matches("agentmemory", STACK_VERSION_FRAGMENTS["agentmemory"]):
        skip("agentmemory CLI: curated version already installed")
        return True
    if not cmd_exists("npm"):
        warn("agentmemory: npm not installed")
        return False

    def install() -> bool:
        if not install_skills_mcps._install_npm_global(
            AGENTMEMORY_NPM_PACKAGE, "agentmemory"
        ):
            return False
        return cmd_version_matches(
            "agentmemory", STACK_VERSION_FRAGMENTS["agentmemory"]
        )

    return _update("agentmemory CLI", install)


def _update_skills() -> bool:
    if not cmd_exists("skills"):
        skip("skills CLI: not installed")
        return True
    if cmd_version_matches("skills", STACK_VERSION_FRAGMENTS["skills"]):
        skip("skills CLI: curated version already installed")
        return True
    if not cmd_exists("npm"):
        warn("skills CLI: npm not installed")
        return False

    def install() -> bool:
        run(["npm", "install", "-g", SKILLS_CLI_PACKAGE])
        return cmd_version_matches("skills", STACK_VERSION_FRAGMENTS["skills"])

    return _update("skills CLI", install)


def _validate_remote_contract() -> bool:
    return validate_remote_contract(
        _REMOTE_INSTALL_CONTRACT, scope="agentic-update-stack"
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)

    if not _validate_remote_contract():
        return 1
    if args.verify_remote_contract:
        ok("agentic-update-stack: remote contract check passed")
        return 0

    steps: tuple[tuple[str, str, Callable[[], bool]], ...] = (
        ("Hermes Agent", "hermes", lambda: install_agents._install_hermes(True)),
        ("OMP / Oh My Pi", "omp", lambda: install_agents._install_omp(True)),
        ("Claude Code", "claude", lambda: install_agents._install_claude(True)),
        (
            "codebase-memory-mcp",
            "codebase-memory-mcp",
            lambda: install_skills_mcps._install_codebase_memory(True, True),
        ),
    )
    ok_all = True
    for label, binary, installer in steps:
        ok_all = _update_if_present(label, binary, installer) and ok_all
    ok_all = _update_codex() and ok_all
    ok_all = _update_agentmemory() and ok_all
    ok_all = _update_skills() and ok_all

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
