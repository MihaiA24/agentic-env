"""Configure project-memory MCP servers and global agent skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from .common import (
    Option,
    ask,
    choose,
    cmd_exists,
    interactive,
    load_json_object,
    ok,
    set_verbose,
    skip,
    warn,
    write_atomic_text,
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
_SKILL_NAMES = ("codebase-memory-mcp", "agentmemory")


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
_HOME = Path.home().resolve()
OMP_MCP_PATHS = (
    Path.home() / ".omp" / "agent" / "mcp.json",
    Path.home() / ".pi" / "agent" / "mcp.json",
)
OMP_AGENT_CONFIG_PATH = Path.home() / ".omp" / "agent" / "config.yml"
OMP_SKILL_ROOTS = (
    _HOME / ".omp" / "agent" / "skills",
    _HOME / ".pi" / "agent" / "skills",
)
HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
HERMES_SKILL_ROOT = Path.home() / ".hermes" / "skills"
# OMP loads ~/.claude/skills (skills.enableClaudeUser); ~/.agents/skills is the
# skill store and stays unmounted as a root (skills.enableAgentsUser: false).
CLAUDE_SKILL_ROOT = _HOME / ".claude" / "skills"


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
    parser.add_argument("--no-skills", action="store_true", help="Do not add or remove global skill descriptors")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions without writing files"
    )
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


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


def add_hermes_servers(data: dict[str, object], servers: list[McpServer]) -> bool:
    """Add missing servers and the required memory provider in place; True when changed.

    Raises ``ValueError`` for drifted entries or a conflicting provider, which are never rewritten."""
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
            memory = data.get("memory")
            if not isinstance(memory, dict):
                data["memory"] = {"provider": server.hermes_memory_provider}
                changed = True
                continue

            current = memory.get("provider")
            if current is None:
                memory["provider"] = server.hermes_memory_provider
                changed = True

    return changed


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
    *,
    remove: tuple[str, ...],
    gate: tuple[str, ...],
) -> bool:
    """Gate and drop names in parsed ``mcp.json`` data; True when changed.

    Raises ``ValueError`` for malformed blocks, which are never rewritten."""
    mcp_servers = data.get("mcpServers")
    if mcp_servers is not None and not isinstance(mcp_servers, dict):
        raise ValueError("`mcpServers` block must be an object; fix this file manually")
    disabled = data.get("disabledServers")
    if disabled is not None and not isinstance(disabled, list):
        raise ValueError("`disabledServers` block must be a list")
    changed = False

    if mcp_servers is None:
        mcp_servers = {}
        data["mcpServers"] = mcp_servers
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


def _converge_config(
    path: Path,
    *,
    load: Callable[[Path], dict[str, object] | None],
    merge: Callable[[dict[str, object]], bool],
    validate: Callable[[dict[str, object]], bool],
    render: Callable[[dict[str, object]], str],
    dry_run: bool,
) -> bool:
    """Read, merge in place, validate, write only when changed, then re-read and validate.

    ``merge`` raises ``ValueError`` on drift or malformed blocks; the file is then left untouched."""
    data = load(path)
    if data is None:
        return False
    try:
        changed = merge(data)
    except ValueError as exc:
        warn(f"{path}: {exc}")
        return False
    if not validate(data):
        warn(f"{path}: merged config failed validation")
        return False
    if not changed:
        return True
    if not write_atomic_text(path, render(data), dry_run=dry_run):
        return False
    if dry_run:
        return True
    verified = load(path)
    if verified is None or not validate(verified):
        warn(f"{path}: write verification failed")
        return False
    return True


def configure_hermes(servers: list[McpServer], *, dry_run: bool) -> bool:
    providers = [server.hermes_memory_provider for server in servers if server.hermes_memory_provider]
    required_provider = providers[-1] if providers else None
    return _converge_config(
        HERMES_CONFIG_PATH,
        load=load_yaml_object,
        merge=lambda data: add_hermes_servers(data, servers),
        validate=lambda data: validate_hermes_config(
            data, servers, required_provider=required_provider
        ),
        render=lambda data: yaml.safe_dump(data, sort_keys=False, allow_unicode=True) if data else "",
        dry_run=dry_run,
    )


# MCP servers deliberately absent from OMP; stale pre-existing entries are removed on converge
# and the names stay in `disabledServers` so OMP's import of another agent's config
# (~/.claude.json, ~/.codex/config.toml) cannot mount them either. lean-ctx is Rejected
# stack-wide (ADR-0009).
OMP_EXCLUDED_SERVERS = {
    "agentmemory": "ADR-0006: Mnemopi owns narrative memory on OMP",
    "lean-ctx": "ADR-0009: lean-ctx removed from the stack",
    "codebase-memory-mcp": "DECISIONS §5: litmus never fired; mount it per project",
}

# OMP built-ins with no `mcpServers` entry; kept in `disabledServers` (0 calls, DECISIONS "Rejected").
OMP_GATED_BUILTINS = ("node_repl",)

# Excluded from OMP for lack of use, not for a conflict (DECISIONS §5): Claude Code keeps
# its own entry, which `disabledServers` hides from OMP's claude-import.
CLAUDE_IMPORT_ALLOWED = ("codebase-memory-mcp",)

# Exact bytes written by older configurators, including the retired lean-ctx and ponytail bodies.
_LEGACY_DESCRIPTOR_HASHES = {
    "codebase-memory-mcp": {
        "f18fcacd95fa9cba0c4dda1792932415b29812f30bbe9f83a6ccc1f0ccd45bbb",
        "6ab32f62066cae7f2be62719f81d8a72c78053baae2a30b3884c16644c2efe50",
    },
    "lean-ctx": {
        "104f9f6a1bda181129bc6af927c47584e084d59f3d3147c966afdd21b3903b5c",
        "5f5649ac7b86c141d149818fb69fad401e79e04ee8816f37526bb6306b87c2fe",
        "5fb6d01468f2fc06de42edfb4cd542587ff172749fb768d5e6b86eaed661a1bf",
    },
    "ponytail": {"95bde9709ddc12a9385b4335552f565587c11debc9a489223f2e796e03ca8ff5"},
}

# Descriptors no longer written (2026-11-20). The ponytail stub sat in OMP's native skill
# root, which outranks the installed ponytail pack, so it took the `ponytail` name. A
# same-named skill is legitimate here, so only unmodified descriptors count as leftovers.
RETIRED_DESCRIPTORS = ("ponytail",)


def _is_claude_root(root: Path) -> bool:
    if root == CLAUDE_SKILL_ROOT:
        return True
    try:
        return root.samefile(CLAUDE_SKILL_ROOT)
    except OSError:
        return False


def excluded_descriptors() -> list[Path]:
    """Excluded descriptors in OMP-loaded roots, including unowned ones for diagnosis."""
    paths = []
    for root in dict.fromkeys((*OMP_SKILL_ROOTS, CLAUDE_SKILL_ROOT)):
        claude_root = _is_claude_root(root)
        for name in OMP_EXCLUDED_SERVERS:
            if claude_root and name in CLAUDE_IMPORT_ALLOWED:
                continue
            path = root / name
            if (path / "SKILL.md").is_file():
                paths.append(path)
    return paths


def _owned_descriptor(path: Path) -> bool:
    """The old configurator wrote a single regular file in a real directory."""
    if path.parent.resolve() != path.parent or path.is_symlink():
        return False
    descriptor = path / "SKILL.md"
    if descriptor.is_symlink() or not descriptor.is_file() or set(path.iterdir()) != {descriptor}:
        return False
    content = descriptor.read_bytes()
    skill = SKILLS.get(path.name)
    return (
        skill is not None and content == (skill.body.rstrip() + "\n").encode()
        or hashlib.sha256(content).hexdigest() in _LEGACY_DESCRIPTOR_HASHES.get(path.name, ())
    )


def retired_descriptors(roots: list[Path] | tuple[Path, ...]) -> list[Path]:
    """Unmodified retired descriptors in `roots`; anything else of that name is the user's."""
    found = []
    for root in dict.fromkeys(roots):
        for name in RETIRED_DESCRIPTORS:
            try:
                if _owned_descriptor(root / name):
                    found.append(root / name)
            except (OSError, RuntimeError):
                continue
    return found


