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
_MATTPOCK_SKILL_PACK = "mattpocock/skills"
_PONYTAIL_SKILL_PACK = "DietrichGebert/ponytail"

_AGENTMEMORY_NPM_PACKAGE = "@agentmemory/agentmemory"
_AGENTMEMORY_PI_INDEX_TS = (
    "https://raw.githubusercontent.com/rohitg00/agentmemory/main/integrations/pi/index.ts"
)
_SKILL_AGENTS = ("Hermes Agent", "Pi", "Claude Code", "Codex")  # Pi == ohmipy


def _skill_agents() -> list[str]:
    return [*_SKILL_AGENTS]


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


def _install_skill_package(source: str) -> bool:
    command = ["add", source, "--global", "--yes"]
    for agent in _skill_agents():
        command.extend(["--agent", agent])
    if cmd_exists("skills"):
        info(f"Installing skill pack: {source}...")
        run(["skills", *command])
        return True

    if not cmd_exists("npm"):
        warn("npm is required to install skills via npx")
        return False

    info(f"Installing skill pack: {source}...")
    run(["npx", "--yes", _SKILLS_CLI_PACKAGE, *command])
    return True


def _install_skills(_: bool) -> bool:
    if not cmd_exists("skills") and not cmd_exists("npm"):
        warn("skills CLI requires npm or a global skills binary")
        return False

    if not _install_skill_package(_MATTPOCK_SKILL_PACK):
        return False
    ok("mattpocock skills: installed")

    if not _install_skill_package(_PONYTAIL_SKILL_PACK):
        return False
    ok("ponytail skill: installed")
    return True



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
        "--all-mcps", action="store_true", help="Install all MCPs without prompting"
    )
    parser.add_argument("--yes", action="store_true", help="Assume defaults in prompts")
    parser.add_argument("--verbose", action="store_true", help="Show full command output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv or sys.argv[1:])
    set_verbose(args.verbose)
    non_interactive = bool(args.yes)

    do_skills = bool(args.all_skills or non_interactive)
    do_codebase = bool(args.all_mcps or non_interactive)
    do_lean = bool(args.all_mcps or non_interactive)
    do_agentmemory = bool(args.all_mcps or non_interactive)

    if not do_skills and not do_codebase and not do_lean and not do_agentmemory:
        do_skills = ask(
            "Install skill packs (mattpocock + ponytail)",
            default=False,
            non_interactive=non_interactive,
        )
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
        if not _install_skills(non_interactive):
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
