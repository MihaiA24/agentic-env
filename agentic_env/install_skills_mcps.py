"""Install agent skills and MCP tooling."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass

from . import configure_agent_mcps
from .common import (
    ask,
    cmd_exists,
    cmd_version_matches,
    install_pinned_binary_archive,
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
    CODEBASE_MEMORY_ARCHIVES,
    CODEBASE_MEMORY_RELEASE_BASE,
    SKILL_AGENTS,
    SKILL_AGENT_CLI_NAMES,
    SKILL_AGENT_LOOKUP,
    SKILLS_CLI_PACKAGE,
    STACK_VERSION_FRAGMENTS,
    SKILLS_INSTALL_REMOTE_CONTRACT,
)

_REMOTE_INSTALL_CONTRACT = SKILLS_INSTALL_REMOTE_CONTRACT
_SKILL_PACK_CONFIG_PATH = Path(__file__).with_name("skill-packs.json")
_SKILL_PACKS: tuple[SkillPack, ...] = ()
_SKILL_PACK_ALIASES: tuple[SkillPackAlias, ...] = ()
_SKILL_PACK_PROFILES: tuple[SkillProfile, ...] = ()



def _collect_unique(values: list[str]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


@dataclass(frozen=True)
class SkillPackAlias:
    alias: str
    pack_name: str


@dataclass(frozen=True)
class SkillPack:
    name: str
    source: str
    label: str
    aliases: tuple[str, ...]
    skills: tuple[str, ...]


@dataclass(frozen=True)
class SkillProfile:
    name: str
    packs: tuple[str, ...]


@dataclass(frozen=True)
class SkillPackSelection:
    selected: tuple[str, ...]
    unknown: tuple[str, ...]


@dataclass(frozen=True)
class SkillNameSelection:
    selected: tuple[str, ...]


@dataclass(frozen=True)
class SkillAgentSelection:
    selected: tuple[str, ...]
    unknown: tuple[str, ...]


@dataclass(frozen=True)
class SkillInstallPlan:
    skill_packs: tuple[str, ...]
    skill_names: SkillNameSelection
    skill_agents: SkillAgentSelection
    do_codebase: bool
    do_agentmemory: bool



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


def _parse_skill_pack_config(
    payload: object, path: Path
) -> tuple[tuple[SkillPack, ...], tuple[SkillPackAlias, ...], tuple[SkillProfile, ...]] | None:
    if not isinstance(payload, dict):
        warn(f"Invalid skill-pack config in {path}: expected object")
        return None

    packs_payload = payload.get("packs")
    if not isinstance(packs_payload, list) or not packs_payload:
        warn(f"Invalid skill-pack config in {path}: 'packs' must be a non-empty list")
        return None

    packs: list[SkillPack] = []
    aliases: list[SkillPackAlias] = []
    profiles: list[SkillProfile] = []
    pack_names: set[str] = set()
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

        if canonical_name in pack_names:
            warn(f"Duplicate pack '{canonical_name}' in {path}")
            return None
        pack_names.add(canonical_name)

        aliases_payload = item.get("aliases", [])
        if not isinstance(aliases_payload, list):
            warn(f"Invalid aliases for pack '{name}' in {path}: expected list")
            return None

        skills_payload = item.get("skills", [])
        if not isinstance(skills_payload, list):
            warn(f"Invalid skills filter for pack '{name}' in {path}: expected list")
            return None

        skill_values: list[str] = []
        for raw_skill in skills_payload:
            if not isinstance(raw_skill, str):
                warn(f"Invalid skill value for pack '{name}' in {path}: {raw_skill!r}")
                return None
            skill = raw_skill.strip()
            if skill and skill not in skill_values:
                skill_values.append(skill)

        raw_aliases: list[str] = []
        for raw_alias in aliases_payload:
            if not isinstance(raw_alias, str):
                warn(f"Invalid alias for pack '{name}' in {path}: {raw_alias!r}")
                return None
            alias = raw_alias.strip().lower()
            if alias:
                raw_aliases.append(alias)

        resolved_aliases = [source_value.lower(), *raw_aliases]

        for alias in _collect_unique(resolved_aliases):
            existing = alias_lookup.get(alias)
            if existing is None:
                alias_lookup[alias] = canonical_name
                aliases.append(SkillPackAlias(alias=alias, pack_name=canonical_name))
            elif existing != canonical_name:
                warn(
                    f"Alias '{alias}' maps to both '{existing}' and '{canonical_name}' in {path}"
                )
                return None

        packs.append(
            SkillPack(
                name=canonical_name,
                source=source_value,
                label=label_value,
                aliases=tuple(_collect_unique(raw_aliases)),
                skills=tuple(skill_values),
            )
        )

    profiles_payload = payload.get("profiles", {"default": [pack.name for pack in packs]})
    if not isinstance(profiles_payload, dict):
        warn(f"Invalid 'profiles' in {path}: expected object")
        return None

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
            if canonical_pack not in pack_names:
                warn(f"Profile '{profile_name}' references unknown pack '{raw_pack}' in {path}")
                return None
            if canonical_pack not in selected:
                selected.append(canonical_pack)

        profiles.append(SkillProfile(name=profile_name.strip(), packs=tuple(selected)))

    return tuple(packs), tuple(aliases), tuple(profiles)


def _load_skill_pack_config(path: Path) -> bool:
    global _SKILL_PACKS, _SKILL_PACK_ALIASES, _SKILL_PACK_PROFILES

    if not path.exists():
        warn(f"Skill pack config not found: {path}")
        return False

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warn(f"Invalid JSON in {path}: {exc}")
        return False
    except OSError as exc:
        warn(f"Cannot read {path}: {exc}")
        return False

    parsed = _parse_skill_pack_config(payload, path)
    if parsed is None:
        return False

    _SKILL_PACKS, _SKILL_PACK_ALIASES, _SKILL_PACK_PROFILES = parsed
    return True


def _pack_aliases() -> dict[str, str]:
    return {alias.alias: alias.pack_name for alias in _SKILL_PACK_ALIASES}


def _pack_profiles() -> dict[str, SkillProfile]:
    return {profile.name: profile for profile in _SKILL_PACK_PROFILES}


def _pack_lookup() -> dict[str, SkillPack]:
    return {pack.name: pack for pack in _SKILL_PACKS}


def _all_skill_packs() -> list[str]:
    return [pack.name for pack in _SKILL_PACKS]


def _all_skill_profiles() -> list[str]:
    return [profile.name for profile in _SKILL_PACK_PROFILES]


def _skill_pack_source(name: str) -> str:
    return _pack_lookup()[name].source


def _skill_pack_label(name: str) -> str:
    return _pack_lookup()[name].label


def _skill_pack_skills(name: str) -> list[str]:
    return list(_pack_lookup()[name].skills)


def profile_skills(profile: str, path: Path = _SKILL_PACK_CONFIG_PATH) -> list[str]:
    """Curated skill roster: union of every pack filter in `profile` (manifest order)."""
    if not _load_skill_pack_config(path):
        return []
    names: list[str] = []
    for pack in _pack_profiles()[profile].packs:
        names.extend(skill for skill in _skill_pack_skills(pack) if skill not in names)
    return names


def _validate_remote_contract() -> bool:
    return validate_remote_contract(
        _REMOTE_INSTALL_CONTRACT, scope="agentic-install-skills-mcps"
    )


def _parse_skill_packs(values: list[str] | None) -> SkillPackSelection:
    selected: list[str] = []
    unknown: list[str] = []
    aliases = _pack_aliases()

    for raw in _split_csv(values):
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


def _parse_skill_names(values: list[str] | None) -> SkillNameSelection:
    requested: list[str] = []
    for name in _split_csv(values):
        if name not in requested:
            requested.append(name)
    return SkillNameSelection(selected=tuple(requested))


def _parse_skill_agents(values: list[str] | None) -> SkillAgentSelection:
    selected: list[str] = []
    unknown: list[str] = []

    for raw in _split_csv(values):
        value = raw.strip().lower()
        if not value:
            continue
        if value == "all":
            return SkillAgentSelection(selected=tuple(_all_skill_agents()), unknown=())

        canonical = SKILL_AGENT_LOOKUP.get(value)
        if canonical is None:
            unknown.append(raw.strip())
            continue
        if canonical not in selected:
            selected.append(canonical)

    return SkillAgentSelection(selected=tuple(selected), unknown=tuple(unknown))


def _all_skill_agents() -> list[str]:
    return [agent for agent, _, _ in SKILL_AGENTS]


def _skill_agent_label(agent: str) -> str:
    return SKILL_AGENT_CLI_NAMES[agent]


def _build_install_plan(args: argparse.Namespace, *, non_interactive: bool) -> SkillInstallPlan | None:
    pack_selection = _parse_skill_packs(args.skill_pack)
    if pack_selection.unknown:
        warn(f"Unknown skill pack(s): {', '.join(sorted(pack_selection.unknown))}")
        warn(f"Available: {', '.join(_all_skill_packs())}")
        return None

    selected_skill_agents = _parse_skill_agents(args.skill_agent)
    if selected_skill_agents.unknown:
        warn(f"Unknown skill agent(s): {', '.join(sorted(selected_skill_agents.unknown))}")
        warn(f"Available: {', '.join(_all_skill_agents())}")
        return None

    skill_names = _parse_skill_names(args.skill)

    if args.all_skills:
        selected_skill_packs = _all_skill_packs()
    elif pack_selection.selected:
        selected_skill_packs = list(pack_selection.selected)
    elif args.skill_profile:
        profile_name = args.skill_profile.strip()
        if not profile_name:
            warn("Empty --skill-profile value")
            return None

        profile = _pack_profiles().get(profile_name)
        if profile is None:
            warn(f"Unknown skill profile: {profile_name}")
            warn(f"Available: {', '.join(_all_skill_profiles())}")
            return None

        selected_skill_packs = list(profile.packs)
    elif non_interactive:
        selected_skill_packs = []
    else:
        selected_skill_packs = []

    return SkillInstallPlan(
        skill_packs=tuple(selected_skill_packs),
        skill_names=skill_names,
        skill_agents=selected_skill_agents,
        do_codebase=bool(args.all_mcps),
        do_agentmemory=bool(args.all_mcps),
    )


def _select_skill_packs(non_interactive: bool) -> list[str]:
    selected: list[str] = []
    for pack in _SKILL_PACKS:
        if ask(
            f"Install skill pack: {pack.label}?",
            default=False,
            non_interactive=non_interactive,
        ):
            selected.append(pack.name)
    return selected


def _command_path_on_path(
    binary: str, extra_paths: list[Path] | None = None
) -> str | None:
    extra: list[str] = [str(path) for path in (extra_paths or [])]
    system_path = os.environ.get("PATH", "")
    if system_path:
        extra.append(system_path)
    search_path = os.pathsep.join(extra) if extra else None
    return shutil.which(binary, path=search_path)


def _command_exists(binary: str) -> bool:
    return _command_path_on_path(binary) is not None


def _should_install_mcp(binary: str, label: str, non_interactive: bool) -> bool:
    if cmd_version_matches(binary, STACK_VERSION_FRAGMENTS[binary]):
        if not ask(
            f"Reinstall {label}", default=False, non_interactive=non_interactive
        ):
            skip(f"{label}: curated version already installed")
            return False
    elif _command_exists(binary):
        warn(f"{label}: installed version differs; converging")
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
        shim_path.write_text(
            f'#!/usr/bin/env sh\nexec "{binary_path}" "$@"\n',
            encoding="utf-8",
        )
        shim_path.chmod(0o755)
    except OSError as exc:
        warn(f"agentmemory: failed to write local shim {shim_path}: {exc}")
        return False

    resolved_path = _command_path_on_path("agentmemory", extra_paths=[user_bin_dir])
    if resolved_path is None:
        warn("agentmemory: fallback install completed but command is not resolvable")
        warn("PATH remediation: add ~/.local/bin to PATH and rerun")
        warn('Example: export PATH="$HOME/.local/bin:$PATH"')
        return False

    if str(user_bin_dir) not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = str(user_bin_dir) + (
            os.pathsep + os.environ.get("PATH", "")
            if os.environ.get("PATH", "")
            else ""
        )
        skip("PATH updated for this process")
        skip('Persist with: export PATH="$HOME/.local/bin:$PATH"')

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



def _configure_hermes_agentmemory() -> bool:
    return (
        configure_agent_mcps.main(
            [
                "--server",
                "agentmemory",
                "--agent",
                "hermes",
                "--yes",
                "--no-skills",
            ]
        )
        == 0
    )




def _install_skills(
    skill_packs: list[str], requested_skills: list[str], skill_agents: list[str]
) -> bool:
    if not cmd_exists("skills") and not cmd_exists("npm"):
        warn("skills CLI requires npm or a global skills binary")
        return False

    if not skill_agents:
        warn("No target agents selected for skill installation")
        return False

    for pack in skill_packs:
        source = _skill_pack_source(pack)
        configured_skills = _skill_pack_skills(pack)

        if configured_skills:
            if requested_skills:
                filtered_skills = [
                    skill for skill in requested_skills if skill in configured_skills
                ]
                if not filtered_skills:
                    warn(
                        f"{_skill_pack_label(pack)}: no requested skills matched this pack's filter; skipped"
                    )
                    continue
            else:
                filtered_skills = configured_skills
        else:
            filtered_skills = requested_skills

        if not _install_skill_package(source, filtered_skills, skill_agents):
            warn(f"{_skill_pack_label(pack)}: installation failed")
            return False
    return True


def _install_skill_package(
    source: str, skills: list[str], skill_agents: list[str]
) -> bool:
    command = ["add", source, "--global", "--yes"]
    for skill in skills:
        command.extend(["--skill", skill])
    for skill_agent in skill_agents:
        command.extend(["--agent", _skill_agent_label(skill_agent)])

    if skills:
        info(f"Installing skills: {', '.join(skills)} from {source}...")
    else:
        info(f"Installing skill pack: {source}...")

    if cmd_version_matches("skills", STACK_VERSION_FRAGMENTS["skills"]):
        run(["skills", *command])
        return True
    if not cmd_exists("npm"):
        warn("The curated skills CLI requires npm")
        return False
    run(["npx", "--yes", SKILLS_CLI_PACKAGE, *command])
    return True


def _install_agentmemory(non_interactive: bool) -> bool:
    if not _should_install_mcp("agentmemory", "agentmemory", non_interactive):
        return True
    if not cmd_exists("npm"):
        warn("npm is required to install agentmemory")
        return False

    info("Installing agentmemory...")
    if not _install_npm_global(AGENTMEMORY_NPM_PACKAGE, "agentmemory"):
        return False
    if not cmd_version_matches("agentmemory", STACK_VERSION_FRAGMENTS["agentmemory"]):
        warn("agentmemory: installed version does not match curated release")
        return False

    return _configure_hermes_agentmemory()


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
    if not cmd_version_matches(binary, STACK_VERSION_FRAGMENTS["codebase-memory-mcp"]):
        warn("codebase-memory-mcp: installed version does not match curated release")
        return False
    ok("codebase-memory-mcp: installed" + (" (with UI)" if with_ui else ""))
    return True


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
        default=str(_SKILL_PACK_CONFIG_PATH),
        help="Path to JSON skill pack config (packs + profiles).",
    )
    parser.add_argument(
        "--all-mcps",
        action="store_true",
        help="Install all MCPs without prompting",
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
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes)

    if not _validate_remote_contract():
        return 1

    if args.verify_remote_contract:
        ok("agentic-install-skills-mcps: remote contract check passed")
        return 0

    if not _load_skill_pack_config(Path(args.skill_config)):
        return 1

    plan = _build_install_plan(args, non_interactive=non_interactive)
    if plan is None:
        return 1

    selected_skill_packs = list(plan.skill_packs)
    requested_skill_names = list(plan.skill_names.selected)
    selected_skill_agents = list(plan.skill_agents.selected) or _all_skill_agents()

    do_skills = bool(selected_skill_packs)
    do_codebase = plan.do_codebase
    do_agentmemory = plan.do_agentmemory

    if not do_skills and not do_codebase and not do_agentmemory:
        do_skills = ask(
            "Install skill packs",
            default=False,
            non_interactive=non_interactive,
        )
        if do_skills:
            selected_skill_packs = _select_skill_packs(non_interactive)
            do_skills = bool(selected_skill_packs)
        do_codebase = ask(
            "Install MCP: codebase-memory-mcp",
            default=False,
            non_interactive=non_interactive,
        )
        do_agentmemory = ask(
            "Install MCP: agentmemory",
            default=False,
            non_interactive=non_interactive,
        )

    ok_all = True
    if do_skills:
        ok_all = (
            _install_skills(
                selected_skill_packs, requested_skill_names, selected_skill_agents
            )
            and ok_all
        )
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

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
