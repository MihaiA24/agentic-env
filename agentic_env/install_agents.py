"""Install agent CLIs and opt-in desktop ACP clients."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import platform
import re
import shutil
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

_DESKTOP_CLIENTS = {
    "t3code": ("T3 Code", "t3-code", ("T3 Code (Beta).app", "T3 Code (Alpha).app", "T3 Code.app")),
    "pycharm": ("PyCharm", "pycharm", ("PyCharm.app",)),
}


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

    install_dir = Path(os.environ.get("PI_INSTALL_DIR") or Path.home() / ".local" / "bin")
    floor = STACK_VERSION_FLOORS["omp"]
    request = urllib.request.Request(
        f"{release}/{asset}", headers={"User-Agent": "agentic-env/1.0"}
    )
    temporary: str | None = None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            install_dir.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".omp.", dir=install_dir)
            digest = hashlib.sha256()
            # Streamed in 1 MiB chunks; the checksum below catches truncation.
            with os.fdopen(fd, "wb") as target:
                while chunk := response.read(1 << 20):
                    digest.update(chunk)
                    target.write(chunk)
        actual = digest.hexdigest()
        if actual != expected[0].lower():
            warn(f"OMP / Oh My Pi: {tag}/{asset} checksum mismatch")
            warn(f"OMP / Oh My Pi: expected {expected[0]}, got {actual}")
            return False
        os.chmod(temporary, 0o755)
        if not cmd_version_at_least(temporary, floor):
            warn("OMP / Oh My Pi: downloaded executable fails the reviewed version floor")
            return False
        os.replace(temporary, install_dir / "omp")
        temporary = None
    except Exception as exc:
        warn(f"OMP / Oh My Pi: failed to install {tag}/{asset}: {exc}")
        return False
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.remove(temporary)
    installed = install_dir / "omp"
    info(f"OMP / Oh My Pi: installed {tag} to {installed}")
    # A different omp earlier on PATH wins, whatever its version; report it
    # rather than touch it. Aliases resolving to the installed file are fine.
    on_path = shutil.which("omp")
    if on_path is None or not os.path.samefile(on_path, installed):
        warn(f"OMP / Oh My Pi: `omp` on PATH ({on_path or 'not found'}) is not {installed}")
        warn(f"OMP / Oh My Pi: put {install_dir} first on PATH or remove the other omp")
        return False
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
    elif not force and cmd_exists("codex"):
        warn("OpenAI Codex CLI: below the reviewed version; installing the latest release")

    info("Installing OpenAI Codex CLI...")
    try:
        run(["npm", "install", "-g", "--force", OPENAI_CODEX_PACKAGE])
    except (OSError, subprocess.CalledProcessError) as exc:
        warn(f"OpenAI Codex CLI: npm install failed: {exc}")
        return False
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
    elif not force and cmd_exists("claude"):
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


def _install_desktop_client(client: str) -> bool:
    label, cask, bundles = _DESKTOP_CLIENTS[client]
    if platform.system() != "Darwin":
        warn(f"{label}: automatic desktop installation requires macOS/Homebrew; see guides/omp-acp.md for manual installation")
        return False
    if any(
        (directory / bundle).is_dir()
        for directory in (Path("/Applications"), Path.home() / "Applications")
        for bundle in bundles
    ) or (client == "pycharm" and cmd_exists("pycharm")):
        skip(f"{label}: already installed; use its app updater or package manager for updates")
        return True
    if not cmd_exists("brew"):
        warn(f"{label}: Homebrew is required; install it or install the app manually (guides/omp-acp.md)")
        return False
    try:
        def installed() -> bool:
            result = subprocess.run(
                ["brew", "list", "--cask", "--versions", cask],
                capture_output=True, text=True, check=False,
            )
            return result.returncode == 0 and bool(result.stdout.strip())

        if installed():
            skip(f"{label}: Homebrew cask already installed")
            return True
        info(f"Installing {label} with Homebrew...")
        run(["brew", "install", "--cask", cask])
        if not installed():
            warn(f"{label}: Homebrew did not register the installed cask")
            return False
    except (OSError, subprocess.CalledProcessError) as exc:
        warn(f"{label}: Homebrew installation failed: {exc}")
        return False
    ok(f"{label}: installed; register OMP with agentic-configure-acp --client {client}")
    return True


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Hermes/OMP/Codex/Claude and optional desktop ACP clients."
    )
    parser.add_argument(
        "--all", action="store_true", help="Install all agent CLIs without prompting (desktop clients remain opt-in)"
    )
    parser.add_argument(
        "--client", action="append", choices=tuple(_DESKTOP_CLIENTS),
        help="Install a desktop client on macOS via Homebrew; repeat for both. Does not configure ACP",
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

    installers = [
        (Option("hermes", "Hermes Agent", True), _install_hermes),
        (Option("omp", "OMP / Oh My Pi", True), _install_omp),
        (Option("codex", "OpenAI Codex CLI", True), _install_codex),
        (Option("claude", "Claude Code", True), _install_claude),
        (Option("t3code", "T3 Code desktop (macOS/Homebrew)"), lambda _: _install_desktop_client("t3code")),
        (Option("pycharm", "PyCharm desktop (macOS/Homebrew)"), lambda _: _install_desktop_client("pycharm")),
    ]
    rows = [option for option, _ in installers]
    if args.all:
        picked = [option.value for option in rows if option.value not in _DESKTOP_CLIENTS]
    elif args.client:
        picked = []
    elif non_interactive:
        picked = []
    else:
        picked = choose("Select agents and desktop clients to install", rows)
    picked.extend(args.client or [])

    ok_all = True
    for option, installer in installers:
        if option.value in picked:
            ok_all = installer(non_interactive) and ok_all
        else:
            skip(f"{option.label}: skipped")

    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
