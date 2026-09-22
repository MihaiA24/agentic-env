"""Run one-shot bootstrap for agentic-env install and configure steps."""

from __future__ import annotations

import argparse
import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

from . import configure_agent_mcps, install_agents, install_skills_mcps, stack_doctor
from .common import interactive, ok, set_verbose, skip, split_csv, warn
from .stack_metadata import CONFIGURE_AGENT_CHOICES, SKILL_AGENTS, SKILL_AGENT_LOOKUP


_DEFAULT_SKILL_PROFILE = "default"
_DEFAULT_CONFIG_SERVERS: Final[tuple[str, ...]] = tuple(configure_agent_mcps.MCP_SERVERS.keys())
_DEFAULT_CONFIG_AGENTS: Final[tuple[str, ...]] = CONFIGURE_AGENT_CHOICES
_DEFAULT_SKILL_AGENTS: Final[tuple[str, ...]] = tuple(agent for agent, _, _ in SKILL_AGENTS)


@dataclass(frozen=True)
class BootstrapPhase:
    name: str
    argv: list[str]
    main: Callable[[list[str]], int]
    requested: bool
    skipped_reason: str | None = None


@dataclass
class BootstrapPhaseResult:
    name: str
    requested: bool
    skipped_reason: str | None = None
    error: str | None = None


