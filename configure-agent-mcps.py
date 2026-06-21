#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
"""Configure project-memory MCP servers and global agent skills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.prompt import Prompt

from common import cmd_exists, console, ok, skip, warn


@dataclass(frozen=True)
class McpServer:
    name: str
    command: str
    args: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    hermes_memory_provider: str | None = None


@dataclass(frozen=True)
class Skill:
    name: str
    body: str


MCP_SERVERS: dict[str, McpServer] = {
    "lean-ctx": McpServer(
        name="lean-ctx",
        command="lean-ctx",
        requires=("lean-ctx",),
    ),
    "codebase-memory-mcp": McpServer(
        name="codebase-memory-mcp",
        command="codebase-memory-mcp",
        requires=("codebase-memory-mcp",),
    ),
    "agentmemory": McpServer(
        name="agentmemory",
        command="npx",
        args=("-y", "@agentmemory/mcp"),
        requires=("npx",),
        hermes_memory_provider="agentmemory",
    ),
}

SKILLS: dict[str, Skill] = {
    "lean-ctx": Skill(
        name="lean-ctx",
        body="""---
name: lean-ctx
description: Use when reading files, searching code, listing directories, or running shell commands so context is compressed and cached.
---

# lean-ctx

Use `lean-ctx` as the default local context layer.

- Prefer lean-ctx reads/search/tree/shell wrappers over raw file and shell output.
- Read the smallest useful fidelity first: map/signatures/range before full files.
- Use cached re-reads and diff mode after edits.
- Run `lean-ctx doctor` when wiring looks broken.
- Do not treat lean-ctx cache or session state as the canonical project decision record.
""",
    ),
    "codebase-memory-mcp": Skill(
        name="codebase-memory-mcp",
        body="""---
name: codebase-memory-mcp
description: Use for structural codebase questions: symbols, callers, callees, architecture, routes, impact, and dead-code candidates.
---

# codebase-memory-mcp

Use `codebase-memory-mcp` for structural memory.

Ask the graph before scanning files manually when the task is about:

- finding symbols or implementations
- callers and callees
- architecture overview
- route/channel discovery
- impact analysis before refactors
- dead or unused candidates

The graph is rebuildable from code. Do not store rationale or accepted decisions here; promote durable decisions to ADRs.
""",
    ),
    "agentmemory": Skill(
        name="agentmemory",
        body="""---
name: agentmemory
description: Use for long-term narrative memory: decisions, rationale, project history, user preferences, and cross-session recall.
---

# agentmemory

Use `agentmemory` for narrative memory.

Good memories:

- decisions and rationale discovered during a session
- project-specific preferences
- debugging history likely to matter later
- context that should survive agent restarts

