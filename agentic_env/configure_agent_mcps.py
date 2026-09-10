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
from .stack_metadata import AGENTMEMORY_VERSION, CONFIGURE_AGENT_CHOICES


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
    "codebase-memory-mcp": McpServer(
        name="codebase-memory-mcp",
        command="codebase-memory-mcp",
        requires=("codebase-memory-mcp",),
    ),
    "agentmemory": McpServer(
        name="agentmemory",
        command="npx",
        args=("-y", f"@agentmemory/mcp@{AGENTMEMORY_VERSION}"),
        requires=("npx",),
        hermes_memory_provider="agentmemory",
    ),
}

SKILLS: dict[str, Skill] = {}

_SKILL_BODY_DIR = Path(__file__).with_name("skill_bodies")
_SKILL_NAMES = ("codebase-memory-mcp", "agentmemory", "ponytail")
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
OMP_AGENT_CONFIG_PATH = Path.home() / ".omp" / "agent" / "config.yml"
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


def _parse_yaml_scalar(raw: str, line_no: int) -> object:
    text = raw.strip()
    if not text:
        raise ValueError(f"line {line_no}: malformed YAML scalar")

    if text.startswith("#"):
        raise ValueError(f"line {line_no}: inline comment without value")

    if text.startswith(("'", '"')) and text.endswith(text[0]):
        return text[1:-1]

    if text.startswith("[") and text.endswith("]"):
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            # YAML flow lists allow unquoted scalars (`[hermes-cli]`); parse
            # each comma-separated item as a scalar instead of failing.
            inner = text[1:-1].strip()
            if not inner:
                return []
            return [
                _parse_yaml_scalar(item, line_no) for item in inner.split(",")
            ]
        if not isinstance(value, list):
            raise ValueError(f"line {line_no}: list value expected")
        return value

    if text in {"true", "false", "null", "~"}:
        return {"true": True, "false": False, "null": None, "~": None}[text]

    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass

    if (text.startswith("{") and text.endswith("}")) or (
        text.startswith('"') and text.endswith('"')
    ):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON value: {exc}") from None

    return text


def _parse_yaml_config(path: str) -> dict[str, object]:
    result: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, result)]

    for line_no, raw_line in enumerate(path.splitlines(), start=1):
        stripped_line = raw_line.rstrip()
        if not stripped_line.strip() or stripped_line.lstrip().startswith("#"):
            continue

        indent = len(stripped_line) - len(stripped_line.lstrip(" "))
        indentation = stripped_line[:indent]
        if "\t" in indentation:
            raise ValueError(f"line {line_no}: tabs are not supported in Hermes config")

        if ":" not in stripped_line.strip():
            raise ValueError(f"line {line_no}: malformed key/value pair")

        while indent <= stack[-1][0]:
            stack.pop()
        parent_indent, parent = stack[-1]

        raw_key, raw_value = stripped_line.strip().split(":", 1)
        if not raw_key:
            raise ValueError(f"line {line_no}: missing key")
        key = raw_key.strip()
        if key in parent:
            raise ValueError(f"line {line_no}: duplicate key '{key}'")

        if not raw_value.strip():
            value: object = {}
            parent[key] = value
            stack.append((indent, value))
            continue

        parent[key] = _parse_yaml_scalar(raw_value.strip(), line_no)

    return result


def _yaml_scalar(value: object) -> str:
    if isinstance(value, str):
        needs_quotes = (
            not value
            or value.startswith(" ")
            or value.endswith(" ")
            or any(ch.isspace() for ch in value)
            or any(ch in ":#{}[]@" for ch in value)
        )
        return json.dumps(value) if needs_quotes else value

    if isinstance(value, (bool, int, float)) or value is None:
        return json.dumps(value)
    if isinstance(value, list):
        return json.dumps(value)

    return json.dumps(value)


