"""Install agent skills and MCP tooling."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field

import questionary

from . import configure_agent_mcps, skill_lock
from .common import (
    Option,
    ask,
    choose,
    cmd_exists,
    cmd_version_at_least,
    install_pinned_binary_archive,
    info,
    interactive,
    ok,
    run,
    set_verbose,
    skip,
    split_csv,
    warn,
    write_atomic_text,
)
from .copy_skills import copy_skill_packages
from .remote_install_contract import validate_remote_contract
from .stack_metadata import (
    AGENTMEMORY_NPM_PACKAGE,
    CODEBASE_MEMORY_ARCHIVES,
    CODEBASE_MEMORY_RELEASE_BASE,
    SKILL_AGENTS,
    SKILL_AGENT_CLI_NAMES,
    SKILL_AGENT_LOOKUP,
    SKILLS_CLI_PACKAGE,
    STACK_VERSION_FLOORS,
    SKILLS_INSTALL_REMOTE_CONTRACT,
)

_REMOTE_INSTALL_CONTRACT = SKILLS_INSTALL_REMOTE_CONTRACT
SKILL_PACK_CONFIG_PATH = Path(__file__).with_name("skill-packs.json")
AGENT_RULES_SOURCE = Path(__file__).with_name("rules") / "AGENTS.md"
# User-level context file of the stack's managed root; OMP reads it by default.
AGENT_RULES_PATH = Path.home() / ".agents" / "AGENTS.md"
# First line of every installed rules file; a file without it is the user's own.
AGENT_RULES_HEADER = "<!-- Installed by agentic-env"
_REMOTE_SOURCE_PATTERN = re.compile(r"^(?P<repo>[\w.-]+/[\w.-]+)(?:#(?P<ref>[^#]+))?$")
_MCP_LABELS = {
    "codebase-memory-mcp": "codebase-memory-mcp (project code graph, checksum-pinned binary)",
    "agentmemory": "agentmemory (Hermes memory provider, npm)",
}


# Where selected skills go: global roots of these agents, or one exact directory.
type SkillDestination = tuple[str, ...] | Path


@dataclass(frozen=True)
class SkillUpstream:
    """The repo and revision a pack's skills come from; `path` scopes a monorepo."""

    repo: str
    ref: str
    path: str | None = None


@dataclass(frozen=True)
class SkillPack:
    name: str
    source: str
    label: str
    skills: tuple[str, ...]
    descriptions: dict[str, str] = field(default_factory=dict)
    # None when neither an `upstream` block nor an `owner/repo#ref` source pins one.
    upstream: SkillUpstream | None = None


@dataclass(frozen=True)
class SkillManifest:
    """Parsed `skill-packs.json`: packs in manifest order, alias → pack name,
    profile → pack names, and skills that have left every roster."""

    packs: dict[str, SkillPack]
    aliases: dict[str, str]
    profiles: dict[str, tuple[str, ...]]
    config_path: Path = SKILL_PACK_CONFIG_PATH
    dropped: tuple[str, ...] = ()

    def source(self, pack: str) -> str:
        """Vendored packs use a `./` source relative to the config they came from;
        the skills CLI takes the absolute path. Anything else is an upstream ref
        passed through."""
        source = self.packs[pack].source
        if source.startswith("./"):
            return str((self.config_path.parent / source[2:]).resolve())
        return source


@dataclass(frozen=True)
class SkillPackSelection:
    selected: tuple[str, ...]
    unknown: tuple[str, ...]


@dataclass(frozen=True)
class SkillAgentSelection:
    selected: tuple[str, ...]
    unknown: tuple[str, ...]


@dataclass(frozen=True)
class SkillInstallPlan:
    skill_packs: tuple[str, ...]
    skill_names: tuple[str, ...]
    destination: SkillDestination
    do_codebase: bool
    do_agentmemory: bool
    do_agent_rules: bool


