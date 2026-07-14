"""Run one-shot bootstrap for agentic-env install and configure steps."""

from __future__ import annotations

import argparse
import shlex
import sys

from . import configure_agent_mcps, install_agents, install_skills_mcps
from .common import ok, set_verbose, skip, warn
from .stack_metadata import CONFIGURE_AGENT_CHOICES, SKILL_AGENTS, SKILL_AGENT_LOOKUP


_DEFAULT_SKILL_PROFILE = "default"
_DEFAULT_CONFIG_SERVERS = tuple(configure_agent_mcps.MCP_SERVERS.keys())
_DEFAULT_CONFIG_AGENTS = CONFIGURE_AGENT_CHOICES
_DEFAULT_SKILL_AGENTS = tuple(agent for agent, _, _ in SKILL_AGENTS)


def _parse(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install all agent CLIs, MCP tooling, and MCP/global skill wiring in one\n"
            "command with safe ordering and optional split steps."
        )
    )
    parser.add_argument(
        "--skip-install-agents", action="store_true", help="Skip the install-agents phase."
    )
    parser.add_argument(
        "--skip-install-skills", action="store_true", help="Skip the install-skills-mcps phase."
    )
    parser.add_argument(
        "--skip-configure", action="store_true", help="Skip the configure-agent-mcps phase."
    )
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
        "--dry-run", action="store_true", help="Show the commands that would run and exit."
    )
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


def _split_csv(values: list[str] | None) -> list[str]:
    if not values:
        return []
    parsed: list[str] = []
    for raw in values:
        for item in raw.split(","):
            value = item.strip()
            if value:
                parsed.append(value)
    return parsed


def _normalize_values(
    values: list[str] | None,
    *,
    allowed: tuple[str, ...] | list[str],
    label: str,
) -> list[str] | None:
    selected = _split_csv(values)
    if not selected:
        return list(allowed)

    lookup = {name.lower(): name for name in allowed}
    out: list[str] = []
    unknown: list[str] = []
    for item in selected:
        canonical = lookup.get(item.lower())
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


def _normalize_skill_agents(values: list[str] | None) -> list[str] | None:
    selected = _split_csv(values)
    if not selected:
        return list(_DEFAULT_SKILL_AGENTS)

    out: list[str] = []
    unknown: list[str] = []
    for item in selected:
        canonical = SKILL_AGENT_LOOKUP.get(item.lower())
        if canonical is None:
            unknown.append(item)
            continue
        if canonical not in out:
            out.append(canonical)

    if unknown:
        warn(f"Unknown skill agent: {', '.join(sorted(unknown))}")
        warn(
            "Available: "
            + ", ".join(agent for agent, _, _ in SKILL_AGENTS)
        )
        return None

    return out


def _bootstrap_plan(
    args: argparse.Namespace,
) -> list[tuple[str, list[str], object]] | None:
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

    skill_agents = _normalize_skill_agents(args.skill_agent)
    if skill_agents is None:
        return None

    phases: list[tuple[str, list[str], object]] = []
    if not args.skip_install_agents:
        install_args = ["--all", "--yes"]
        if args.verbose:
            install_args.append("--verbose")
        phases.append(("install-agents", install_args, install_agents.main))

    if not args.skip_install_skills:
        skill_args = ["--all-mcps", "--yes", "--skill-profile", args.skill_profile]
        for skill_agent in skill_agents:
            skill_args.extend(["--skill-agent", skill_agent])
        if args.verbose:
            skill_args.append("--verbose")
        phases.append(("install-skills", skill_args, install_skills_mcps.main))

    if not args.skip_configure:
        configure_args = ["--yes"]
        if args.configure_no_skills:
            configure_args.append("--no-skills")
        for server in config_servers:
            configure_args.extend(["--server", server])
        for agent in config_agents:
            configure_args.extend(["--agent", agent])
        if args.verbose:
            configure_args.append("--verbose")
        phases.append(("configure", configure_args, configure_agent_mcps.main))

    return phases


def _display_plan(phases: list[tuple[str, list[str], object]]) -> None:
    for name, argv, _ in phases:
        skip(f"agentic-bootstrap [dry-run]: {name}: {' '.join(shlex.quote(arg) for arg in argv)}")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    set_verbose(args.verbose)

    if args.skip_install_agents and args.skip_install_skills and args.skip_configure:
        skip("agentic-bootstrap: no phases selected")
        return 0

    if not args.skill_profile.strip():
        warn("--skill-profile must not be empty")
        return 1

    plan = _bootstrap_plan(args)
    if plan is None:
        return 1

    if not plan:
        warn("agentic-bootstrap: no executable phases after argument validation")
        return 1

    if args.dry_run:
        _display_plan(plan)
        return 0

    ok_all = True
    for phase_name, phase_args, phase_main in plan:
        ok(f"agentic-bootstrap: running {phase_name}")
        ok_all = phase_main(phase_args) == 0 and ok_all

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
