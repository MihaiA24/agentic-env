#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
from __future__ import annotations

"""Install agent skills and MCP tooling."""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from common import ask, cmd_exists, ok, run, run_shell, set_verbose, skip, warn, info


_SKILLS_CLI_PACKAGE = "skills@latest"
_AGENTMEMORY_NPM_PACKAGE = "@agentmemory/agentmemory"
_AGENTMEMORY_PI_INDEX_TS = (
    "https://raw.githubusercontent.com/rohitg00/agentmemory/main/integrations/pi/index.ts"
)
_SKILL_AGENTS: tuple[tuple[str, str], ...] = (
    ("hermes", "Hermes Agent"),
    ("ohmipy", "Pi"),  # Pi == ohmipy
    ("claude", "Claude Code"),
    ("codex", "Codex"),
)
_SKILL_AGENT_LABELS = {agent: label for agent, label in _SKILL_AGENTS}
_SKILL_AGENT_LOOKUP = {
    **{agent: agent for agent, _ in _SKILL_AGENTS},
    **{label.lower(): agent for agent, label in _SKILL_AGENTS},
}
_SKILL_PACK_CONFIG_PATH = Path(__file__).with_name("skill-packs.json")
_DEFAULT_SKILL_PACKS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("mattpocock", "mattpocock/skills", "mattpocock skills", ()),
    ("ponytail", "DietrichGebert/ponytail", "ponytail skill", ()),
)
_DEFAULT_SKILL_PACK_ALIASES = {
    "mattpocock": "mattpocock",
    "mattpocock/skills": "mattpocock",
    "ponytail": "ponytail",
    "dietrichgebert/ponytail": "ponytail",
}
_DEFAULT_SKILL_PACK_PROFILES = {"default": ["mattpocock", "ponytail"]}
_SKILL_PACKS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = _DEFAULT_SKILL_PACKS
_SKILL_PACK_ALIASES = {**_DEFAULT_SKILL_PACK_ALIASES}
_SKILL_PACK_PROFILES = {**_DEFAULT_SKILL_PACK_PROFILES}


def _load_skill_pack_config(path: Path) -> bool:
    global _SKILL_PACKS, _SKILL_PACK_ALIASES, _SKILL_PACK_PROFILES

    if not path.exists():
        if path != _SKILL_PACK_CONFIG_PATH:
            warn(f"Skill pack config not found: {path}")
            return False
        _SKILL_PACKS = _DEFAULT_SKILL_PACKS
        _SKILL_PACK_ALIASES = {**_DEFAULT_SKILL_PACK_ALIASES}
        _SKILL_PACK_PROFILES = {**_DEFAULT_SKILL_PACK_PROFILES}
        return True

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warn(f"Invalid JSON in {path}: {exc}")
        return False
    except OSError as exc:
        warn(f"Cannot read {path}: {exc}")
        return False

    if not isinstance(payload, dict):
        warn(f"Invalid skill-pack config in {path}: expected object")
        return False

    packs_payload = payload.get("packs")
    if not isinstance(packs_payload, list) or not packs_payload:
        warn(f"Invalid skill-pack config in {path}: 'packs' must be a non-empty list")
        return False

    packs: list[tuple[str, str, str, tuple[str, ...]]] = []
    aliases: dict[str, str] = {}
    pack_names: set[str] = set()
    for item in packs_payload:
        if not isinstance(item, dict):
            warn(f"Invalid pack entry in {path}: {item!r}")
            return False
        name = item.get("name")
        source = item.get("source")
        label = item.get("label", f"{name} skill")
        if not isinstance(name, str) or not name.strip():
            warn(f"Invalid pack name in {path}: {name!r}")
            return False
        if not isinstance(source, str) or not source.strip():
            warn(f"Invalid source for pack '{name}' in {path}: {source!r}")
            return False
        if not isinstance(label, str) or not label.strip():
            warn(f"Invalid label for pack '{name}' in {path}: {label!r}")
            return False

        aliases_raw = item.get("aliases", [])
        if not isinstance(aliases_raw, list):
            warn(f"Invalid aliases for pack '{name}' in {path}: expected list")
            return False

        skills_raw = item.get("skills", [])
        if not isinstance(skills_raw, list):
            warn(f"Invalid skills filter for pack '{name}' in {path}: expected list")
            return False
        skills: list[str] = []
        for raw_skill in skills_raw:
            if not isinstance(raw_skill, str):
                warn(f"Invalid skill value for pack '{name}' in {path}: {raw_skill!r}")
                return False
            skill = raw_skill.strip()
            if not skill:
                continue
            if skill not in skills:
                skills.append(skill)

        canonical = name.strip().lower()
        source = source.strip()
        label = label.strip()
        if canonical in pack_names:
            warn(f"Duplicate pack '{canonical}' in {path}")
            return False
        pack_names.add(canonical)
        packs.append((canonical, source, label, tuple(skills)))
        source_alias = source.lower()
        if source_alias in aliases and aliases[source_alias] != canonical:
            warn(
                f"Source '{source_alias}' is also an alias for '{aliases[source_alias]}', "
                f"not '{canonical}', in {path}"
            )
            return False
        aliases[source_alias] = canonical
        for raw_alias in aliases_raw:
            if not isinstance(raw_alias, str):
                warn(f"Invalid alias for pack '{name}' in {path}: {raw_alias!r}")
                return False
            alias_key = raw_alias.strip().lower()
            if not alias_key:
                continue
            if alias_key in aliases and aliases[alias_key] != canonical:
                warn(
                    f"Alias '{alias_key}' maps to both '{aliases[alias_key]}' and '{canonical}' in {path}"
                )
                return False
            aliases[alias_key] = canonical

    profiles_payload = payload.get("profiles", {"default": [name for name, _, _, _ in packs]})
    if not isinstance(profiles_payload, dict):
        warn(f"Invalid 'profiles' in {path}: expected object")
        return False

    profiles: dict[str, list[str]] = {}
    for profile_name, pack_values in profiles_payload.items():
        if not isinstance(profile_name, str) or not profile_name.strip():
            warn(f"Invalid profile name in {path}: {profile_name!r}")
            return False
        if not isinstance(pack_values, list) or not all(isinstance(item, str) for item in pack_values):
            warn(f"Invalid profile '{profile_name}' in {path}: expected list of pack names")
            return False
        normalized: list[str] = []
        for raw_pack in pack_values:
            canonical_pack = raw_pack.strip().lower()
            if canonical_pack not in pack_names:
                warn(f"Profile '{profile_name}' references unknown pack '{raw_pack}' in {path}")
                return False
            if canonical_pack not in normalized:
                normalized.append(canonical_pack)
        profiles[profile_name.strip()] = normalized

    _SKILL_PACKS = tuple(packs)
    _SKILL_PACK_ALIASES = aliases
    _SKILL_PACK_PROFILES = profiles
    return True