def _parse_skill_pack_config(payload: object, path: Path) -> SkillManifest | None:
    if not isinstance(payload, dict):
        warn(f"Invalid skill-pack config in {path}: expected object")
        return None

    packs_payload = payload.get("packs")
    if not isinstance(packs_payload, list) or not packs_payload:
        warn(f"Invalid skill-pack config in {path}: 'packs' must be a non-empty list")
        return None

    packs: dict[str, SkillPack] = {}
    alias_lookup: dict[str, str] = {}

    for item in packs_payload:
        if not isinstance(item, dict):
            warn(f"Invalid pack entry in {path}: {item!r}")
            return None

        name = item.get("name")
        source = item.get("source")
        label = item.get("label", f"{name} skill")

        if not isinstance(name, str) or not name.strip():
            warn(f"Invalid pack name in {path}: {name!r}")
            return None
        if not isinstance(source, str) or not source.strip():
            warn(f"Invalid source for pack '{name}' in {path}: {source!r}")
            return None
        if not isinstance(label, str) or not label.strip():
            warn(f"Invalid label for pack '{name}' in {path}: {label!r}")
            return None

        canonical_name = name.strip().lower()
        source_value = source.strip()
        label_value = label.strip()

        if canonical_name in packs:
            warn(f"Duplicate pack '{canonical_name}' in {path}")
            return None

        aliases_payload = item.get("aliases", [])
        if not isinstance(aliases_payload, list):
            warn(f"Invalid aliases for pack '{name}' in {path}: expected list")
            return None

        skills_payload = item.get("skills", [])
        if not isinstance(skills_payload, list):
            warn(f"Invalid skills filter for pack '{name}' in {path}: expected list")
            return None

        skill_values: list[str] = []
        skill_descriptions: dict[str, str] = {}
        for raw_skill in skills_payload:
            if isinstance(raw_skill, str):
                skill, description = raw_skill.strip(), ""
            elif isinstance(raw_skill, dict) and isinstance(raw_skill.get("name"), str):
                skill = raw_skill["name"].strip()
                description = str(raw_skill.get("description", "")).strip()
            else:
                warn(f"Invalid skill value for pack '{name}' in {path}: {raw_skill!r}")
                return None
            if skill and skill not in skill_values:
                skill_values.append(skill)
                if description:
                    skill_descriptions[skill] = description

        raw_aliases: list[str] = []
        for raw_alias in aliases_payload:
            if not isinstance(raw_alias, str):
                warn(f"Invalid alias for pack '{name}' in {path}: {raw_alias!r}")
                return None
            alias = raw_alias.strip().lower()
            if alias:
                raw_aliases.append(alias)

        resolved_aliases = [canonical_name, source_value.lower(), *raw_aliases]

        for alias in dict.fromkeys(resolved_aliases):
            existing = alias_lookup.get(alias)
            if existing is None:
                alias_lookup[alias] = canonical_name
            elif existing != canonical_name:
                warn(
                    f"Alias '{alias}' maps to both '{existing}' and '{canonical_name}' in {path}"
                )
                return None

        upstream_payload = item.get("upstream", {})
        if not isinstance(upstream_payload, dict):
            warn(f"Invalid upstream for pack '{name}' in {path}: expected object")
            return None

        upstream_fields: dict[str, str] = {}
        for key in ("repo", "ref", "path"):
            value = upstream_payload.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                warn(f"Invalid upstream {key} for pack '{name}' in {path}: {value!r}")
                return None
            upstream_fields[key] = value.strip()

        # Resolve available metadata once; legacy partial blocks remain usable
        # for installation but cannot support an upstream comparison.
        remote = None if source_value.startswith("./") else _REMOTE_SOURCE_PATTERN.fullmatch(source_value)
        repo = upstream_fields.get("repo") or (remote["repo"] if remote else None)
        ref = upstream_fields.get("ref") or (remote["ref"] if remote else None)
        if repo is not None and ref is not None:
            upstream = SkillUpstream(repo=repo, ref=ref, path=upstream_fields.get("path"))
        else:
            upstream = None

        packs[canonical_name] = SkillPack(
            name=canonical_name,
            source=source_value,
            label=label_value,
            skills=tuple(skill_values),
            descriptions=skill_descriptions,
            upstream=upstream,
        )

    profiles_payload = payload.get("profiles", {"default": list(packs)})
    if not isinstance(profiles_payload, dict):
        warn(f"Invalid 'profiles' in {path}: expected object")
        return None

    profiles: dict[str, tuple[str, ...]] = {}
    for profile_name, pack_values in profiles_payload.items():
        if not isinstance(profile_name, str) or not profile_name.strip():
            warn(f"Invalid profile name in {path}: {profile_name!r}")
            return None

        if not isinstance(pack_values, list) or not all(isinstance(item, str) for item in pack_values):
            warn(f"Invalid profile '{profile_name}' in {path}: expected list of pack names")
            return None

        selected: list[str] = []
        for raw_pack in pack_values:
            canonical_pack = str(raw_pack).strip().lower()
            if not canonical_pack:
                warn(f"Profile '{profile_name}' references unknown pack '{raw_pack}' in {path}")
                return None
            if canonical_pack not in packs:
                warn(f"Profile '{profile_name}' references unknown pack '{raw_pack}' in {path}")
                return None
            if canonical_pack not in selected:
                selected.append(canonical_pack)

        profiles[profile_name.strip()] = tuple(selected)

    dropped_payload = payload.get("dropped", [])
    if not isinstance(dropped_payload, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[a-z0-9][a-z0-9_-]*", item.strip())
        for item in dropped_payload
    ):
        warn(f"Invalid 'dropped' in {path}: expected list of skill slugs")
        return None
    dropped = tuple(dict.fromkeys(item.strip() for item in dropped_payload))
    rostered = [name for name in dropped if any(name in pack.skills for pack in packs.values())]
    if rostered:
        warn(f"Dropped skill(s) still in a pack roster in {path}: {', '.join(rostered)}")
        return None

    return SkillManifest(
        packs=packs, aliases=alias_lookup, profiles=profiles, config_path=path, dropped=dropped
    )


def load_skill_manifest(path: Path) -> SkillManifest | None:
    if not path.exists():
        warn(f"Skill pack config not found: {path}")
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warn(f"Invalid JSON in {path}: {exc}")
        return None
    except OSError as exc:
        warn(f"Cannot read {path}: {exc}")
        return None

    return _parse_skill_pack_config(payload, path)


def _validate_remote_contract() -> bool:
    return validate_remote_contract(
        _REMOTE_INSTALL_CONTRACT, scope="agentic-install-skills-mcps"
    )


def _parse_skill_packs(values: list[str] | None, manifest: SkillManifest) -> SkillPackSelection:
    selected: list[str] = []
    unknown: list[str] = []
    aliases = manifest.aliases

    for raw in split_csv(values):
        name = raw.strip().lower()
        if not name:
            continue
        canonical = aliases.get(name)
        if canonical is None:
            unknown.append(raw.strip())
            continue
        if canonical not in selected:
            selected.append(canonical)

    return SkillPackSelection(selected=tuple(selected), unknown=tuple(unknown))


def _parse_skill_names(values: list[str] | None) -> tuple[str, ...]:
    requested: list[str] = []
    for name in split_csv(values):
        if name not in requested:
            requested.append(name)
    return tuple(requested)


