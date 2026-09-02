"""Read-only diagnosis of the agent stack against the wiring contract.

Mandatory checks cover the OMP-primary layer (DECISIONS_AI_TOOLING.md "Live
wiring"): any failure exits 1 and names the corrective command. Secondary
agents (Hermes, Claude Code, Codex) only warn; their wiring correctness is
tracked under "Secondary agents TODO". Nothing is written.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.table import Table

from . import configure_agent_mcps as cfg
from .common import cmd_exists, cmd_version_matches, console
from .install_skills_mcps import profile_skills
from .stack_metadata import STACK_VERSION_FRAGMENTS

CLAUDE_USER_CONFIG_PATH = Path.home() / ".claude.json"
# OMP loads ~/.claude/skills (skills.enableClaudeUser); ~/.agents/skills is the
# recovery store and stays unloaded (skills.enableAgentsUser: false).
CLAUDE_SKILL_ROOT = Path.home() / ".claude" / "skills"
SKILL_PROFILE = "default"
SECONDARY_AGENTS = ("hermes", "claude", "codex", "agentmemory")

FIX_CONFIGURE = "agentic-configure-agent-mcps --yes"
FIX_UPDATE = "agentic-update-stack"
FIX_SKILLS = f"agentic-install-skills-mcps --all-mcps --yes --skill-profile {SKILL_PROFILE}"

# Prose that re-routes native reads through an MCP; forbidden anywhere OMP
# loads MCP definitions from (ADR-0007, ADR-0009).
INTERCEPTION_MARKERS = ("ctx_", "shadow mode", "auto-route")


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str = ""
    fix: str = ""
    mandatory: bool = True


def _check_binary(name: str, *, fix: str, mandatory: bool) -> Check:
    want = " ".join(STACK_VERSION_FRAGMENTS[name])
    if not cmd_exists(name):
        return Check(f"{name} on PATH", False, "missing", fix, mandatory)
    if not cmd_version_matches(name, STACK_VERSION_FRAGMENTS[name]):
        return Check(f"{name} on PATH", False, f"version != {want}", fix, mandatory)
    return Check(f"{name} on PATH", True, want, mandatory=mandatory)


def _mcp_servers(path: Path) -> tuple[dict[str, object], list[object]] | None:
    data = cfg._load_json_object(path)
    if data is None:
        return None
    servers = data.get("mcpServers")
    disabled = data.get("disabledServers")
    return (
        servers if isinstance(servers, dict) else {},
        disabled if isinstance(disabled, list) else [],
    )


def _interception_prose(servers: dict[str, object]) -> list[str]:
    hits: list[str] = []
    for name, entry in servers.items():
        text = entry.get("instructions", "") if isinstance(entry, dict) else ""
        if isinstance(text, str) and any(marker in text for marker in INTERCEPTION_MARKERS):
            hits.append(name)
    return hits


def _short(path: Path) -> str:
    home = Path.home()
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


def _check_omp_mcp(path: Path) -> list[Check]:
    label = _short(path)
    if not path.exists():
        return [Check(f"{label} present", False, "missing", FIX_CONFIGURE)]
    loaded = _mcp_servers(path)
    if loaded is None:
        return [Check(f"{label} present", False, "unreadable JSON", FIX_CONFIGURE)]
    servers, disabled = loaded
    checks = [
        Check(
            f"{label}: {name} wired + gated",
            name in servers and name in disabled,
            "mcpServers + disabledServers" if name in servers and name in disabled
            else "missing from mcpServers" if name not in servers
            else "not in disabledServers",
            FIX_CONFIGURE,
        )
        for name in cfg.OMP_GATED_SERVERS
    ]
    mounted = [name for name in cfg.OMP_EXCLUDED_SERVERS if name in servers]
    checks.append(
        Check(
            f"{label}: excluded servers absent",
            not mounted,
            ", ".join(mounted) if mounted else ", ".join(cfg.OMP_EXCLUDED_SERVERS),
            FIX_CONFIGURE,
        )
    )
    hits = _interception_prose(servers)
    checks.append(
        Check(
            f"{label}: no read-interception prose",
            not hits,
            ", ".join(hits) if hits else "clean",
            FIX_CONFIGURE,
        )
    )
    return checks


def _check_claude_import() -> Check:
    """OMP's claude-import mounts ~/.claude.json servers; their prose must be clean too."""
    name = "~/.claude.json: no read-interception prose"
    if not CLAUDE_USER_CONFIG_PATH.exists():
        return Check(name, True, "absent")
    loaded = _mcp_servers(CLAUDE_USER_CONFIG_PATH)
    if loaded is None:
        return Check(name, False, "unreadable JSON", "fix ~/.claude.json by hand")
    hits = _interception_prose(loaded[0])
    return Check(
        name,
        not hits,
        ", ".join(hits) if hits else "clean",
        "delete mcpServers.<name> from ~/.claude.json" if hits else "",
    )