def _parse(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install all agent CLIs, MCP tooling, and MCP/global skill wiring in one\n"
            "command with safe ordering and optional split steps."
        )
    )
    parser.add_argument("--skip-install-agents", action="store_true", help="Skip the install-agents phase.")
    parser.add_argument("--skip-install-skills", action="store_true", help="Skip the install-skills-mcps phase.")
    parser.add_argument("--skip-configure", action="store_true", help="Skip the configure-agent-mcps phase.")
    parser.add_argument("--skip-doctor", action="store_true", help="Skip the final stack-doctor phase.")
    parser.add_argument(
        "--configure-no-skills",
        action="store_true",
        help="During configure phase, skip writing matching global skills.",
    )
    parser.add_argument(
        "--server",
        action="append",
        help=(
            "MCP server(s) to configure for the configure phase. Repeat or comma-separate. "
            f"Defaults to all: {', '.join(_DEFAULT_CONFIG_SERVERS)}"
        ),
    )
    parser.add_argument(
        "--agent",
        action="append",
        help=(
            "Agent(s) to configure with MCP entries. Repeat or comma-separate. "
            f"Defaults to: {', '.join(_DEFAULT_CONFIG_AGENTS)}."
        ),
    )
    parser.add_argument(
        "--skill-agent",
        action="append",
        help=(
            "Target agent name(s) for skill installation. Repeat or comma-separate. "
            f"Defaults to all ({', '.join(_DEFAULT_SKILL_AGENTS)})."
        ),
    )
    parser.add_argument(
        "--skill-profile",
        default=_DEFAULT_SKILL_PROFILE,
        help=(
            "Skill-pack profile name for install-skills-mcps phase. "
            f"Defaults to '{_DEFAULT_SKILL_PROFILE}'."
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help=(
            "Let the two install phases prompt with their checkbox pickers instead of "
            "installing every CLI and the --skill-profile packs."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Show the commands that would run and exit.")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


def _normalize_values(
    values: list[str] | None,
    *,
    allowed: tuple[str, ...] | list[str],
    label: str,
    lookup: Mapping[str, str] | None = None,
) -> list[str] | None:
    selected = split_csv(values)
    if not selected:
        return list(allowed)

    canonical_lookup = lookup if lookup is not None else {name.lower(): name for name in allowed}
    out: list[str] = []
    unknown: list[str] = []
    for item in selected:
        canonical = canonical_lookup.get(item.lower())
        if canonical is None:
            unknown.append(item)
            continue
        if canonical not in out:
            out.append(canonical)

    if unknown:
        warn(f"Unknown {label}: {', '.join(sorted(unknown))}")
        warn(f"Available: {', '.join(allowed)}")
        return None

    return out


def _bootstrap_plan(args: argparse.Namespace) -> list[BootstrapPhase] | None:
    config_servers = _normalize_values(args.server, allowed=_DEFAULT_CONFIG_SERVERS, label="server")
    if config_servers is None:
        return None

    config_agents = _normalize_values(
        args.agent,
        allowed=_DEFAULT_CONFIG_AGENTS,
        label="agent",
    )
    if config_agents is None:
        return None

    skill_agents = _normalize_values(
        args.skill_agent,
        allowed=_DEFAULT_SKILL_AGENTS,
        label="skill agent",
        lookup=SKILL_AGENT_LOOKUP,
    )
    if skill_agents is None:
        return None

    if args.interactive:
        install_args = []
        skill_args = []
        for skill_agent in split_csv(args.skill_agent):
            skill_args.extend(["--skill-agent", skill_agent])
    else:
        install_args = ["--all", "--yes"]
        skill_args = ["--all-mcps", "--yes", "--skill-profile", args.skill_profile]
        for skill_agent in skill_agents:
            skill_args.extend(["--skill-agent", skill_agent])
    if args.verbose:
        install_args.append("--verbose")
        skill_args.append("--verbose")

    configure_args = ["--yes"]
    if args.configure_no_skills:
        configure_args.append("--no-skills")
    for server in config_servers:
        configure_args.extend(["--server", server])
    for agent in config_agents:
        configure_args.extend(["--agent", agent])
    if args.verbose:
        configure_args.append("--verbose")

    return [
        BootstrapPhase(
            name="install-agents",
            argv=install_args,
            main=install_agents.main,
            requested=not args.skip_install_agents,
            skipped_reason=(
                "install-agents phase skipped (pass --skip-install-agents to restore)"
                if args.skip_install_agents
                else None
            ),
        ),
        BootstrapPhase(
            name="install-skills",
            argv=skill_args,
            main=install_skills_mcps.main,
            requested=not args.skip_install_skills,
            skipped_reason=(
                "install-skills phase skipped (pass --skip-install-skills to restore)"
                if args.skip_install_skills
                else None
            ),
        ),
        BootstrapPhase(
            name="configure",
            argv=configure_args,
            main=configure_agent_mcps.main,
            requested=not args.skip_configure,
            skipped_reason=(
                "configure phase skipped (pass --skip-configure to restore)"
                if args.skip_configure
                else None
            ),
        ),
        BootstrapPhase(
            name="doctor",
            argv=[],
            main=stack_doctor.main,
            requested=not args.skip_doctor,
            skipped_reason=(
                "doctor phase skipped (pass --skip-doctor to restore)"
                if args.skip_doctor
                else None
            ),
        ),
    ]


def _display_plan(phases: list[BootstrapPhase]) -> None:
    for phase in phases:
        if not phase.requested:
            continue
        skip(f"agentic-bootstrap [dry-run]: {phase.name}: {' '.join(shlex.quote(arg) for arg in phase.argv)}")


def _run_phase(phase: BootstrapPhase) -> BootstrapPhaseResult:
    if not phase.requested:
        return BootstrapPhaseResult(
            name=phase.name,
            requested=False,
            skipped_reason=phase.skipped_reason,
        )

    try:
        ok(f"agentic-bootstrap: running {phase.name}")
        exit_code = phase.main(phase.argv)
    except Exception as exc:  # pragma: no cover - defensive bridge only
        return BootstrapPhaseResult(
            name=phase.name,
            requested=True,
            error=f"bootstrap phase raised {type(exc).__name__}: {exc}",
        )

    if exit_code != 0:
        return BootstrapPhaseResult(
            name=phase.name,
            requested=True,
            error="phase returned non-zero",
        )

    return BootstrapPhaseResult(name=phase.name, requested=True)


def _run_plan(plan: list[BootstrapPhase]) -> list[BootstrapPhaseResult]:
    return [_run_phase(phase) for phase in plan]


def _print_summary(results: list[BootstrapPhaseResult]) -> None:
    for phase in results:
        if not phase.requested and phase.skipped_reason:
            warn(f"agentic-bootstrap: {phase.name}: {phase.skipped_reason}")
        if phase.requested and phase.error:
            warn(f"agentic-bootstrap: {phase.name}: {phase.error}")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    set_verbose(args.verbose)

    if args.skip_install_agents and args.skip_install_skills and args.skip_configure and args.skip_doctor:
        skip("agentic-bootstrap: no phases selected")
        return 0

    if not args.skill_profile.strip():
        warn("--skill-profile must not be empty")
        return 1

    if args.interactive and not args.dry_run and not interactive():
        warn("--interactive needs a terminal")
        return 1

    plan = _bootstrap_plan(args)
    if plan is None:
        return 1

    if not any(phase.requested for phase in plan):
        warn("agentic-bootstrap: no executable phases after argument validation")
        return 1

    if args.dry_run:
        _display_plan(plan)
        return 0

    results = _run_plan(plan)
    _print_summary(results)
    if any(result.error for result in results):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