def _parse_skill_agents(values: list[str] | None) -> SkillAgentSelection:
    selected: list[str] = []
    unknown: list[str] = []

    for raw in split_csv(values):
        value = raw.strip().lower()
        if not value:
            continue
        if value == "all":
            return SkillAgentSelection(selected=_all_skill_agents(), unknown=())

        canonical = SKILL_AGENT_LOOKUP.get(value)
        if canonical is None:
            unknown.append(raw.strip())
            continue
        if canonical not in selected:
            selected.append(canonical)

    return SkillAgentSelection(selected=tuple(selected), unknown=tuple(unknown))


def _all_skill_agents() -> tuple[str, ...]:
    return tuple(agent for agent, _, _ in SKILL_AGENTS)


def _build_install_plan(
    args: argparse.Namespace, manifest: SkillManifest
) -> SkillInstallPlan | None:
    if args.converge and (args.skill_pack or args.skill or args.all_skills or args.skills_dir is not None):
        warn("--converge cannot be combined with --skill-pack, --skill, --all-skills or --skills-dir")
        return None
    if args.skills_dir is not None and (
        args.skill_agent or args.mcp or args.all_mcps or args.agent_rules
    ):
        warn("--skills-dir cannot be combined with --skill-agent, --mcp, --all-mcps or --agent-rules")
        return None

    pack_selection = _parse_skill_packs(args.skill_pack, manifest)
    if pack_selection.unknown:
        warn(f"Unknown skill pack(s): {', '.join(sorted(pack_selection.unknown))}")
        warn(f"Available: {', '.join(manifest.packs)}")
        return None

    selected_skill_agents = _parse_skill_agents(args.skill_agent)
    if selected_skill_agents.unknown:
        warn(f"Unknown skill agent(s): {', '.join(sorted(selected_skill_agents.unknown))}")
        warn(f"Available: {', '.join(_all_skill_agents())}")
        return None

    skill_names = _parse_skill_names(args.skill)

    if args.all_skills:
        selected_skill_packs = list(manifest.packs)
    elif pack_selection.selected:
        selected_skill_packs = list(pack_selection.selected)
    elif args.skill_profile:
        profile_name = args.skill_profile.strip()
        if not profile_name:
            warn("Empty --skill-profile value")
            return None

        profile = manifest.profiles.get(profile_name)
        if profile is None:
            warn(f"Unknown skill profile: {profile_name}")
            warn(f"Available: {', '.join(manifest.profiles)}")
            return None

        selected_skill_packs = list(profile)
    else:
        selected_skill_packs = []

    # Names are checkable only when every selected pack ships a roster; a pack
    # without one takes whatever `--skill` names it is given.
    rosters = [manifest.packs[name].skills for name in selected_skill_packs]
    if skill_names and rosters and all(rosters):
        known = [skill for roster in rosters for skill in roster]
        unknown_skills = [name for name in skill_names if name not in known]
        if unknown_skills:
            warn(f"Unknown skill(s) for the selected packs: {', '.join(unknown_skills)}")
            warn(f"Available: {', '.join(dict.fromkeys(known))}")
            return None

    requested_mcps = [name.lower() for name in split_csv(args.mcp)]
    unknown_mcps = [name for name in requested_mcps if name not in _MCP_LABELS]
    if unknown_mcps:
        warn(f"Unknown MCP server(s): {', '.join(unknown_mcps)}")
        warn(f"Available: {', '.join(_MCP_LABELS)}")
        return None

    destination: SkillDestination = (
        args.skills_dir.expanduser().resolve()
        if args.skills_dir is not None
        else selected_skill_agents.selected or _all_skill_agents()
    )
    return SkillInstallPlan(
        skill_packs=tuple(selected_skill_packs),
        skill_names=skill_names,
        destination=destination,
        do_codebase=bool(args.all_mcps) or "codebase-memory-mcp" in requested_mcps,
        do_agentmemory=bool(args.all_mcps) or "agentmemory" in requested_mcps,
        do_agent_rules=bool(args.agent_rules),
    )


def _pick_skills(manifest: SkillManifest, requested: list[str]) -> dict[str, list[str]]:
    """One row per skill under a pack heading, plus a row that takes the whole pack.

    Returns pack -> skill filter, where an empty filter installs whatever the pack
    ships. Without `--skill` the pre-checked rows are the whole packs of the
    `default` profile; with it, only the matching skill rows start checked.
    """
    default_packs = manifest.profiles.get("default")
    rows: list[Option | str] = []
    for pack in manifest.packs.values():
        in_default = default_packs is None or pack.name in default_packs
        count = f" ({len(pack.skills)} skills)" if pack.skills else ""
        rows.append(pack.label)
        rows.append(
            Option(f"{pack.name}/", f"All of {pack.label}{count}", in_default and not requested)
        )
        rows.extend(
            Option(
                f"{pack.name}/{skill}",
                skill,
                in_default and skill in requested,
                pack.descriptions.get(skill),
            )
            for skill in pack.skills
        )

    selection: dict[str, list[str]] = {}
    whole_packs: list[str] = []
    for value in choose("Select skills to install", rows):
        pack_name, _, skill = value.partition("/")
        skills = selection.setdefault(pack_name, [])
        if not skill:
            whole_packs.append(pack_name)
        elif skill not in skills:
            skills.append(skill)
    for pack_name in whole_packs:
        selection[pack_name] = list(manifest.packs[pack_name].skills)
    return selection


