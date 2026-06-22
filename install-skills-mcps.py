#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# ///
from __future__ import annotations

"""Install agent skills and MCP tooling."""

import argparse
import json
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
    command = ["add", source, "--agent", "*", "--global", "--yes"]
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


def _install_codebase_memory(with_ui: bool) -> bool:
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


def _install_agentmemory(_non_interactive: bool) -> bool:
    if not cmd_exists("npm"):
        warn("npm is required to install agentmemory")
        return False

    if cmd_exists("agentmemory"):
        skip("agentmemory: already installed")
    else:
        info("Installing agentmemory...")
        run(["npm", "install", "-g", _AGENTMEMORY_NPM_PACKAGE])
        ok("agentmemory: installed")

    pi_ok = _configure_pi_agentmemory()
    hermes_ok = _configure_hermes_agentmemory()
    return hermes_ok and pi_ok


def _install_lean_ctx(non_interactive: bool) -> bool:
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
        _install_codebase_memory(with_ui)
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