def _remove_descriptors(paths: list[Path], *, dry_run: bool) -> bool:
    ok_all = True
    for path in paths:
        try:
            if not _owned_descriptor(path):
                warn(f"{path}: kept; not an unmodified agentic-env descriptor. Review it manually")
                continue
            if dry_run:
                skip(f"dry-run: would remove {path}")
                continue
            (path / "SKILL.md").unlink()
            path.rmdir()
        except (OSError, RuntimeError) as exc:
            warn(f"{path}: cannot remove this leftover descriptor: {exc}")
            ok_all = False
            continue
        ok(f"{path}: removed obsolete agentic-env descriptor")
    return ok_all


def remove_excluded_descriptors(*, dry_run: bool) -> bool:
    return _remove_descriptors(excluded_descriptors(), dry_run=dry_run)


def remove_retired_descriptors(agents: list[str], *, dry_run: bool) -> bool:
    return _remove_descriptors(retired_descriptors(_skill_roots(agents)), dry_run=dry_run)


def configure_omp(servers: list[McpServer], *, dry_run: bool) -> bool:
    # OMP registers no stack server: a new MCP_SERVERS entry needs a reason in OMP_EXCLUDED_SERVERS.
    for server in servers:
        skip(f"OMP config: {server.name} MCP not written ({OMP_EXCLUDED_SERVERS[server.name]})")

    excluded = tuple(OMP_EXCLUDED_SERVERS)
    gated = OMP_GATED_BUILTINS + excluded
    ok_all = True
    for path in OMP_MCP_PATHS:
        ok_all = _converge_config(
            path,
            load=load_json_object,
            merge=lambda data: _merge_omp_mcp(path, data, remove=excluded, gate=gated),
            validate=lambda data: isinstance(data.get("mcpServers"), dict),
            render=lambda data: json.dumps(data, indent=2) + "\n",
            dry_run=dry_run,
        ) and ok_all
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