def _pick_skill_destination() -> SkillDestination:
    destination = questionary.select(
        "Install skills where?",
        choices=[
            questionary.Choice("Supported harnesses (managed skill directories)", value="agents"),
            questionary.Choice("Other / custom directory", value="directory"),
        ],
    ).ask()
    if destination is None:
        raise SystemExit(130)
    if destination == "agents":
        return tuple(
            choose(
                "Install skills for which agents?",
                [Option(agent, label, True) for agent, _, label in SKILL_AGENTS],
            )
        )
    path = questionary.path(
        "Skills directory (exact folder)",
        only_directories=True,
        validate=lambda value: bool(value.strip()) or "Enter a skills directory",
    ).ask()
    if path is None:
        raise SystemExit(130)
    try:
        return Path(path).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        warn(f"Invalid skills directory: {exc}")
        raise SystemExit(1) from exc


def _command_path_on_path(
    binary: str, extra_paths: list[Path] | None = None
) -> str | None:
    extra: list[str] = [str(path) for path in (extra_paths or [])]
    system_path = os.environ.get("PATH", "")
    if system_path:
        extra.append(system_path)
    search_path = os.pathsep.join(extra) if extra else None
    return shutil.which(binary, path=search_path)


def _should_install_mcp(binary: str, label: str, non_interactive: bool) -> bool:
    if cmd_version_at_least(binary, STACK_VERSION_FLOORS[binary]):
        if not ask(
            f"Reinstall {label}", default=False, non_interactive=non_interactive
        ):
            skip(f"{label}: at or above the reviewed version")
            return False
    elif cmd_exists(binary):
        warn(f"{label}: below the reviewed version; converging")
    return True


def _platform_key() -> tuple[str, str] | None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    architecture = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine)
    if system not in {"darwin", "linux"} or architecture is None:
        warn(f"Unsupported platform: {system}/{machine}")
        return None
    return system, architecture


def _is_npm_permission_error(exc: subprocess.CalledProcessError) -> bool:
    message = (exc.stderr or "") + (exc.stdout or "")
    lower = message.lower()
    return "eacces" in lower or "permission denied" in lower


def _install_agentmemory_user_local(package: str) -> bool:
    local_prefix = Path.home() / ".local" / "agentmemory"
    try:
        run(["npm", "install", "--prefix", str(local_prefix), "-g", package])
    except subprocess.CalledProcessError:
        warn(f"agentmemory: local npm install failed for prefix {local_prefix}")
        return False
    binary_path = local_prefix / "bin" / "agentmemory"
    if not binary_path.exists():
        warn(
            f"agentmemory fallback install succeeded but binary missing: {binary_path}"
        )
        return False

    user_bin_dir = Path.home() / ".local" / "bin"
    user_bin_dir.mkdir(parents=True, exist_ok=True)
    shim_path = user_bin_dir / "agentmemory"
    try:
        shim_path.unlink(missing_ok=True)
        shim_path.symlink_to(binary_path)
    except OSError as exc:
        warn(f"agentmemory: failed to write local shim {shim_path}: {exc}")
        return False

    resolved_path = _command_path_on_path("agentmemory", extra_paths=[user_bin_dir])
    if resolved_path is None:
        warn("agentmemory: fallback install completed but command is not resolvable")
        warn("PATH remediation: add ~/.local/bin to PATH and rerun")
        warn('Example: export PATH="$HOME/.local/bin:$PATH"')
        return False


    ok(f"agentmemory: installed to user-local npm prefix {local_prefix}")
    ok(f"agentmemory command resolved at: {resolved_path}")
    skip(
        "PATH may not include ~/.local/bin automatically; add it to use the fallback binary"
    )
    return True


def _install_npm_global(package: str, label: str) -> bool:
    try:
        run(["npm", "install", "-g", package])
        if _command_path_on_path(label) is None:
            warn(f"{label}: install succeeded but command is not resolvable")
            warn("PATH remediation: ensure npm global bin is on PATH")
            return False
        ok(f"{label}: installed")
        return True
    except subprocess.CalledProcessError as exc:
        if not _is_npm_permission_error(exc):
            warn(f"{label}: npm install failed")
            return False
        warn(f"{label}: global npm install blocked by permissions")
        return _install_agentmemory_user_local(package)


def _resolve_pack_skills(
    manifest: SkillManifest, packs: list[str], requested: list[str]
) -> dict[str, list[str]]:
    """Pack -> skill filter to pass to `skills add`; [] means the entire pack."""
    selection: dict[str, list[str]] = {}
    for name in packs:
        pack = manifest.packs[name]
        if not pack.skills:
            selection[name] = list(requested)
        elif not requested:
            selection[name] = list(pack.skills)
        else:
            filtered = [skill for skill in requested if skill in pack.skills]
            if not filtered:
                warn(f"{pack.label}: no requested skills matched this pack's filter; skipped")
                continue
            selection[name] = filtered
    return selection


def _summarize_selection(
    manifest: SkillManifest,
    selection: dict[str, list[str]],
    destination: SkillDestination,
    do_codebase: bool,
    do_agentmemory: bool,
    do_agent_rules: bool = False,
) -> None:
    for name, skills in selection.items():
        pack = manifest.packs[name]
        if not skills:
            detail = "everything the pack ships"
        elif tuple(skills) == pack.skills:
            detail = f"whole pack ({len(skills)} skills)"
        else:
            detail = ", ".join(skills)
        info(f"{pack.label}: {detail}")
    if selection:
        if isinstance(destination, Path):
            info(f"Skill destination: {destination}")
        else:
            info(f"Skill target agents: {', '.join(destination)}")
    for name, wanted in (("codebase-memory-mcp", do_codebase), ("agentmemory", do_agentmemory)):
        if wanted:
            info(f"MCP server: {name}")
    if do_agent_rules:
        info(f"Agent rules: {AGENT_RULES_PATH}")