def _all_skill_packs() -> list[str]:
    return [name for name, _, _, _ in _SKILL_PACKS]


def _all_skill_profiles() -> list[str]:
    return list(_SKILL_PACK_PROFILES.keys())


def _skill_pack_source(name: str) -> str:
    return {name: source for name, source, _, _ in _SKILL_PACKS}[name]


def _skill_pack_label(name: str) -> str:
    return {name: label for name, _, label, _ in _SKILL_PACKS}[name]


def _skill_pack_skills(name: str) -> list[str]:
    return list({name: skills for name, _, _, skills in _SKILL_PACKS}[name])



def _parse_skill_packs(values: list[str] | None) -> tuple[list[str], list[str]]:
    selected: list[str] = []
    unknown: list[str] = []
    for raw in values or []:
        for token in raw.split(","):
            name = token.strip().lower()
            if not name:
                continue
            canonical = _SKILL_PACK_ALIASES.get(name)
            if canonical is None:
                unknown.append(token.strip())
                continue
            if canonical not in selected:
                selected.append(canonical)
    return selected, unknown


def _parse_skill_names(values: list[str] | None) -> list[str]:
    requested: list[str] = []
    for raw in values or []:
        for token in raw.split(","):
            name = token.strip()
            if not name:
                continue
            if name not in requested:
                requested.append(name)
    return requested


def _parse_skill_agents(values: list[str] | None) -> tuple[list[str], list[str]]:
    selected: list[str] = []
    unknown: list[str] = []
    for raw in values or []:
        for token in raw.split(","):
            value = token.strip().lower()
            if not value:
                continue
            if value == "all":
                return list(_all_skill_agents()), []
            canonical = _SKILL_AGENT_LOOKUP.get(value)
            if canonical is None:
                unknown.append(token.strip())
                continue
            if canonical not in selected:
                selected.append(canonical)
    return selected, unknown


def _all_skill_agents() -> list[str]:
    return [agent for agent, _ in _SKILL_AGENTS]


def _skill_agent_label(agent: str) -> str:
    return _SKILL_AGENT_LABELS[agent]


def _select_skill_packs(non_interactive: bool) -> list[str]:
    selected: list[str] = []
    for name, _, label, _ in _SKILL_PACKS:
        if ask(f"Install skill pack: {label}?", default=False, non_interactive=non_interactive):
            selected.append(name)
    return selected