def _check_agent_config() -> list[Check]:
    path = cfg.OMP_AGENT_CONFIG_PATH
    if not path.exists():
        return [Check("~/.omp/agent/config.yml present", False, "missing", FIX_CONFIGURE)]
    text = path.read_text(encoding="utf-8")
    missing = cfg.omp_config_drift(text)
    checks = [
        Check(
            "config.yml stack contract",
            not missing,
            ", ".join(missing) if missing else f"{len(cfg.OMP_AGENT_CONFIG_CONTRACT)} settings",
            "merge DECISIONS_AI_TOOLING.md 'Live wiring' into ~/.omp/agent/config.yml",
        )
    ]
    extensions = [line.lstrip("- ").strip() for line in cfg.omp_config_block(text, "extensions")]
    for hook in cfg._OMP_HOOK_FILES:
        paths = [Path(entry) for entry in extensions if entry.endswith(f"/{hook}")]
        if len(paths) != 1:
            detail = "not registered" if not paths else f"registered {len(paths)}x"
            checks.append(Check(f"hook {hook} once", False, detail, "edit extensions: in ~/.omp/agent/config.yml"))
        elif not paths[0].is_file():
            checks.append(Check(f"hook {hook} once", False, f"{paths[0]} missing", "restore omp/hooks in the dotfiles checkout"))
        else:
            checks.append(Check(f"hook {hook} once", True, str(paths[0])))
    return checks


def _check_skills() -> list[Check]:
    roster = profile_skills(SKILL_PROFILE)
    missing = [name for name in roster if not (CLAUDE_SKILL_ROOT / name / "SKILL.md").is_file()]
    checks = [
        Check(
            f"curated roster ({SKILL_PROFILE}) under ~/.claude/skills",
            bool(roster) and not missing,
            ", ".join(missing) if missing else f"{len(roster)} skills" if roster else "manifest unreadable",
            FIX_SKILLS,
        )
    ]
    for root in cfg.OMP_SKILL_ROOTS:
        absent = [
            name for name in cfg.SKILLS
            if name not in cfg.OMP_EXCLUDED_SERVERS and not (root / name / "SKILL.md").is_file()
        ]
        checks.append(
            Check(
                f"built-in descriptors in {_short(root)}",
                not absent,
                ", ".join(absent) if absent else "present",
                FIX_CONFIGURE,
            )
        )
    stale = [root / "lean-ctx" for root in (*cfg.OMP_SKILL_ROOTS, CLAUDE_SKILL_ROOT) if (root / "lean-ctx").exists()]
    checks.append(
        Check(
            "no lean-ctx skill in OMP-loaded roots",
            not stale,
            ", ".join(map(str, stale)) if stale else "clean",
            " && ".join(f"rm -rf {path}" for path in stale),
        )
    )
    return checks


def _check_hermes() -> list[Check]:
    path = cfg.HERMES_CONFIG_PATH
    if not path.exists():
        return [Check("~/.hermes/config.yaml present", False, "missing", FIX_CONFIGURE, mandatory=False)]
    entries = cfg.omp_config_block(path.read_text(encoding="utf-8"), "mcp_servers")
    absent = [name for name in cfg.MCP_SERVERS if f"{name}:" not in entries]
    checks = [
        Check(
            "hermes mcp_servers wired",
            not absent,
            ", ".join(absent) if absent else ", ".join(cfg.MCP_SERVERS),
            FIX_CONFIGURE,
            mandatory=False,
        )
    ]
    missing = [name for name in cfg.SKILLS if not (cfg.HERMES_SKILL_ROOT / name / "SKILL.md").is_file()]
    checks.append(
        Check(
            "hermes skill descriptors",
            not missing,
            ", ".join(missing) if missing else "present",
            FIX_CONFIGURE,
            mandatory=False,
        )
    )
    return checks


def run_checks() -> list[Check]:
    checks = [
        _check_binary("omp", fix=FIX_UPDATE, mandatory=True),
        _check_binary("codebase-memory-mcp", fix=FIX_SKILLS, mandatory=True),
    ]
    for path in cfg.OMP_MCP_PATHS:
        checks.extend(_check_omp_mcp(path))
    checks.append(_check_claude_import())
    checks.extend(_check_agent_config())
    checks.extend(_check_skills())
    checks.extend(_check_binary(name, fix=FIX_UPDATE, mandatory=False) for name in SECONDARY_AGENTS)
    checks.extend(_check_hermes())
    return checks


def report(checks: list[Check]) -> int:
    table = Table(title="agentic-stack-doctor", show_lines=False)
    table.add_column("", width=1)
    table.add_column("check")
    table.add_column("detail")
    for check in checks:
        mark = "[green]✓[/]" if check.ok else "[red]✗[/]" if check.mandatory else "[yellow]![/]"
        table.add_row(mark, check.name, check.detail)
    console.print(table)

    failures = [check for check in checks if not check.ok and check.mandatory]
    warnings = [check for check in checks if not check.ok and not check.mandatory]
    for check in warnings:
        console.print(f"[yellow]![/] TODO secondary: {check.name} ({check.detail}) → {check.fix}")
    for check in failures:
        console.print(f"[red]✗[/] {check.name} ({check.detail}) → {check.fix}")
    if failures:
        console.print(f"[red]{len(failures)} mandatory check(s) failed[/]")
        return 1
    console.print(f"[green]stack OK[/] ({len(warnings)} secondary warning(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose the installed agent stack against the wiring contract (read-only)."
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])
    return report(run_checks())


if __name__ == "__main__":
    raise SystemExit(main())