def _replay_command(
    manifest: SkillManifest,
    selection: dict[str, list[str]],
    destination: SkillDestination,
    do_codebase: bool,
    do_agentmemory: bool,
    do_agent_rules: bool = False,
) -> str | None:
    """The flag-only command that repeats this selection, or None when the flags
    cannot express it because `--skill` would widen a per-pack subset."""
    packs = list(selection)
    skills: list[str] = []
    for names in selection.values():
        skills.extend(name for name in names if name not in skills)
    # Whole rosters need no `--skill`, so try the short form before the long one.
    if packs and _resolve_pack_skills(manifest, packs, []) == selection:
        skills = []
    elif packs and _resolve_pack_skills(manifest, packs, skills) != selection:
        return None

    parts = ["agentic-install-skills-mcps"]
    if packs:
        if manifest.config_path != SKILL_PACK_CONFIG_PATH:
            parts.append(f"--skill-config {shlex.quote(str(manifest.config_path.resolve()))}")
        parts.append(f"--skill-pack {','.join(packs)}")
        if skills:
            parts.append(f"--skill {','.join(skills)}")
        if isinstance(destination, Path):
            parts.append(f"--skills-dir {shlex.quote(str(destination))}")
        else:
            parts.append(f"--skill-agent {','.join(destination)}")
    mcps = [
        name
        for name, wanted in (("codebase-memory-mcp", do_codebase), ("agentmemory", do_agentmemory))
        if wanted
    ]
    if len(mcps) == len(_MCP_LABELS):
        parts.append("--all-mcps")
    elif mcps:
        parts.append(f"--mcp {','.join(mcps)}")
    if do_agent_rules:
        parts.append("--agent-rules")
    parts.append("--yes")
    return " ".join(parts)


def _install_skills(
    manifest: SkillManifest,
    selection: dict[str, list[str]],
    destination: SkillDestination,
    *,
    non_interactive: bool = True,
) -> bool:
    if isinstance(destination, Path):
        return _install_skill_directory(
            manifest, selection, destination, non_interactive=non_interactive
        )

    if not cmd_exists("skills") and not cmd_exists("npm"):
        warn("skills CLI requires npm or a global skills binary")
        return False

    if not destination:
        warn("No target agents selected for skill installation")
        return False

    for name, skills in selection.items():
        if not _install_skill_package(manifest.source(name), skills, destination):
            warn(f"{manifest.packs[name].label}: installation failed")
            return False
    return True


def _install_skill_directory(
    manifest: SkillManifest,
    selection: dict[str, list[str]],
    destination: Path,
    *,
    non_interactive: bool,
) -> bool:
    """Copy selected packages into the exact destination with Python alone, on any OS:
    vendored packs from this checkout, remote packs from their pinned GitHub tarball."""
    from .skill_drift import locate_skill, source_root  # skill_drift imports this module

    wanted: dict[str, list[str]] = {}
    for name, skills in selection.items():
        pack = manifest.packs[name]
        wanted[name] = skills or pack.skills
        if not wanted[name]:
            warn(f"{pack.label}: no skill roster; name the skills with --skill")
            return False
    # Packages land at destination/<skill name>, so collisions are known before any download.
    existing = [
        skill
        for names in wanted.values()
        for skill in names
        if (destination / skill).exists() or (destination / skill).is_symlink()
    ]
    if existing:
        if non_interactive:
            warn(
                f"Already in {destination}: {', '.join(existing)}; "
                "rerun on a terminal without --yes to choose overwriting them"
            )
            return False
        if not ask(
            f"Overwrite {len(existing)} existing skill(s) in {destination}: "
            f"{', '.join(existing)}? Local changes in them are lost",
            default=False,
            non_interactive=False,
        ):
            skip("existing skills kept; nothing installed")
            return True
    packages: list[Path] = []
    for name, names in wanted.items():
        pack = manifest.packs[name]
        info(f"Fetching {', '.join(names)} from {pack.source}...")
        root = source_root(manifest, name, pack.upstream, offline=False)
        for skill in names:
            package = locate_skill(root, skill)
            if package is None:
                warn(f"{pack.label}: {skill} not found in {pack.source}")
                return False
            packages.append(package)
    try:
        copy_skill_packages(packages, destination, replace=existing)
    except (OSError, ValueError) as exc:
        warn(f"Directory skill installation failed: {exc}")
        return False
    ok(f"Installed skill packages: {len(packages)} in {destination}")
    return True


def _skills_cli() -> list[str] | None:
    """The command that runs a skills CLI at or above the reviewed floor: the global
    binary when it qualifies, else the npx package; None when neither does."""
    if cmd_version_at_least("skills", STACK_VERSION_FLOORS["skills"]):
        return ["skills"]
    if not cmd_exists("npm"):
        warn("The curated skills CLI requires npm")
        return None
    if not cmd_version_at_least(
        "npx",
        STACK_VERSION_FLOORS["skills"],
        args=("--yes", SKILLS_CLI_PACKAGE, "--version"),
    ):
        warn("skills CLI: could not verify a version at or above the reviewed floor")
        return None
    return ["npx", "--yes", SKILLS_CLI_PACKAGE]