def _command_exists(binary: str) -> bool:
    if cmd_exists(binary):
        return True
    return (Path.home() / ".local" / "bin" / binary).is_file()


def _should_install_mcp(binary: str, label: str, non_interactive: bool) -> bool:
    if _command_exists(binary):
        if not ask(f"Reinstall {label}", default=False, non_interactive=non_interactive):
            skip(f"{label}: already installed")
            return False
    return True



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
        warn(f"agentmemory fallback install succeeded but binary missing: {binary_path}")
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
    ok(f"agentmemory: installed to user-local npm prefix {local_prefix}")
    skip(
        "PATH may not include ~/.local/bin automatically; add it to use the fallback binary"
    )
    return True


def _install_npm_global(package: str, label: str) -> bool:
    try:
        run(["npm", "install", "-g", package])
        ok(f"{label}: installed")
        return True
    except subprocess.CalledProcessError as exc:
        if not _is_npm_permission_error(exc):
            warn(f"{label}: npm install failed")
            return False
        warn(f"{label}: global npm install blocked by permissions")
        return _install_agentmemory_user_local(package)


def _download_text(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as exc:
        warn(f"agentmemory setup: failed to download {url}: {exc}")
        return None


def _configure_hermes_agentmemory() -> bool:
    configure_script = Path(__file__).with_name("configure-agent-mcps.py")
    run(
        [
            sys.executable,
            str(configure_script),
            "--server",
            "agentmemory",
            "--agent",
            "hermes",
            "--yes",
            "--no-skills",
        ]
    )
    return True


def _configure_pi_agentmemory() -> bool:
    extension_dir = Path.home() / ".pi" / "agent" / "extensions" / "agentmemory"
    index_path = extension_dir / "index.ts"
    extension_ref_tilde = "~/.pi/agent/extensions/agentmemory"
    extension_ref_abs = str(extension_dir)
    settings_path = Path.home() / ".pi" / "agent" / "settings.json"

    if not index_path.exists():
        integration = _download_text(_AGENTMEMORY_PI_INDEX_TS)
        if integration is None:
            return False
        extension_dir.mkdir(parents=True, exist_ok=True)
        index_path.write_text(integration, encoding="utf-8")
        ok("ohmipi/omp config: copied agentmemory extension index.ts")
    else:
        skip("ohmipi/omp config: extension already present")

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            extensions = settings.get("extensions")
            if not isinstance(extensions, list):
                warn("ohmipi/omp settings.json: extensions is not a list; skipped")
                return True
            if (
                extension_ref_tilde not in extensions
                and extension_ref_abs not in extensions
            ):
                extensions.append(extension_ref_tilde)
                settings_path.write_text(
                    json.dumps(settings, indent=2) + "\n",
                    encoding="utf-8",
                )
                ok("ohmipi/omp config: enabled agentmemory extension in settings.json")
            else:
                skip(
                    "ohmipi/omp config: settings already includes agentmemory extension"
                )
        except json.JSONDecodeError:
            warn("ohmipi/omp settings.json: invalid JSON; skipped")
            return True
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"extensions": [extension_ref_tilde]}, indent=2) + "\n",
            encoding="utf-8",
        )
        ok("ohmipi/omp config: created settings.json with agentmemory extension")

    return True


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
    if cmd_exists("skills"):
        if skills:
            info(f"Installing skills: {', '.join(skills)} from {source}...")
        else:
            info(f"Installing skill pack: {source}...")
        run(["skills", *command])
        return True

    if not cmd_exists("npm"):
        warn("npm is required to install skills via npx")
        return False

    if skills:
        info(f"Installing skills: {', '.join(skills)} from {source}...")
    else:
        info(f"Installing skill pack: {source}...")
    run(["npx", "--yes", _SKILLS_CLI_PACKAGE, *command])
    return True
def _install_agentmemory(non_interactive: bool) -> bool:
    if not _should_install_mcp("agentmemory", "agentmemory", non_interactive):
        return True

    if not cmd_exists("npm"):
        warn("npm is required to install agentmemory")
        return False

    info("Installing agentmemory...")
    if not _install_npm_global(_AGENTMEMORY_NPM_PACKAGE, "agentmemory"):
        return False

    pi_ok = _configure_pi_agentmemory()
    hermes_ok = _configure_hermes_agentmemory()
    return hermes_ok and pi_ok







def _install_codebase_memory(with_ui: bool, non_interactive: bool) -> bool:
    if not _should_install_mcp(
        "codebase-memory-mcp",
        "codebase-memory-mcp",
        non_interactive,
    ):
        return True

    if not cmd_exists("curl"):
        warn("curl is required to install codebase-memory-mcp")
        return False

    base = (
        "https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh"
    )
    info("Installing codebase-memory-mcp...")
    run_shell(f"curl -fsSL {base} | bash" + (" -s -- --ui" if with_ui else ""))
    ok("codebase-memory-mcp: installed" + (" (with UI)" if with_ui else ""))
    return True