Important accepted decisions must also be promoted to plain text in `docs/adr/*.md`. `agentmemory` improves recall; it is not the canonical audit record.
""",
    ),
}

AGENT_CHOICES = ("hermes", "omp")
OMP_MCP_PATHS = (
    Path.home() / ".omp" / "agent" / "mcp.json",
    Path.home() / ".pi" / "agent" / "mcp.json",
)
OMP_SKILL_ROOTS = (
    Path.home() / ".omp" / "agent" / "skills",
    Path.home() / ".pi" / "agent" / "skills",
)
HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
HERMES_SKILL_ROOT = Path.home() / ".hermes" / "skills"


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure Hermes/OMP MCP servers and global skills"
    )
    parser.add_argument(
        "--server",
        action="append",
        choices=(*MCP_SERVERS.keys(), "all"),
        help="MCP server to configure; repeatable. Default: interactive checkbox, or all with --yes.",
    )
    parser.add_argument(
        "--agent",
        action="append",
        choices=(*AGENT_CHOICES, "all"),
        help="Agent to configure; repeatable. Default: interactive checkbox, or all with --yes.",
    )
    parser.add_argument("--yes", action="store_true", help="Select defaults without prompts")
    parser.add_argument("--no-skills", action="store_true", help="Do not add global skills")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    return parser.parse_args(argv)


def _expand(values: list[str] | None, all_values: tuple[str, ...] | list[str]) -> list[str] | None:
    if not values:
        return None
    if "all" in values:
        return list(all_values)
    return list(dict.fromkeys(values))


def _select_many(
    title: str,
    values: list[str],
    *,
    explicit: list[str] | None,
    non_interactive: bool,
) -> list[str]:
    if explicit is not None:
        return explicit
    if non_interactive:
        return values

    console.print(f"\n[bold]{title}[/]")
    for idx, value in enumerate(values, start=1):
        console.print(f"  [green][x][/] {idx}. {value}")
    raw = Prompt.ask(
        "[cyan]?[/] Select numbers, comma ranges, 'all', or Enter for checked defaults",
        default="all",
    ).strip()
    if raw.lower() in {"", "all"}:
        return values
    if raw.lower() in {"none", "-"}:
        return []

    selected: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            indexes = range(int(start), int(end) + 1)
        else:
            indexes = (int(part),)
        for index in indexes:
            if index < 1 or index > len(values):
                raise SystemExit(f"invalid selection: {index}")
            selected.append(values[index - 1])
    return list(dict.fromkeys(selected))


def _server_yaml(server: McpServer, indent: str = "  ") -> list[str]:
    lines = [f"{indent}{server.name}:", f"{indent}  command: {server.command}"]
    if server.args:
        lines.append(f"{indent}  args: {json.dumps(list(server.args))}")
    return lines


def _find_yaml_block(lines: list[str], key: str) -> tuple[int, int, int] | None:
    pattern = re.compile(rf"^(?P<indent>\s*){re.escape(key)}:\s*$")
    for start, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        indent = len(match.group("indent"))
        end = len(lines)
        for i in range(start + 1, len(lines)):
            child = lines[i]
            if child.strip() and len(child) - len(child.lstrip()) <= indent:
                end = i
                break
        return start, end, indent
    return None


def _yaml_block_has_key(lines: list[str], start: int, end: int, indent: int, key: str) -> bool:
    pattern = re.compile(rf"^\s{{{indent + 2}}}{re.escape(key)}:\s*$")
    return any(pattern.match(line) for line in lines[start + 1 : end])


def _ensure_hermes_memory_provider(lines: list[str], provider: str) -> tuple[list[str], bool]:
    block = _find_yaml_block(lines, "memory")
    if block is None:
        return [*lines, "", "memory:", f"  provider: {provider}"], True

    start, end, indent = block
    provider_pattern = re.compile(r"^\s*provider:\s*(.*?)\s*$")
    for i in range(start + 1, end):
        match = provider_pattern.match(lines[i])
        if not match:
            continue
        current = match.group(1)
        if current == provider:
            return lines, False
        warn("Hermes config: existing memory.provider is set; skipped changing it")
        return lines, False

    updated = [*lines]
    updated.insert(start + 1, " " * (indent + 2) + f"provider: {provider}")
    return updated, True


def configure_hermes(servers: list[McpServer], *, dry_run: bool) -> bool:
    path = HERMES_CONFIG_PATH
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    changed = False

    block = _find_yaml_block(lines, "mcp_servers")
    if block is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("mcp_servers:")
        block = (len(lines) - 1, len(lines), 0)
        changed = True

    for server in servers:
        start, end, indent = block
        if _yaml_block_has_key(lines, start, end, indent, server.name):
            skip(f"Hermes config: {server.name} MCP already configured")
        else:
            lines[end:end] = _server_yaml(server, " " * (indent + 2))
            block = _find_yaml_block(lines, "mcp_servers") or block
            changed = True
            ok(f"Hermes config: {server.name} MCP added")

        if server.hermes_memory_provider:
            lines, provider_changed = _ensure_hermes_memory_provider(
                lines, server.hermes_memory_provider
            )
            changed = changed or provider_changed
            block = _find_yaml_block(lines, "mcp_servers") or block

    if changed:
        if dry_run:
            skip(f"dry-run: would write {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def _json_entry(server: McpServer) -> dict[str, object]:
    entry: dict[str, object] = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    return entry


def _load_json_object(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        warn(f"{path}: invalid JSON; skipped")
        return None
    if not isinstance(value, dict):
        warn(f"{path}: root JSON value is not an object; skipped")
        return None
    return value


def configure_omp(servers: list[McpServer], *, dry_run: bool) -> bool:
    ok_all = True
    for path in OMP_MCP_PATHS:
        data = _load_json_object(path)
        if data is None:
            ok_all = False
            continue
        mcp_servers = data.setdefault("mcpServers", {})
        if not isinstance(mcp_servers, dict):
            warn(f"{path}: mcpServers is not an object; skipped")
            ok_all = False
            continue

        changed = False
        for server in servers:
            if server.name in mcp_servers:
                skip(f"{path}: {server.name} MCP already configured")
            else:
                mcp_servers[server.name] = _json_entry(server)
                changed = True
                ok(f"{path}: {server.name} MCP added")

        if changed:
            if dry_run:
                skip(f"dry-run: would write {path}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return ok_all


def _install_skill(root: Path, skill: Skill, *, dry_run: bool) -> bool:
    skill_path = root / skill.name / "SKILL.md"
    if skill_path.exists():
        skip(f"{skill_path}: skill already present")
        return True
    if dry_run:
        skip(f"dry-run: would write {skill_path}")
        return True
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(skill.body.rstrip() + "\n", encoding="utf-8")
    ok(f"{skill_path}: skill added")
    return True


def install_skills(agents: list[str], server_names: list[str], *, dry_run: bool) -> bool:
    roots: list[Path] = []
    if "hermes" in agents:
        roots.append(HERMES_SKILL_ROOT)
    if "omp" in agents:
        roots.extend(OMP_SKILL_ROOTS)

    ok_all = True
    for root in roots:
        for server_name in server_names:
            ok_all = _install_skill(root, SKILLS[server_name], dry_run=dry_run) and ok_all
    return ok_all


def warn_missing_commands(servers: list[McpServer]) -> None:
    for server in servers:
        for command in server.requires:
            if not cmd_exists(command):
                warn(f"{server.name}: required command '{command}' not found on PATH")


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    server_names = _select_many(
        "MCP servers",
        list(MCP_SERVERS),
        explicit=_expand(args.server, list(MCP_SERVERS)),
        non_interactive=args.yes,
    )
    agents = _select_many(
        "Agents",
        list(AGENT_CHOICES),
        explicit=_expand(args.agent, list(AGENT_CHOICES)),
        non_interactive=args.yes,
    )

    install_matching_skills = not args.no_skills
    if not args.yes and install_matching_skills:
        from common import ask

        install_matching_skills = ask(
            "Add matching global skills if missing",
            default=True,
            non_interactive=False,
        )

    servers = [MCP_SERVERS[name] for name in server_names]
    warn_missing_commands(servers)

    ok_all = True
    if "hermes" in agents:
        ok_all = configure_hermes(servers, dry_run=args.dry_run) and ok_all
    if "omp" in agents:
        ok_all = configure_omp(servers, dry_run=args.dry_run) and ok_all
    if install_matching_skills:
        ok_all = install_skills(agents, server_names, dry_run=args.dry_run) and ok_all
    else:
        skip("global skills: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