def _install_skill_package(source: str, skills: list[str], agents: tuple[str, ...]) -> bool:
    """`skills add` into the agents' global roots."""
    command = ["add", source, "--yes", "--global"]
    for skill in skills:
        command.extend(["--skill", skill])
    for skill_agent in agents:
        command.extend(["--agent", SKILL_AGENT_CLI_NAMES[skill_agent]])

    if skills:
        info(f"Installing skills: {', '.join(skills)} from {source}...")
    else:
        info(f"Installing skill pack: {source}...")

    runner = _skills_cli()
    if runner is None:
        return False
    try:
        run([*runner, *command])
    except (OSError, subprocess.CalledProcessError) as exc:
        warn(f"skills CLI failed for {source}: {exc}")
        return False
    return True


def _install_agentmemory(non_interactive: bool, *, update: bool = False) -> bool:
    """Install agentmemory and wire it into Hermes; `update` installs the latest
    release even when an installed one meets the floor."""
    if not update and not _should_install_mcp("agentmemory", "agentmemory", non_interactive):
        return True
    if not cmd_exists("npm"):
        warn("npm is required to install agentmemory")
        return False

    info("Installing agentmemory...")
    if not _install_npm_global(AGENTMEMORY_NPM_PACKAGE, "agentmemory"):
        return False
    if not cmd_version_at_least("agentmemory", STACK_VERSION_FLOORS["agentmemory"]):
        warn("agentmemory: installed version is below the reviewed version")
        return False

    return (
        configure_agent_mcps.main(
            ["--server", "agentmemory", "--agent", "hermes", "--yes", "--no-skills"]
        )
        == 0
    )


def _install_codebase_memory(with_ui: bool, non_interactive: bool) -> bool:
    if not _should_install_mcp(
        "codebase-memory-mcp", "codebase-memory-mcp", non_interactive
    ):
        return True
    platform_key = _platform_key()
    if platform_key is None:
        return False
    archive_name, checksum = CODEBASE_MEMORY_ARCHIVES[(*platform_key, with_ui)]

    info("Installing codebase-memory-mcp...")
    if not install_pinned_binary_archive(
        label="codebase-memory-mcp",
        binary="codebase-memory-mcp",
        url=f"{CODEBASE_MEMORY_RELEASE_BASE}/{archive_name}",
        expected_sha256=checksum,
    ):
        return False
    binary = str(Path.home() / ".local" / "bin" / "codebase-memory-mcp")
    if not cmd_version_at_least(binary, STACK_VERSION_FLOORS["codebase-memory-mcp"]):
        warn("codebase-memory-mcp: installed version is below the reviewed version")
        return False
    ok("codebase-memory-mcp: installed" + (" (with UI)" if with_ui else ""))
    return True


def _user_agent_rules() -> bool:
    """An existing rules file without the managed header: installing replaces it."""
    # Bytes: a user's file need not be UTF-8.
    return AGENT_RULES_PATH.is_file() and not AGENT_RULES_PATH.read_bytes().startswith(
        AGENT_RULES_HEADER.encode()
    )


def _install_agent_rules() -> bool:
    """Write the generic rules to the managed user-level context file. A file the
    user wrote stays beside it as `AGENTS.md.agentic-env.bak`; replacing a managed
    file takes no backup, so updates never overwrite the user's copy."""
    content = AGENT_RULES_SOURCE.read_text(encoding="utf-8")
    if AGENT_RULES_PATH.is_file() and AGENT_RULES_PATH.read_bytes() == content.encode("utf-8"):
        ok(f"agent rules: already current at {AGENT_RULES_PATH}")
        return True
    if not write_atomic_text(
        AGENT_RULES_PATH, content, dry_run=False, backup=_user_agent_rules()
    ):
        return False
    ok(f"agent rules: installed at {AGENT_RULES_PATH}")
    return True


def _update_skills_cli() -> bool:
    """Keep a global `skills` binary at the latest release. Without one, installs
    run the floor-checked npx package and there is nothing to update."""
    if not cmd_exists("skills"):
        return True
    if not cmd_exists("npm"):
        warn("skills CLI: npm is required to update it")
        return False
    info("Updating the skills CLI...")
    try:
        run(["npm", "install", "-g", SKILLS_CLI_PACKAGE])
    except (OSError, subprocess.CalledProcessError) as exc:
        warn(f"skills CLI: update failed: {exc}")
        return False
    if not cmd_version_at_least("skills", STACK_VERSION_FLOORS["skills"]):
        warn("skills CLI: installed version is below the reviewed version")
        return False
    ok("skills CLI: updated")
    return True


def _converge_selection(
    manifest: SkillManifest,
    profile_packs: tuple[str, ...],
    lock: dict[str, dict],
    offered: set[str],
) -> tuple[dict[str, list[str]], list[str]]:
    """What a converge run installs, and the roster skills to offer for the first time.

    A host holding roster skills refreshes exactly those. A host that holds none
    and was never offered any is new, and takes the profile packs.
    """
    held = {
        pack.name: [skill for skill in pack.skills if skill in lock]
        for pack in manifest.packs.values()
    }
    selection = {pack: skills for pack, skills in held.items() if skills}
    if not selection and not offered:
        selection = _resolve_pack_skills(manifest, list(profile_packs), [])
    chosen = {skill for skills in selection.values() for skill in skills}
    offer = [
        skill
        for pack in manifest.packs.values()
        for skill in pack.skills
        if skill not in chosen and skill not in lock and skill not in offered
    ]
    return selection, list(dict.fromkeys(offer))