def _install_lean_ctx(non_interactive: bool) -> bool:
    if not _should_install_mcp("lean-ctx", "lean-ctx", non_interactive):
        return True

    if not cmd_exists("curl"):
        warn("curl is required to install lean-ctx")
        return False

    info("Installing lean-ctx...")
    run_shell("curl -fsSL https://leanctx.com/install.sh | sh")
    ok("lean-ctx: installed")

    if cmd_exists("lean-ctx") and ask(
        "Run lean-ctx setup now", default=True, non_interactive=non_interactive
    ):
        run(["lean-ctx", "setup"])
        ok("lean-ctx setup: run")
    else:
        skip("lean-ctx setup: skipped")

    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install shared skills and MCP tooling"
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
            "Install to specific agents (for example: hermes, ohmipy, claude, codex). "
            "Repeat or use commas. Defaults to all configured targets."
        ),
    )
    parser.add_argument(
        "--skill-profile",
        metavar="NAME",
        help=(
            "Install packs from this profile in the skill pack config. "
            "Defaults to 'default' only when selected in non-interactive mode."
        ),
    )
    parser.add_argument(
        "--skill-config",
        metavar="PATH",
        default=str(_SKILL_PACK_CONFIG_PATH),
        help="Path to JSON skill pack config (packs + profiles).",
    )
    parser.add_argument(
        "--all-mcps", action="store_true", help="Install all MCPs without prompting"
    )
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes)

    if not _load_skill_pack_config(Path(args.skill_config)):
        return 1

    requested_skill_packs, unknown_skill_packs = _parse_skill_packs(args.skill_pack)
    if unknown_skill_packs:
        warn(f"Unknown skill pack(s): {', '.join(sorted(unknown_skill_packs))}")
        warn(f"Available: {', '.join(_all_skill_packs())}")
        return 1

    requested_skill_names = _parse_skill_names(args.skill)
    requested_skill_agents, unknown_skill_agents = _parse_skill_agents(args.skill_agent)
    if unknown_skill_agents:
        warn(f"Unknown skill agent(s): {', '.join(sorted(unknown_skill_agents))}")
        warn(f"Available: {', '.join(_all_skill_agents())}")
        return 1
    selected_skill_agents = requested_skill_agents or _all_skill_agents()

    if args.all_skills:
        selected_skill_packs = _all_skill_packs()
    elif requested_skill_packs:
        selected_skill_packs = requested_skill_packs
    elif args.skill_profile:
        profile_name = args.skill_profile.strip()
        if not profile_name:
            warn("Empty --skill-profile value")
            return 1
        profile = _SKILL_PACK_PROFILES.get(profile_name)
        if profile is None:
            warn(f"Unknown skill profile: {profile_name}")
            warn(f"Available: {', '.join(_all_skill_profiles())}")
            return 1
        selected_skill_packs = profile
    elif non_interactive:
        selected_skill_packs = _SKILL_PACK_PROFILES.get("default", _all_skill_packs())
    else:
        selected_skill_packs = []

    do_skills = bool(selected_skill_packs)
    do_codebase = bool(args.all_mcps or non_interactive)
    do_lean = bool(args.all_mcps or non_interactive)
    do_agentmemory = bool(args.all_mcps or non_interactive)

    if not do_skills and not do_codebase and not do_lean and not do_agentmemory:
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
        do_lean = ask(
            "Install MCP: lean-ctx", default=False, non_interactive=non_interactive
        )
        do_agentmemory = ask(
            "Install MCP: agentmemory",
            default=False,
            non_interactive=non_interactive,
        )

    if do_skills:
        if not _install_skills(
            selected_skill_packs, requested_skill_names, selected_skill_agents
        ):
            warn("Skill installation failed")
    else:
        skip("skill packs: skipped")

    if do_codebase:
        with_ui = ask(
            "Install codebase-memory-mcp with UI",
            default=True,
            non_interactive=non_interactive,
        )
        _install_codebase_memory(with_ui, non_interactive)
    else:
        skip("codebase-memory-mcp: skipped")

    if do_lean:
        _install_lean_ctx(non_interactive)
    else:
        skip("lean-ctx: skipped")

    if do_agentmemory:
        _install_agentmemory(non_interactive)
    else:
        skip("agentmemory: skipped")

    return 0




if __name__ == "__main__":
    raise SystemExit(main())
