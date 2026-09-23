"""Configure project-memory MCP servers and global agent skills."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from .common import (
    Option,
    ask,
    choose,
    cmd_exists,
    interactive,
    ok,
    set_verbose,
    skip,
    warn,
)
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


_SKILL_BODY_DIR = Path(__file__).with_name("skill_bodies")
_SKILL_NAMES = ("codebase-memory-mcp", "agentmemory", "ponytail")


def _load_skill_body(name: str) -> str | None:
    path = _SKILL_BODY_DIR / f"{name}.md"
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError as exc:
        warn(f"skill descriptor missing for '{name}': {path} ({exc})")
        return None

    if not payload.strip():
        warn(f"skill descriptor empty for '{name}': {path}")
        return None

    return payload


def _load_builtin_skills() -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for name in _SKILL_NAMES:
        body = _load_skill_body(name)
        if body is not None:
            skills[name] = Skill(name=name, body=body)
    return skills


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


def load_json_object(path: Path) -> dict[str, object] | None:
    """Parsed JSON object; ``{}`` when absent, ``None`` (after a warning) when unusable."""
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


def load_yaml_object(path: Path) -> dict[str, object] | None:
    """Parsed YAML mapping; ``{}`` when absent or empty, ``None`` (after a warning) when unusable."""
    if not path.exists():
        return {}
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        warn(f"{path}: malformed YAML config ({exc})")
        return None
    if value is None:
        return {}
    if not isinstance(value, dict):
        warn(f"{path}: root YAML value is not a mapping; skipped")
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

def mcp_entry_drift(entry: object, server: McpServer) -> str:
    if not isinstance(entry, dict):
        return "must be an object"
    if entry.get("command") != server.command:
        return f"command must be {server.command!r}"
    if entry.get("args", []) != list(server.args):
        return f"args must be {list(server.args)!r}"
    return ""


def _check_existing_mcp_entries(
    data: dict[str, object], key: str, servers: list[McpServer]
) -> dict[str, object] | None:
    entries = data.get(key)
    if entries is None:
        return None
    if not isinstance(entries, dict):
        raise ValueError(f"`{key}` block must be an object; fix this file manually")
    for server in servers:
        if server.name in entries:
            drift = mcp_entry_drift(entries[server.name], server)
            if drift:
                raise ValueError(
                    f"{key}.{server.name}: {drift}; existing entry preserved; fix it manually"
                )
    return entries


@dataclass(frozen=True)
class _ConfigMergeOutcome:
    config: dict[str, object]
    changed: bool
    required_provider: str | None


def _write_hermes_config(
    path: Path, data: dict[str, object], *, dry_run: bool
) -> bool:
    content = yaml.safe_dump(data, sort_keys=False, allow_unicode=True) if data else ""
    return _write_atomic_text(path, content, dry_run=dry_run)


def add_hermes_servers(
    data: dict[str, object], servers: list[McpServer]
) -> _ConfigMergeOutcome:
    mcp_servers = _check_existing_mcp_entries(data, "mcp_servers", servers)
    for server in servers:
        if not server.hermes_memory_provider:
            continue
        memory = data.get("memory")
        if memory is not None and not isinstance(memory, dict):
            raise ValueError("`memory` block must be an object; fix this file manually")
        current = memory.get("provider") if isinstance(memory, dict) else None
        if current is not None and current != server.hermes_memory_provider:
            raise ValueError(
                f"memory.provider: existing {current!r} conflicts with required "
                f"{server.hermes_memory_provider!r}; preserved; fix it manually"
            )

    changed = False
    required_provider: str | None = None

    if mcp_servers is None:
        mcp_servers = {}
        data["mcp_servers"] = mcp_servers
        changed = True

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
            required_provider = server.hermes_memory_provider
            memory = data.get("memory")
            if not isinstance(memory, dict):
                data["memory"] = {"provider": server.hermes_memory_provider}
                changed = True
                continue

            current = memory.get("provider")
            if current is None:
                memory["provider"] = server.hermes_memory_provider
                changed = True

    return _ConfigMergeOutcome(
        config=data,
        changed=changed,
        required_provider=required_provider,
    )


def validate_hermes_config(
    data: dict[str, object],
    servers: list[McpServer],
    *,
    required_provider: str | None = None,
) -> bool:
    mcp_servers = data.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        return False
    if any(mcp_entry_drift(mcp_servers.get(server.name), server) for server in servers):
        return False

    if required_provider is None:
        return True

    memory = data.get("memory")
    if not isinstance(memory, dict):
        return False
    provider = memory.get("provider")
    return isinstance(provider, str) and provider == required_provider


def _merge_omp_mcp(
    path: Path,
    data: dict[str, object],
    servers: list[McpServer],
    *,
    remove: tuple[str, ...],
    gate: tuple[str, ...],
) -> bool:
    """Add missing servers, gate and drop names in parsed ``mcp.json`` data; True when changed.

    Raises ``ValueError`` for drifted entries or malformed blocks, which are never rewritten."""
    mcp_servers = _check_existing_mcp_entries(data, "mcpServers", servers)
    disabled = data.get("disabledServers")
    if disabled is not None and not isinstance(disabled, list):
        raise ValueError("`disabledServers` block must be a list")
    changed = False

    if mcp_servers is None:
        mcp_servers = {}
        data["mcpServers"] = mcp_servers
        changed = True
    for server in servers:
        if server.name in mcp_servers:
            skip(f"{path}: {server.name} MCP already configured")
            continue
        mcp_servers[server.name] = _json_entry(server)
        ok(f"{path}: {server.name} MCP added")
        changed = True

    if gate and disabled is None:
        disabled = []
        data["disabledServers"] = disabled
    for name in gate:
        if name not in disabled:
            disabled.append(name)
            ok(f"{path}: {name} MCP gated off (disabledServers)")
            changed = True

    for name in remove:
        if name in mcp_servers:
            del mcp_servers[name]
            ok(f"{path}: {name} MCP removed (excluded on OMP)")
            changed = True
    return changed


def _validate_omp_mcp(data: dict[str, object], servers: list[McpServer]) -> bool:
    mcp_servers = data.get("mcpServers")
    return isinstance(mcp_servers, dict) and not any(
        mcp_entry_drift(mcp_servers.get(server.name), server) for server in servers
    )


def _json_entry(server: McpServer) -> dict[str, object]:
    entry: dict[str, object] = {"command": server.command}
    if server.args:
        entry["args"] = list(server.args)
    return entry


def _configure_omp_mcp(
    path: Path,
    servers: list[McpServer],
    *,
    remove: tuple[str, ...],
    gate: tuple[str, ...],
    dry_run: bool,
) -> bool:
    data = load_json_object(path)
    if data is None:
        return False

    try:
        changed = _merge_omp_mcp(path, data, servers, remove=remove, gate=gate)
    except ValueError as exc:
        warn(f"{path}: {exc}")
        return False

    if not _validate_omp_mcp(data, servers):
        warn(f"{path}: generated config failed validation")
        return False

    if not changed:
        return True

    if not _write_atomic_text(path, json.dumps(data, indent=2) + "\n", dry_run=dry_run):
        return False
    if dry_run:
        return True

    verified = load_json_object(path)
    if verified is None or not _validate_omp_mcp(verified, servers):
        warn(f"{path}: write verification failed")
        return False
    return True


def configure_hermes(servers: list[McpServer], *, dry_run: bool) -> bool:
    path = HERMES_CONFIG_PATH
    data = load_yaml_object(path)
    if data is None:
        return False

    try:
        outcome = add_hermes_servers(data, servers)
    except ValueError as exc:
        warn(f"{path}: {exc}")
        return False

    required_provider = outcome.required_provider
    if not validate_hermes_config(
        outcome.config,
        servers,
        required_provider=required_provider,
    ):
        warn(f"{path}: post-merge validation failed")
        return False

    if not outcome.changed:
        return True

    if not _write_hermes_config(path, outcome.config, dry_run=dry_run):
        return False
    if dry_run:
        return True

    verified = load_yaml_object(path)
    if verified is None or not validate_hermes_config(
        verified,
        servers,
        required_provider=required_provider,
    ):
        warn(f"{path}: write verification failed")
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
    for path in OMP_MCP_PATHS:
        if not _configure_omp_mcp(
            path, omp_servers, remove=excluded, gate=gated, dry_run=dry_run
        ):
            ok_all = False
    return ok_all


OMP_HOOK_FILES = ("verification-recorder.ts", "retention-canary.ts")

# Settings that must hold in ~/.omp/agent/config.yml as (top-level block, key,
# value), keyed per settings-schema.ts as reviewed at OMP_VERSION
# (DECISIONS_AI_TOOLING.md "Live wiring": compaction tuning, single memory
# owner, skill-store discipline). omp_config_drift also requires every
# OMP_HOOK_FILES entry under extensions:.
OMP_AGENT_CONFIG_CONTRACT = (
    ("memory", "backend", "mnemopi"),
    ("mnemopi", "polyphonicRecall", False),
    ("compaction", "thresholdTokens", 150000),
    ("compaction", "idleEnabled", True),
    ("compaction", "handoffSaveToDisk", True),
    ("compaction", "methodOrder", ["handoff", "remote", "soft"]),
    ("skills", "enableClaudeUser", True),
    ("skills", "enableAgentsUser", False),
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


def omp_extension_paths(data: dict[str, object]) -> list[str]:
    """String entries under top-level ``extensions:``; non-list/non-string entries ignored."""
    extensions = data.get("extensions")
    if not isinstance(extensions, list):
        return []
    return [entry for entry in extensions if isinstance(entry, str)]


def omp_config_drift(data: dict[str, object]) -> list[str]:
    """Contract settings missing from a parsed OMP agent config; empty when compliant.

    Values must match with the same YAML type: ``enableClaudeUser: 1`` is drift."""
    missing: list[str] = []
    for block, key, expected in OMP_AGENT_CONFIG_CONTRACT:
        section = data.get(block)
        actual = section.get(key) if isinstance(section, dict) else None
        if type(actual) is not type(expected) or actual != expected:
            missing.append(f"{block}.{key}")
    hooks = omp_extension_paths(data)
    missing.extend(
        f"extensions.{name}" for name in OMP_HOOK_FILES
        if not any(entry.endswith(f"/{name}") for entry in hooks)
    )
    return missing


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
        if all((hooks_dir / name).is_file() for name in OMP_HOOK_FILES):
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
        hook_lines = "\n".join(f"  - {hooks_dir / name}" for name in OMP_HOOK_FILES)
        extensions = f"extensions:\n{hook_lines}\n"
        content = _OMP_AGENT_CONFIG_TEMPLATE.format(extensions=extensions)
        if not _write_atomic_text(path, content, dry_run=dry_run):
            return False
        if not dry_run:
            ok(f"{path}: agent config seeded from stack contract")
        return True

    # Existing config is user-owned YAML; OMP convergence is deliberately read-only.
    # Verify the contract and report drift instead of rewriting syntax/comments.
    data = load_yaml_object(path)
    if data is None:
        return False
    missing = omp_config_drift(data)
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


def _select(
    flag_values: list[str] | None,
    choices: list[str],
    prompt: str,
    *,
    non_interactive: bool,
) -> list[str]:
    """Flags win and `all` expands; otherwise prompt, or take everything with no terminal."""
    if flag_values is not None:
        return choices if "all" in flag_values else list(dict.fromkeys(flag_values))
    if non_interactive:
        return choices
    return choose(prompt, [Option(name, name, True) for name in choices])


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes) or not interactive()

    server_names = _select(
        args.server, list(MCP_SERVERS), "Select MCP servers", non_interactive=non_interactive
    )
    agents = _select(
        args.agent, list(AGENT_CHOICES), "Select agents", non_interactive=non_interactive
    )

    install_matching_skills = not args.no_skills
    if not non_interactive and install_matching_skills:
        install_matching_skills = ask(
            "Add matching global skills if missing",
            default=True,
            non_interactive=non_interactive,
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