def _pick_offered(manifest: SkillManifest, offer: list[str]) -> dict[str, list[str]]:
    """Ask about roster skills this host lacks; those of `default` packs start checked."""
    default_packs = manifest.profiles.get("default", ())
    rows: list[Option | str] = []
    for pack in manifest.packs.values():
        skills = [skill for skill in pack.skills if skill in offer]
        if skills:
            rows.append(pack.label)
            rows.extend(
                Option(
                    f"{pack.name}/{skill}",
                    skill,
                    pack.name in default_packs,
                    pack.descriptions.get(skill),
                )
                for skill in skills
            )
    picked: dict[str, list[str]] = {}
    for value in choose(
        "Install skills this host does not have? Asked once: unchecked skills are not offered again",
        rows,
    ):
        pack_name, _, skill = value.partition("/")
        picked.setdefault(pack_name, []).append(skill)
    return picked


def _from_pack(manifest: SkillManifest, entry: dict) -> bool:
    """Require the exact local pack path or a configured remote repository."""
    source = entry.get("source")
    if not isinstance(source, str):
        return False
    return any(
        source == manifest.source(pack.name)
        if pack.source.startswith("./")
        else source.lower() == pack.source.partition("#")[0].lower()
        for pack in manifest.packs.values()
    )


def _installed_paths(name: str) -> list[Path]:
    """The canonical store and the agent roots this installer can target."""
    home = Path.home().resolve()
    roots = [skill_lock.CANONICAL_SKILL_ROOT]
    for variable, default in (("CLAUDE_CONFIG_DIR", ".claude"), ("HERMES_HOME", ".hermes")):
        roots.append(home / default / "skills")
        if override := os.environ.get(variable, "").strip():
            roots.append(Path(override) / "skills")
    paths = []
    for root in dict.fromkeys(roots):
        path = root / name
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        paths.append(path)
    return paths


def _managed_links(folder: Path, paths: list[Path]) -> list[Path] | None:
    """The links to the canonical installation, or None for independent copies."""
    links = []
    for path in paths:
        # A root may itself be an alias of the canonical store. Do not modify
        # entries beneath any other aliased root.
        root = path.parent.resolve()
        if root == folder.parent:
            continue
        if root != path.parent.absolute() or not path.is_symlink() or path.resolve(strict=True) != folder:
            return None
        links.append(path)
    return list(dict.fromkeys(links))


def _prune_dropped(manifest: SkillManifest, lock: skill_lock.SkillLock) -> tuple[bool, list[str]]:
    """Delete only a verified canonical folder and the known aliases into it."""
    removed: list[str] = []
    ok_all = True
    for name in manifest.dropped:
        folder = skill_lock.CANONICAL_SKILL_ROOT / name
        entry = lock.skills.get(name)
        try:
            paths = _installed_paths(name)
            if not paths and entry is None:
                continue
            reason = None
            if entry is None:
                reason = "no skills lock record"
            elif not _from_pack(manifest, entry):
                reason = f"source {entry.get('source')} does not match a curated pack"
            elif folder.parent.resolve() != folder.parent or not skill_lock.matches_record(folder, entry):
                reason = f"cannot verify unchanged canonical folder {folder}"
            elif (links := _managed_links(folder, paths)) is None:
                reason = "an independent copy or link is installed"
            if reason is not None:
                warn(f"{name}: left the roster but kept: {reason}. Review the installed paths manually")
                continue
        except (OSError, RuntimeError, UnicodeError) as exc:
            warn(f"{name}: left the roster but kept: cannot verify installation ({exc})")
            continue

        try:
            for link in links:
                link.unlink()
            shutil.rmtree(folder)
        except OSError as exc:
            warn(f"{name}: could not remove the obsolete installation: {exc}")
            ok_all = False
            continue
        removed.append(name)
        ok(f"{name}: removed unchanged skill that left the roster")
    return ok_all, removed