def _dump_yaml_config(data: dict[str, object], *, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            if value:
                lines.append(_dump_yaml_config(value, indent=indent + 2))
            continue

        lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")

    return "\n".join(lines)


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

@dataclass(frozen=True)
class _ConfigMergeOutcome:
    config: dict[str, object]
    changed: bool
    provider_conflict: bool
    required_provider: str | None


@dataclass(frozen=True)
class _HermesConfigAdapter:
    path: Path

    def _read(self) -> dict[str, object] | None:
        if not self.path.exists():
            return {}

        raw = self.path.read_text(encoding="utf-8")
        try:
            return _parse_yaml_config(raw)
        except Exception as exc:
            warn(f"{self.path}: malformed YAML config ({exc})")
            return None

    def _write(self, data: dict[str, object], *, dry_run: bool) -> bool:
        content = _dump_yaml_config(data).rstrip()
        if content:
            content += "\n"
        return _write_atomic_text(self.path, content, dry_run=dry_run)

    def add_servers(self, data: dict[str, object], servers: list[McpServer]) -> _ConfigMergeOutcome:
        mcp_servers = data.get("mcp_servers")
        changed = False
        provider_conflict = False
        required_provider: str | None = None

        if mcp_servers is None:
            mcp_servers = {}
            data["mcp_servers"] = mcp_servers
            changed = True
        elif not isinstance(mcp_servers, dict):
            raise ValueError("`mcp_servers` block must be an object")

        for server in servers:
            if server.name not in mcp_servers:
                mcp_servers[server.name] = {
                    "command": server.command,
                    **({"args": list(server.args)} if server.args else {}),
                }
                ok(f"Hermes config: {server.name} MCP added")
                changed = True
            else:
                skip(f"Hermes config: {server.name} MCP already configured")

            if server.hermes_memory_provider:
                memory = data.get("memory")
                if memory is None:
                    data["memory"] = {"provider": server.hermes_memory_provider}
                    required_provider = server.hermes_memory_provider
                    changed = True
                    continue

                if not isinstance(memory, dict):
                    raise ValueError("`memory` block must be an object")
                current = memory.get("provider")
                if current is None:
                    memory["provider"] = server.hermes_memory_provider
                    required_provider = server.hermes_memory_provider
                    changed = True
                elif current != server.hermes_memory_provider:
                    provider_conflict = True
                    warn("Hermes config: existing memory.provider is set; skipped changing it")

                if current == server.hermes_memory_provider:
                    required_provider = server.hermes_memory_provider

        return _ConfigMergeOutcome(
            config=data,
            changed=changed,
            provider_conflict=provider_conflict,
            required_provider=required_provider,
        )

    def validate(
        self,
        data: dict[str, object],
        servers: list[McpServer],
        *,
        required_provider: str | None = None,
    ) -> bool:
        mcp_servers = data.get("mcp_servers")
        if not isinstance(mcp_servers, dict):
            return False
        for server in servers:
            if server.name not in mcp_servers:
                return False

        if required_provider is None:
            return True

        memory = data.get("memory")
        if not isinstance(memory, dict):
            return False
        provider = memory.get("provider")
        return isinstance(provider, str) and provider == required_provider


@dataclass(frozen=True)
class _OmpConfigAdapter:
    path: Path

    def _read(self) -> dict[str, object] | None:
        return _load_json_object(self.path)

    def _write(self, data: dict[str, object], *, dry_run: bool) -> bool:
        return _write_atomic_text(self.path, json.dumps(data, indent=2) + "\n", dry_run=dry_run)

    def add_servers(self, data: dict[str, object], servers: list[McpServer]) -> bool:
        mcp_servers = data.get("mcpServers")
        changed = False

        if mcp_servers is None:
            mcp_servers = {}
            data["mcpServers"] = mcp_servers
            changed = True
        elif not isinstance(mcp_servers, dict):
            raise ValueError("`mcpServers` block must be an object")

        for server in servers:
            if server.name in mcp_servers:
                skip(f"{self.path}: {server.name} MCP already configured")
                continue

            mcp_servers[server.name] = _json_entry(server)
            ok(f"{self.path}: {server.name} MCP added")
            changed = True

        return changed

    def remove_servers(self, data: dict[str, object], names: tuple[str, ...]) -> bool:
        mcp_servers = data.get("mcpServers")
        if not isinstance(mcp_servers, dict):
            return False
        changed = False
        for name in names:
            if name in mcp_servers:
                del mcp_servers[name]
                ok(f"{self.path}: {name} MCP removed (excluded on OMP)")
                changed = True
        return changed

    def gate_servers(self, data: dict[str, object], names: tuple[str, ...]) -> bool:
        if not names:
            return False
        disabled = data.get("disabledServers")
        if disabled is None:
            disabled = []
            data["disabledServers"] = disabled
        elif not isinstance(disabled, list):
            raise ValueError("`disabledServers` block must be a list")
        changed = False
        for name in names:
            if name not in disabled:
                disabled.append(name)
                ok(f"{self.path}: {name} MCP gated off (disabledServers)")
                changed = True
        return changed

    def validate(self, data: dict[str, object], servers: list[McpServer]) -> bool:
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
            if not server.args and args:
                return False
            if server.args and args != list(server.args):
                return False

        return True


_HERMES_CONFIG_ADAPTER = _HermesConfigAdapter(path=HERMES_CONFIG_PATH)
_OMP_CONFIG_ADAPTERS = [_OmpConfigAdapter(path=path) for path in OMP_MCP_PATHS]


def _json_entry(server: McpServer) -> dict[str, object]:
    entry: dict[str, object] = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    return entry


def _write_json_config_data(
    adapter: _OmpConfigAdapter,
    servers: list[McpServer],
    *,
    remove: tuple[str, ...] = (),
    gate: tuple[str, ...] = (),
    dry_run: bool,
) -> bool:
    data = adapter._read()
    if data is None:
        return False

    try:
        changed = adapter.add_servers(data, servers)
        changed = adapter.gate_servers(data, gate) or changed
    except ValueError as exc:
        warn(f"{adapter.path}: {exc}")
        return False
    changed = adapter.remove_servers(data, remove) or changed

    if not adapter.validate(data, servers):
        warn(f"{adapter.path}: generated config failed validation")
        return False

    if not changed:
        return True

    if not adapter._write(data, dry_run=dry_run):
        return False
    if dry_run:
        return True

    verified = adapter._read()
    if verified is None or not adapter.validate(verified, servers):
        warn(f"{adapter.path}: write verification failed")
        return False
    return True


def configure_hermes(servers: list[McpServer], *, dry_run: bool) -> bool:
    data = _HERMES_CONFIG_ADAPTER._read()
    if data is None:
        return False

    try:
        outcome = _HERMES_CONFIG_ADAPTER.add_servers(data, servers)
    except ValueError as exc:
        warn(f"{_HERMES_CONFIG_ADAPTER.path}: {exc}")
        return False

    required_provider = None if outcome.provider_conflict else outcome.required_provider
    if not _HERMES_CONFIG_ADAPTER.validate(
        outcome.config,
        servers,
        required_provider=required_provider,
    ):
        warn("Hermes config: post-merge validation failed")
        return False

    if not outcome.changed:
        return True

    if not _HERMES_CONFIG_ADAPTER._write(outcome.config, dry_run=dry_run):
        return False
    if dry_run:
        return True

    verified = _HERMES_CONFIG_ADAPTER._read()
    if verified is None or not _HERMES_CONFIG_ADAPTER.validate(
        verified,
        servers,
        required_provider=required_provider,
    ):
        warn(f"{_HERMES_CONFIG_ADAPTER.path}: write verification failed")
        return False
    return True


# MCP servers deliberately absent from OMP; stale pre-existing entries are removed on converge
# and the names stay in `disabledServers` so OMP's claude-import (~/.claude.json) cannot
# mount them either. lean-ctx is Rejected stack-wide (ADR-0009).
OMP_EXCLUDED_SERVERS = {
    "agentmemory": "ADR-0006: Mnemopi owns narrative memory on OMP",
    "lean-ctx": "ADR-0009: lean-ctx removed from the stack",
}

# Servers wired on OMP but default-off ("Gated" in DECISIONS_AI_TOOLING.md); the installer
# keeps them in `disabledServers` so a fresh machine never mounts them silently.
OMP_GATED_SERVERS = ("codebase-memory-mcp",)
# OMP built-ins with no `mcpServers` entry; gated the same way (0 calls, DECISIONS "Rejected").
OMP_GATED_BUILTINS = ("node_repl",)


def configure_omp(servers: list[McpServer], *, dry_run: bool) -> bool:
    omp_servers: list[McpServer] = []
    for server in servers:
        reason = OMP_EXCLUDED_SERVERS.get(server.name)
        if reason:
            skip(f"OMP config: {server.name} MCP not written ({reason})")
        else:
            omp_servers.append(server)

    excluded = tuple(OMP_EXCLUDED_SERVERS)
    gated = tuple(s.name for s in omp_servers if s.name in OMP_GATED_SERVERS) + OMP_GATED_BUILTINS + excluded
    ok_all = True
    for adapter in _OMP_CONFIG_ADAPTERS:
        if not _write_json_config_data(
            adapter, omp_servers, remove=excluded, gate=gated, dry_run=dry_run
        ):
            ok_all = False
    return ok_all


_OMP_HOOK_FILES = ("verification-recorder.ts", "retention-canary.ts")

# Settings that must be present in ~/.omp/agent/config.yml as (top-level block,
# "key: value" line), keyed per settings-schema.ts at the pinned OMP_VERSION
# (DECISIONS_AI_TOOLING.md "Live wiring": compaction tuning, single memory
# owner, hooks, skill-store discipline).
OMP_AGENT_CONFIG_CONTRACT = (
    ("memory", "backend: mnemopi"),
    ("mnemopi", "polyphonicRecall: false"),
    ("compaction", "thresholdTokens: 150000"),
    ("compaction", "idleEnabled: true"),
    ("compaction", "handoffSaveToDisk: true"),
    ("compaction", "methodOrder:"),
    ("skills", "enableClaudeUser: true"),
    ("skills", "enableAgentsUser: false"),
    *(("extensions", name) for name in _OMP_HOOK_FILES),
)

_OMP_AGENT_CONFIG_TEMPLATE = """memory:
  backend: mnemopi
mnemopi:
  polyphonicRecall: false
{extensions}compaction:
  thresholdTokens: 150000
  idleEnabled: true
  handoffSaveToDisk: true
  methodOrder:
    - handoff
    - remote
    - soft
skills:
  enableClaudeUser: true
  enableAgentsUser: false
"""


def omp_config_block(text: str, key: str) -> list[str]:
    """Stripped direct-child lines under top-level ``key:``."""
    lines: list[str] = []
    inside = False
    child_indent: int | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        if indent == 0:
            inside = line.split(":", 1)[0].strip() == key
            child_indent = None
            continue
        if not inside:
            continue
        if child_indent is None:
            child_indent = indent
        if indent < child_indent:
            inside = False
            child_indent = None
        elif indent == child_indent:
            lines.append(stripped)
    return lines


def _omp_scalar_without_comment(raw: str) -> str:
    quote: str | None = None
    index = 0
    while index < len(raw):
        char = raw[index]
        if quote == "'":
            if char == "'":
                if index + 1 < len(raw) and raw[index + 1] == "'":
                    index += 2
                    continue
                quote = None
        elif quote == '"':
            if char == "\\":
                index += 2
                continue
            if char == '"':
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == "#" and (index == 0 or raw[index - 1].isspace()):
            return raw[:index].rstrip()
        index += 1
    return raw.strip()


def _omp_contract_line_matches(line: str, marker: str) -> bool:
    expected_key, separator, expected_raw = marker.partition(":")
    if not separator:
        return marker in line

    actual_key, separator, actual_raw = line.partition(":")
    if not separator or actual_key.strip() != expected_key.strip():
        return False
    if not expected_raw.strip():
        return True

    try:
        expected = _parse_yaml_scalar(_omp_scalar_without_comment(expected_raw), 0)
        actual = _parse_yaml_scalar(_omp_scalar_without_comment(actual_raw), 0)
    except ValueError:
        return False
    return type(actual) is type(expected) and actual == expected


def omp_config_drift(text: str) -> list[str]:
    """Contract settings missing from an OMP agent config; empty when compliant."""
    return [
        f"{block}.{marker}"
        for block, marker in OMP_AGENT_CONFIG_CONTRACT
        if not any(
            _omp_contract_line_matches(line, marker)
            for line in omp_config_block(text, block)
        )
    ]


def _find_omp_hooks_dir() -> Path | None:
    """Hooks live in the dotfiles checkout, never in the wheel: $AGENTIC_DOTFILES_ROOT,
    then ~/.dotfiles, then any ancestor of cwd or this file."""
    roots: list[Path] = []
    env_root = os.environ.get("AGENTIC_DOTFILES_ROOT")
    if env_root:
        roots.append(Path(env_root))
    roots.append(Path.home() / ".dotfiles")
    for base in (Path.cwd().resolve(), Path(__file__).resolve()):
        roots.append(base)
        roots.extend(base.parents)
    for root in roots:
        hooks_dir = root / "omp" / "hooks"
        if all((hooks_dir / name).is_file() for name in _OMP_HOOK_FILES):
            return hooks_dir
    return None


def converge_omp_agent_config(*, dry_run: bool) -> bool:
    path = OMP_AGENT_CONFIG_PATH
    if not path.exists():
        hooks_dir = _find_omp_hooks_dir()
        if hooks_dir is None:
            warn(
                f"{path}: omp/hooks not found in ~/.dotfiles (or set AGENTIC_DOTFILES_ROOT); "
                "not seeding a config the doctor would fail"
            )
            return False
        hook_lines = "\n".join(f"  - {hooks_dir / name}" for name in _OMP_HOOK_FILES)
        extensions = f"extensions:\n{hook_lines}\n"
        content = _OMP_AGENT_CONFIG_TEMPLATE.format(extensions=extensions)
        if not _write_atomic_text(path, content, dry_run=dry_run):
            return False
        if not dry_run:
            ok(f"{path}: agent config seeded from stack contract")
        return True

    # Existing config is user-owned YAML this module cannot safely rewrite
    # (block lists and quoted scalars do not survive the built-in parser),
    # so verify the contract markers and report drift instead of editing.
    missing = omp_config_drift(path.read_text(encoding="utf-8"))
    if not missing:
        skip(f"{path}: agent config matches stack contract")
        return True
    warn(
        f"{path}: missing stack contract settings: {', '.join(missing)} "
        "(see DECISIONS_AI_TOOLING.md 'Live wiring'; merge manually)"
    )
    return True


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
            reason = OMP_EXCLUDED_SERVERS.get(server_name)
            if root in OMP_SKILL_ROOTS and reason:
                skip(f"{root / server_name}: skill not installed on OMP ({reason})")
                continue
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
        ok_all = converge_omp_agent_config(dry_run=args.dry_run) and ok_all
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
