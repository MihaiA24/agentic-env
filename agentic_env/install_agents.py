"""Install local agent CLIs."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from .common import (
    Option,
    ask,
    choose,
    cmd_exists,
    cmd_version_at_least,
    fetch_url,
    info,
    interactive,
    is_valid_sha256,
    ok,
    run,
    run_remote_script,
    set_verbose,
    skip,
    warn,
)
from .remote_install_contract import validate_remote_contract
from .stack_metadata import (
    AGENTS_INSTALL_REMOTE_CONTRACT,
    CLAUDE_INSTALL_SHA256,
    CLAUDE_INSTALL_URL,
    HERMES_COMMIT,
    HERMES_INSTALL_SHA256,
    HERMES_INSTALL_URL,
    OMP_RELEASES_URL,
    OPENAI_CODEX_PACKAGE,
    STACK_VERSION_FLOORS,
)

_REMOTE_INSTALL_CONTRACT = AGENTS_INSTALL_REMOTE_CONTRACT


def _validate_remote_contract() -> bool:
    return validate_remote_contract(
        _REMOTE_INSTALL_CONTRACT, scope="agentic-install-agents"
    )


def _install_hermes(non_interactive: bool) -> bool:
    # Hermes is the one agent still fetched at a fixed identity: the installer
    # runs from a pinned commit (#39) and refuses to roll an existing checkout
    # backwards, so "install latest" is not available here.
    if cmd_version_at_least("hermes", STACK_VERSION_FLOORS["hermes"]):
        if not ask(
            "Reinstall Hermes Agent", default=False, non_interactive=non_interactive
        ):
            skip("Hermes Agent: at or above the reviewed version")
            return True
    elif cmd_exists("hermes"):
        warn("Hermes Agent: below the reviewed version; converging")

    info("Installing Hermes...")
    if not run_remote_script(
        label="Hermes installer",
        url=HERMES_INSTALL_URL,
        expected_sha256=HERMES_INSTALL_SHA256,
        interpreter="bash",
        interpreter_args=["--skip-setup", "--commit", HERMES_COMMIT],
    ):
        return False
    if not cmd_version_at_least("hermes", STACK_VERSION_FLOORS["hermes"]):
        warn("Hermes Agent: installed version is below the reviewed version")
        return False
    ok("Hermes Agent: installed")
    return True


def _install_omp(non_interactive: bool, *, force: bool = False) -> bool:
    if not force and cmd_version_at_least("omp", STACK_VERSION_FLOORS["omp"]):
        if not ask(
            "Reinstall OMP / Oh My Pi", default=False, non_interactive=non_interactive
        ):
            skip("OMP / Oh My Pi: at or above the reviewed version")
            return True
    elif not force and cmd_exists("omp"):
        warn("OMP / Oh My Pi: below the reviewed version; installing the latest release")

    info("Installing OMP / Oh My Pi...")
    if not _install_omp_release():
        return False
    ok("OMP / Oh My Pi: installed")
    return True


# Stable releases only; also keeps the tag a single safe URL path segment.
_OMP_TAG = re.compile(r"v\d+\.\d+\.\d+")


def _omp_latest_tag() -> str:
    """Resolve the latest stable release from github.com's releases/latest
    redirect; the api.github.com REST lookup is rate-limited per IP."""
    request = urllib.request.Request(
        f"{OMP_RELEASES_URL}/latest",
        method="HEAD",
        headers={"User-Agent": "agentic-env/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        resolved = response.url
    prefix = f"{OMP_RELEASES_URL}/tag/"
    tag = resolved.removeprefix(prefix)
    if not resolved.startswith(prefix) or not _OMP_TAG.fullmatch(tag):
        raise ValueError(f"unexpected latest-release redirect to {resolved}")
    return tag


def _omp_asset() -> str | None:
    """Release asset for this host, mirroring upstream scripts/install.sh."""
    system, machine = platform.system(), platform.machine().lower()
    if system == "Darwin":
        # sysctl, not the machine name: a Rosetta Python reports x86_64 on arm64.
        probe = subprocess.run(
            ["/usr/sbin/sysctl", "-in", "hw.optional.arm64"],
            capture_output=True,
            text=True,
            check=False,
        )
        return "omp-darwin-" + ("arm64" if probe.stdout.strip() == "1" else "x64")
    arch = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}
    if system != "Linux" or machine not in arch:
        warn(f"OMP / Oh My Pi: unsupported platform {system}/{machine}")
        return None
    musl = Path("/etc/alpine-release").exists()
    if not musl and cmd_exists("ldd"):
        # musl's ldd prints its banner to stderr and exits non-zero.
        ldd = subprocess.run(
            ["ldd", "--version"], capture_output=True, text=True, check=False
        )
        musl = "musl" in (ldd.stdout + ldd.stderr).lower()
    return f"omp-linux{'-musl' if musl else ''}-{arch[machine]}"


def _install_omp_release() -> bool:
    """Install the latest release binary after checking it against the
    release's SHA256SUMS.txt. That file comes over the same TLS channel, so
    this proves integrity, not publisher signature."""
    asset = _omp_asset()
    if asset is None:
        return False
    try:
        tag = _omp_latest_tag()
        release = f"{OMP_RELEASES_URL}/download/{tag}"
        sums = fetch_url(f"{release}/SHA256SUMS.txt", 30).decode()
        # ponytail: whole binary (~200 MB) in memory; stream to disk if that bites.
        payload = fetch_url(f"{release}/{asset}", 120)
    except Exception as exc:
        warn(f"OMP / Oh My Pi: release download failed: {exc}")
        return False

    expected = [
        fields[0]
        for fields in map(str.split, sums.splitlines())
        if len(fields) == 2 and fields[1].removeprefix("*") == asset
    ]
    if len(expected) != 1 or not is_valid_sha256(expected[0]):
        warn(f"OMP / Oh My Pi: {tag} SHA256SUMS.txt has no single valid entry for {asset}")
        return False
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected[0].lower():
        warn(f"OMP / Oh My Pi: {tag}/{asset} checksum mismatch")
        warn(f"OMP / Oh My Pi: expected {expected[0]}, got {actual}")
        return False

    install_dir = Path(os.environ.get("PI_INSTALL_DIR") or Path.home() / ".local" / "bin")
    temporary: str | None = None
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".omp.", dir=install_dir)
        with os.fdopen(fd, "wb") as target:
            target.write(payload)
        os.chmod(temporary, 0o755)
        if not cmd_version_at_least(temporary, STACK_VERSION_FLOORS["omp"]):
            warn("OMP / Oh My Pi: downloaded executable fails the reviewed version floor")
            return False
        os.replace(temporary, install_dir / "omp")
        temporary = None
    except OSError as exc:
        warn(f"OMP / Oh My Pi: failed to install {asset}: {exc}")
        return False
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.remove(temporary)
    info(f"OMP / Oh My Pi: installed {tag} to {install_dir / 'omp'}")
    return True


def _install_codex(non_interactive: bool, *, force: bool = False) -> bool:
    if not cmd_exists("npm"):
        warn("npm is required to install OpenAI Codex CLI")
        return False

    if not force and cmd_version_at_least("codex", STACK_VERSION_FLOORS["codex"]):
        if not ask(
            "Reinstall OpenAI Codex CLI", default=False, non_interactive=non_interactive
        ):
            skip("OpenAI Codex CLI: at or above the reviewed version")
            return True
    elif cmd_exists("codex"):
        warn("OpenAI Codex CLI: below the reviewed version; installing the latest release")

    info("Installing OpenAI Codex CLI...")
    run(["npm", "install", "-g", "--force", OPENAI_CODEX_PACKAGE])
    if not cmd_version_at_least("codex", STACK_VERSION_FLOORS["codex"]):
        warn("OpenAI Codex CLI: installed version is below the reviewed version")
        return False
    ok("OpenAI Codex CLI: installed")
    return True


def _install_claude(non_interactive: bool, *, force: bool = False) -> bool:
    if not force and cmd_version_at_least("claude", STACK_VERSION_FLOORS["claude"]):
        if not ask(
            "Reinstall Claude Code", default=False, non_interactive=non_interactive
        ):
            skip("Claude Code: at or above the reviewed version")
            return True
    elif cmd_exists("claude"):
        warn("Claude Code: below the reviewed version; installing the latest release")

    info("Installing Claude Code...")
    if not run_remote_script(
        label="Claude installer",
        url=CLAUDE_INSTALL_URL,
        expected_sha256=CLAUDE_INSTALL_SHA256,
        interpreter="bash",
        interpreter_args=["latest"],
    ):
        return False
    if not cmd_version_at_least("claude", STACK_VERSION_FLOORS["claude"]):
        warn("Claude Code: installed version is below the reviewed version")
        return False
    ok("Claude Code: installed")
    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Hermes/OMP/Codex/Claude. Returns non-zero on any selected-step failure."
    )
    parser.add_argument(
        "--all", action="store_true", help="Install all tools without prompting"
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
        ok("agentic-install-agents: remote contract check passed")
        return 0

    rows = [
        Option("hermes", "Hermes Agent", True),
        Option("omp", "OMP / Oh My Pi", True),
        Option("codex", "OpenAI Codex CLI", True),
        Option("claude", "Claude Code", True),
    ]
    if args.all:
        picked = [option.value for option in rows]
    elif non_interactive:
        picked = []
    else:
        picked = choose("Select agent CLIs to install", rows)

    do_hermes = "hermes" in picked
    do_omp = "omp" in picked
    do_codex = "codex" in picked
    do_claude = "claude" in picked

    ok_all = True
    if do_hermes:
        ok_all = _install_hermes(non_interactive) and ok_all
    else:
        skip("Hermes Agent: skipped")

    if do_omp:
        ok_all = _install_omp(non_interactive) and ok_all
    else:
        skip("OMP / Oh My Pi: skipped")

    if do_codex:
        ok_all = _install_codex(non_interactive) and ok_all
    else:
        skip("OpenAI Codex CLI: skipped")

    if do_claude:
        ok_all = _install_claude(non_interactive) and ok_all
    else:
        skip("Claude Code: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