def _converge(manifest: SkillManifest, plan: SkillInstallPlan, prompt: bool) -> int:
    """Bring this host up to date without asking anything twice (`--converge`)."""
    try:
        lock = skill_lock.load_lock()
    except skill_lock.InvalidLock as exc:
        warn(str(exc))
        return 1
    selection, offer = _converge_selection(manifest, plan.skill_packs, lock.skills, lock.offered)
    asked = bool(offer) and prompt
    if asked:
        for pack, skills in _pick_offered(manifest, offer).items():
            selection.setdefault(pack, []).extend(skills)
    elif offer:
        skip(f"Not offered with --yes or without a terminal: {', '.join(offer)}")

    ok_all = _update_skills_cli()
    _summarize_selection(
        manifest, selection, plan.destination,
        plan.do_codebase, plan.do_agentmemory, plan.do_agent_rules,
    )
    if selection:
        ok_all = _install_skills(manifest, selection, plan.destination) and ok_all
    else:
        skip("skill packs: no roster skill on this host")
    # Native installs may have changed the lock since we planned the selection.
    try:
        lock = skill_lock.load_lock()
    except skill_lock.InvalidLock as exc:
        warn(str(exc))
        return 1
    pruned, removed = _prune_dropped(manifest, lock)
    ok_all = pruned and ok_all
    if removed or asked:
        ok_all = lock.record_changes(removed=removed, offered=offer if asked else []) and ok_all

    if plan.do_codebase:
        # Pinned: reinstalls only below the reviewed version.
        ok_all = _install_codebase_memory(True, True) and ok_all
    if plan.do_agentmemory:
        ok_all = _install_agentmemory(True, update=True) and ok_all
    if plan.do_agent_rules:
        ok_all = _install_agent_rules() and ok_all
    return 0 if ok_all else 1


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install shared skills and MCP tooling. "
            "Returns non-zero on any selected-step failure."
        )
    )
    parser.add_argument(
        "--all-skills", action="store_true", help="Install all skills without prompting"
    )
    parser.add_argument(
        "--skill-pack",
        action="append",
        help=(
            "Install one or more skill packs (for example: mattpocock, ponytail). "
            "Repeat or use commas."
        ),
    )
    parser.add_argument(
        "--skill",
        action="append",
        help=(
            "Install only these skill names from the selected packs (repeat or use commas). "
            "Requires the skills CLI --skill filter."
        ),
    )
    parser.add_argument(
        "--skill-agent",
        action="append",
        help=(
            "Install to specific agents (for example: hermes, claude, codex). "
            "Repeat or use commas. Defaults to all configured targets."
        ),
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        metavar="PATH",
        help="Copy selected skill packages into this exact directory instead of global agent roots.",
    )
    parser.add_argument(
        "--skill-profile",
        metavar="NAME",
        help=(
            "Install packs from this profile in the skill pack config. "
            "No profile is selected by default in non-interactive mode."
        ),
    )
    parser.add_argument(
        "--skill-config",
        metavar="PATH",
        default=str(SKILL_PACK_CONFIG_PATH),
        help="Path to JSON skill pack config (packs + profiles).",
    )
    parser.add_argument(
        "--all-mcps",
        action="store_true",
        help="Install all MCPs without prompting",
    )
    parser.add_argument(
        "--mcp",
        action="append",
        help=(
            f"Install only these MCP servers ({', '.join(_MCP_LABELS)}). "
            "Repeat or use commas."
        ),
    )
    parser.add_argument(
        "--agent-rules",
        action="store_true",
        help=(
            "Install the recommended generic agent rules to ~/.agents/AGENTS.md "
            "(the previous file is kept as a backup)."
        ),
    )
    parser.add_argument(
        "--converge",
        action="store_true",
        help=(
            "Bring this host up to date: refresh the roster skills it has (a host with "
            "none takes --skill-profile), offer each missing roster skill once on a "
            "terminal, remove dropped skills unchanged since install, update a global "
            "skills CLI and the selected MCPs. agentic-bootstrap runs this."
        ),
    )
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    parser.add_argument(
        "--verbose", action="store_true", help="Show full command output"
    )
    parser.add_argument(
        "--verify-remote-contract",
        action="store_true",
        help="Validate remote install contract entries and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes) or not interactive()

    if not _validate_remote_contract():
        return 1

    if args.verify_remote_contract:
        ok("agentic-install-skills-mcps: remote contract check passed")
        return 0

    manifest = load_skill_manifest(Path(args.skill_config))
    if manifest is None:
        return 1

    plan = _build_install_plan(args, manifest)
    if plan is None:
        return 1

    if args.converge:
        return _converge(manifest, plan, prompt=not args.yes and interactive())

    skill_selection = _resolve_pack_skills(manifest, list(plan.skill_packs), list(plan.skill_names))
    destination = plan.destination
    do_codebase = plan.do_codebase
    do_agentmemory = plan.do_agentmemory
    do_agent_rules = plan.do_agent_rules

    if (
        not plan.skill_packs
        and not do_codebase
        and not do_agentmemory
        and not do_agent_rules
        and not non_interactive
    ):
        skill_selection = _pick_skills(manifest, list(plan.skill_names))
        if skill_selection and not args.skill_agent and args.skills_dir is None:
            destination = _pick_skill_destination()
            if destination == ():
                warn("No target agent selected")
                skill_selection = {}

        if not isinstance(destination, Path):
            selected_mcps = choose(
                "Select MCP tooling",
                [Option(name, label, True) for name, label in _MCP_LABELS.items()],
            )
            do_codebase = "codebase-memory-mcp" in selected_mcps
            do_agentmemory = "agentmemory" in selected_mcps
            question = f"Install the recommended agent rules to {AGENT_RULES_PATH}"
            if _user_agent_rules():
                # The backup sits beside the symlink target, as `write_atomic_text` writes there.
                question += f" (replaces your file; it is kept as {AGENT_RULES_PATH.resolve()}.agentic-env.bak)"
            do_agent_rules = ask(question, default=True, non_interactive=False)

        if skill_selection or do_codebase or do_agentmemory or do_agent_rules:
            _summarize_selection(
                manifest, skill_selection, destination, do_codebase, do_agentmemory, do_agent_rules
            )
            replay = _replay_command(
                manifest, skill_selection, destination, do_codebase, do_agentmemory, do_agent_rules
            )
            if replay:
                info(f"Same selection without prompts: {replay}")
            if not ask("Install this selection", default=True, non_interactive=False):
                skip("nothing installed")
                return 0
    elif not skill_selection and (args.skill or args.skills_dir is not None):
        warn("--skill/--skills-dir: the selected packs provide no matching skills; nothing to install")
        return 1

    ok_all = True
    if skill_selection:
        ok_all = _install_skills(
            manifest, skill_selection, destination, non_interactive=non_interactive
        ) and ok_all
    else:
        skip("skill packs: skipped")

    if do_codebase:
        with_ui = ask(
            "Install codebase-memory-mcp with UI",
            default=True,
            non_interactive=non_interactive,
        )
        ok_all = _install_codebase_memory(with_ui, non_interactive) and ok_all
    else:
        skip("codebase-memory-mcp: skipped")

    if do_agentmemory:
        ok_all = _install_agentmemory(non_interactive) and ok_all
    else:
        skip("agentmemory: skipped")

    if do_agent_rules:
        ok_all = _install_agent_rules() and ok_all
    else:
        skip("agent rules: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