def _omp_agent_config_text(hooks_dir: Path) -> str:
    sections: dict[str, dict[str, object]] = {}
    for block, key, value in OMP_AGENT_CONFIG_CONTRACT:
        sections.setdefault(block, {})[key] = value
    return yaml.safe_dump(
        {**sections, "extensions": [str(hooks_dir / name) for name in OMP_HOOK_FILES]},
        sort_keys=False,
        allow_unicode=True,
    )


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
    """Hooks live in the agentic-env checkout, never in the wheel: $AGENTIC_ENV_ROOT,
    then any ancestor of cwd or this file."""
    roots: list[Path] = []
    env_root = os.environ.get("AGENTIC_ENV_ROOT")
    if env_root:
        roots.append(Path(env_root))
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
                f"{path}: omp/hooks not found from the current directory (run from the "
                "agentic-env checkout or set AGENTIC_ENV_ROOT); not seeding a config the doctor would fail"
            )
            return False
        content = _omp_agent_config_text(hooks_dir)
        if not write_atomic_text(path, content, dry_run=dry_run):
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
    return False


def _install_skill(root: Path, skill: Skill, *, dry_run: bool) -> bool:
    skill_path = root / skill.name / "SKILL.md"
    if skill_path.exists():
        skip(f"{skill_path}: skill already present")
        return True

    content = skill.body.rstrip() + "\n"
    if not write_atomic_text(skill_path, content, dry_run=dry_run):
        return False
    if dry_run:
        return True

    if skill_path.read_text(encoding="utf-8") != content:
        warn(f"{skill_path}: write verification failed")
        return False
    ok(f"{skill_path}: skill written")
    return True


def _skill_roots(agents: list[str]) -> list[Path]:
    roots: list[Path] = []
    if "hermes" in agents:
        roots.append(HERMES_SKILL_ROOT)
    if "omp" in agents:
        roots.extend(OMP_SKILL_ROOTS)
    return roots


def install_skills(agents: list[str], server_names: list[str], *, dry_run: bool) -> bool:
    ok_all = True
    for root in _skill_roots(agents):
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
            "Add missing global skill descriptors and remove obsolete agentic-env descriptors",
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
            ok_all = remove_excluded_descriptors(dry_run=args.dry_run) and ok_all
    if install_matching_skills:
        ok_all = remove_retired_descriptors(agents, dry_run=args.dry_run) and ok_all
        ok_all = install_skills(agents, server_names, dry_run=args.dry_run) and ok_all
    else:
        skip("global skills: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
