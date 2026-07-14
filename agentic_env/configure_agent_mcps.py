"""Configure project-memory MCP servers and global agent skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rich.prompt import Prompt

from .common import cmd_exists, console, ok, set_verbose, skip, warn
from .stack_metadata import CONFIGURE_AGENT_CHOICES


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

SKILLS: dict[str, Skill] = {}

_SKILL_BODY_DIR = Path(__file__).with_name("skill_bodies")
_SKILL_NAMES = ("lean-ctx", "codebase-memory-mcp", "agentmemory", "ponytail")
_SKILL_BODY_MISSING_TEMPLATE = """---
name: {name}
description: Built-in skill descriptor is unavailable; using fallback text.
---

# {name}

Built-in skill body is unavailable in this package.
Please add a matching file under `agentic_env/skill_bodies/{name}.md`.
"""


def _skill_body_path(name: str) -> Path:
    return _SKILL_BODY_DIR / f"{name}.md"


def _load_skill_body(name: str) -> str:
    path = _skill_body_path(name)
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError as exc:
        warn(f"skill descriptor missing for '{name}': {path} ({exc})")
        return _SKILL_BODY_MISSING_TEMPLATE.format(name=name)

    if not payload.strip():
        warn(f"skill descriptor empty for '{name}': {path}")
        return _SKILL_BODY_MISSING_TEMPLATE.format(name=name)

    return payload


def _load_builtin_skills() -> dict[str, Skill]:
    return {
        name: Skill(name=name, body=_load_skill_body(name)) for name in _SKILL_NAMES
    }


SKILLS = _load_builtin_skills()

AGENT_CHOICES = CONFIGURE_AGENT_CHOICES
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
_BACKUP_SUFFIX = ".agentic-env.bak"


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
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions without writing files"
    )
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
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


def _yaml_block_get_key_value(
    lines: list[str], start: int, end: int, indent: int, key: str
) -> str | None:
    pattern = re.compile(rf"^\s{{{indent + 2}}}{re.escape(key)}:\s*(.*?)\s*$")
    for line in lines[start + 1 : end]:
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return None


def _validate_hermes_config(
    lines: list[str], servers: list[McpServer], *, required_provider: str | None = None
) -> bool:
    block = _find_yaml_block(lines, "mcp_servers")
    if block is None:
        return False
    start, end, indent = block
    for server in servers:
        if not _yaml_block_has_key(lines, start, end, indent, server.name):
            return False

    if required_provider is None:
        return True

    memory_block = _find_yaml_block(lines, "memory")
    if memory_block is None:
        return False
    memory_start, memory_end, memory_indent = memory_block
    provider = _yaml_block_get_key_value(
        lines, memory_start, memory_end, memory_indent, "provider"
    )
    if provider is None:
        return False
    return provider == required_provider


def _write_atomic_text(path: Path, content: str, *, dry_run: bool) -> bool:
    if dry_run:
        skip(f"dry-run: would write {path}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = path.with_suffix(path.suffix + _BACKUP_SUFFIX)
    if path.exists():
        if backup_path.exists():
            try:
                backup_path.unlink()
            except OSError as exc:
                warn(f"{path}: failed to clear stale backup {backup_path}: {exc}")
                return False
        try:
            shutil.copy2(path, backup_path)
        except OSError as exc:
            warn(f"{path}: failed to create backup {backup_path}: {exc}")
            return False

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            temp_path = Path(stream.name)
        os.replace(temp_path, path)
        return True
    except Exception as exc:
        warn(f"{path}: atomic write failed: {exc}")
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return False


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _ensure_hermes_memory_provider(
    lines: list[str], provider: str
) -> tuple[list[str], bool, bool]:
    block = _find_yaml_block(lines, "memory")
    if block is None:
        return [*lines, "", "memory:", f"  provider: {provider}"], True, False

    start, end, indent = block
    provider_pattern = re.compile(r"^\s*provider:\s*(.*?)\s*$")
    for i in range(start + 1, end):
        match = provider_pattern.match(lines[i])
        if not match:
            continue
        current = match.group(1).strip().strip('"').strip("'")
        if current == provider:
            return lines, False, False
        warn("Hermes config: existing memory.provider is set; skipped changing it")
        return lines, False, True

    updated = [*lines]
    updated.insert(start + 1, " " * (indent + 2) + f"provider: {provider}")
    return updated, True, False


def configure_hermes(servers: list[McpServer], *, dry_run: bool) -> bool:
    path = HERMES_CONFIG_PATH
    lines = _read_lines(path)
    changed = False
    provider_conflict = False
    required_provider: str | None = None

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
            lines, provider_changed, conflict = _ensure_hermes_memory_provider(
                lines, server.hermes_memory_provider
            )
            changed = changed or provider_changed
            provider_conflict = provider_conflict or conflict
            if provider_changed:
                required_provider = server.hermes_memory_provider
            block = _find_yaml_block(lines, "mcp_servers") or block

    if changed:
        if not _validate_hermes_config(
            lines,
            servers,
            required_provider=None if provider_conflict else required_provider,
        ):
            warn("Hermes config: post-merge validation failed")
            return False
        if not _write_atomic_text(path, "\n".join(lines).rstrip() + "\n", dry_run=dry_run):
            return False
        if not dry_run:
            verified = _read_lines(path)
            if not _validate_hermes_config(
                verified,
                servers,
                required_provider=None if provider_conflict else required_provider,
            ):
                warn(f"{path}: write verification failed")
                return False
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


def _validate_omp_config(data: dict[str, object], servers: list[McpServer]) -> bool:
    mcp_servers = data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        return False
    for server in servers:
        entry = mcp_servers.get(server.name)
        if not isinstance(entry, dict):
            return False
        if entry.get("command") != server.command:
            return False
        args = entry.get("args", [])
        if not server.args:
            if args:
                return False
        elif args != list(server.args):
            return False
    return True


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
            if not _validate_omp_config(data, servers):
                warn(f"{path}: generated config failed validation")
                ok_all = False
                continue
            if not _write_atomic_text(
                path, json.dumps(data, indent=2) + "\n", dry_run=dry_run
            ):
                ok_all = False
                continue
            if not dry_run:
                verified = _load_json_object(path)
                if verified is None or not _validate_omp_config(verified, servers):
                    warn(f"{path}: write verification failed")
                    ok_all = False
    return ok_all


def _install_skill(root: Path, skill: Skill, *, dry_run: bool) -> bool:
    skill_path = root / skill.name / "SKILL.md"
    if skill_path.exists():
        skip(f"{skill_path}: skill already present")
        return True

    content = skill.body.rstrip() + "\n"
    if not _write_atomic_text(skill_path, content, dry_run=dry_run):
        return False
    if dry_run:
        return True

    if skill_path.read_text(encoding="utf-8") != content:
        warn(f"{skill_path}: write verification failed")
        return False
    ok(f"{skill_path}: skill written")
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
    set_verbose(args.verbose)
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
        from .common import ask

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
        install_names = list(server_names)
        if server_names and "ponytail" not in install_names:
            install_names.append("ponytail")
        ok_all = install_skills(agents, install_names, dry_run=args.dry_run) and ok_all
    else:
        skip("global skills: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
