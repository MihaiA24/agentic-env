"""Opt-in Linux OMP isolation; never changes normal OMP startup or personal state."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import secrets
import shutil
import socket
import subprocess
import tarfile
import tempfile
from pathlib import Path

from .common import verified_download, warn

NONO_VERSION = "0.81.0"
NONO_ASSET = "nono-v0.81.0-x86_64-unknown-linux-gnu.tar.gz"
NONO_SHA256 = "7ecc33ff9c349bdfa84b4496e7a7555f67bcc33f1e125c7df9efb653c6c4e569"
NONO_URL = f"https://github.com/nolabs-ai/nono/releases/download/v{NONO_VERSION}/{NONO_ASSET}"


def _host_check() -> None:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("isolation requires the reviewed Linux x86_64 host; SSH clients need no installation")
    # Linux x86_64 landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION).
    # ABI 6 includes truncate, refer, TCP filtering and required signal scoping.
    abi = ctypes.CDLL(None, use_errno=True).syscall(444, 0, 0, 1)
    if abi < 6:
        raise ValueError(f"Landlock ABI >= 6 required, found {abi}; refusing an unenforced/partial launch")


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _instance_path(path: Path) -> Path:
    absolute = path.expanduser().absolute()
    resolved = absolute.resolve()
    if absolute != resolved:
        raise ValueError("instance path must be canonical, with no symlink components or '..'")
    return resolved


def _guard_paths(instance: Path, project: Path) -> None:
    if instance.is_relative_to(project) or project.is_relative_to(instance):
        raise ValueError("project and trusted instance must not overlap")
    if Path.home().resolve().is_relative_to(project):
        raise ValueError("refusing to grant the operator home or an ancestor")
    if Path(__file__).resolve().is_relative_to(project):
        raise ValueError("install/run this launcher outside the sandbox-writable project")
    if not project.is_dir() or project.resolve(strict=True) != project:
        raise ValueError("project must remain its original canonical directory")


def _environment(instance: Path) -> dict[str, str]:
    import pwd

    home = instance / "broker"
    user = pwd.getpwuid(os.getuid()).pw_name
    return {
        "HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
        "TERM": os.environ.get("TERM", "xterm-256color"), "USER": user, "LOGNAME": user,
        "TMPDIR": "/tmp", "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_DATA_HOME": str(home / "data"), "XDG_STATE_HOME": str(home / "state"),
        "XDG_CACHE_HOME": str(home / "cache"), "XDG_RUNTIME_DIR": str(home / "run"),
    }


def _profile(instance: Path, project: Path) -> dict:
    runtime = instance / "runtime"
    return {
        "meta": {"name": "agentic-omp-isolated", "description": "Reviewed opt-in policy; no runtime elevation"},
        # Keep required deny groups, but remove implicit system/home/tool/scratch grants.
        "groups": {"exclude": [
            "system_read_macos", "system_read_linux_core", "system_write_macos", "system_write_linux",
            "user_tools", "homebrew_macos", "homebrew_linux", "dangerous_commands",
            "dangerous_commands_macos", "dangerous_commands_linux",
        ]},
        "workdir": {"access": "none"},
        "filesystem": {
            "allow": [str(project), str(runtime)],
            "read": ["/usr", "/etc/ssl/certs"],
            "read_file": [
                str(instance / "bin" / "omp"), "/etc/ld.so.cache", "/etc/passwd", "/etc/group",
                "/etc/ssl/certs/ca-certificates.crt", "/etc/ssl/openssl.cnf",
                "/dev/urandom", "/dev/random", "/proc/self/maps",
            ],
            "allow_file": ["/dev/null", "/dev/tty", "/dev/ptmx"],
        },
        "network": {"allow_domain": [
            "auth.openai.com", "chatgpt.com", "github.com", "codeload.github.com",
            "objects.githubusercontent.com", "registry.npmjs.org", "pypi.org", "files.pythonhosted.org",
        ]},
        "linux": {
            "sandbox_policy": "auto", "af_unix_mediation": "pathname",
            "isolate": {"network": True, "ipc": True, "uts": True},
        },
        "security": {"capability_elevation": False, "signal_mode": "allow_same_sandbox"},
        "environment": {
            "allow_vars": ["PATH", "TERM", "LANG", "USER", "LOGNAME"],
            "set_vars": {
                "HOME": str(runtime / "home"), "TMPDIR": str(runtime / "tmp"),
                "PI_CODING_AGENT_DIR": str(runtime / "agent"),
                "XDG_CONFIG_HOME": str(runtime / "config"), "XDG_DATA_HOME": str(runtime / "data"),
                "XDG_STATE_HOME": str(runtime / "state"), "XDG_CACHE_HOME": str(runtime / "cache"),
                "XDG_RUNTIME_DIR": str(runtime / "run"),
            },
        },
        "command_policies": {"commands": {
            name: {"from": {"session": "deny"}}
            for name in ("sudo", "su", "doas", "pkexec", "mount", "umount", "nsenter", "unshare",
                         "systemctl", "machinectl", "reboot", "shutdown", "poweroff")
            if shutil.which(name, path="/usr/bin:/bin")
        }},
        "open_urls": {"allow_origins": [], "allow_localhost": False},
    }


def _command(instance: Path, command: list[str]) -> list[str]:
    return [str(instance / "bin" / "nono"), "run", "--profile", str(instance / "policy.json"),
            "--strict-broker-path", "--no-rollback", "--no-diagnostics", "--", *command]


def _load(instance: Path) -> dict:
    data = json.loads((instance / "manifest.json").read_text())
    project = Path(data["project"])
    _guard_paths(instance, project)
    for name, expected in data["sha256"].items():
        path = instance / name
        if name not in ("policy.json", "bin/nono", "bin/omp") or path.is_symlink() or _digest(path) != expected:
            raise ValueError(f"trusted file changed: {name}; review and initialize a new instance")
    if set(data["sha256"]) != {"policy.json", "bin/nono", "bin/omp"}:
        raise ValueError("incomplete instance manifest")
    # Writable runtime directories must never redirect supervisor state or grants.
    for path in (instance / "bin", instance / "broker", instance / "runtime"):
        if path.is_symlink() or path.resolve(strict=True) != path:
            raise ValueError(f"instance directory changed: {path}")
    return data


def _initialize(instance: Path, project: Path, omp: str) -> None:
    _guard_paths(instance, project)
    if instance.exists():
        raise FileExistsError(f"{instance}: already exists; initialization never overwrites state")
    source = shutil.which(os.path.expanduser(omp))
    if not source:
        raise ValueError(f"OMP executable not found: {omp}")
    source_path = Path(source).resolve(strict=True)
    with source_path.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            raise ValueError("OMP must be the standalone Linux ELF executable, not a shell wrapper")
    instance.parent.mkdir(parents=True, exist_ok=True)
    instance.mkdir(mode=0o700)
    try:
        for directory in ("bin", "broker", "runtime"):
            (instance / directory).mkdir(mode=0o700)
        for directory in ("tmp", "config", "data", "state", "cache", "run"):
            (instance / "broker" / directory).mkdir(mode=0o700)
        for directory in ("home", "agent", "tmp", "config", "data", "state", "cache", "run"):
            (instance / "runtime" / directory).mkdir(mode=0o700)
        shutil.copyfile(source_path, instance / "bin" / "omp")
        (instance / "bin" / "omp").chmod(0o500)
        with verified_download(NONO_URL, NONO_SHA256, 120) as archive_path:
            with tarfile.open(archive_path, "r:gz") as archive:
                members = [m for m in archive.getmembers() if m.isfile() and Path(m.name).name == "nono"]
                if len(members) != 1:
                    raise ValueError("release must contain exactly one nono executable")
                with archive.extractfile(members[0]) as source, (instance / "bin" / "nono").open("xb") as target:
                    shutil.copyfileobj(source, target)
        (instance / "bin" / "nono").chmod(0o500)
        (instance / "policy.json").write_text(json.dumps(_profile(instance, project), indent=2) + "\n")
        (instance / "manifest.json").write_text(json.dumps({
            "project": str(project), "nono_version": NONO_VERSION,
            "sha256": {name: _digest(instance / name) for name in ("policy.json", "bin/nono", "bin/omp")},
        }, indent=2) + "\n")
        # A version-only launch still applies all required mechanisms before running OMP.
        subprocess.run(_command(instance, [str(instance / "bin" / "omp"), "--version"]),
                       cwd=project, env=_environment(instance), check=True, timeout=60)
    except BaseException:
        shutil.rmtree(instance)
        raise
    print(f"Initialized {instance}\nProject: {project}\nNo personal configuration or credentials copied.")


def _check(instance: Path, project: Path) -> int:
    from . import isolation_probe

    with tempfile.TemporaryDirectory(prefix="agentic-isolation-canary-") as outside_dir:
        outside = Path(outside_dir) / "secret"
        nonce = secrets.token_hex(16)
        outside.write_text(nonce)
        # The host socket deliberately lives inside a filesystem write grant.
        with tempfile.TemporaryDirectory(prefix=".isolation-check-", dir=project) as project_dir:
            inside = Path(project_dir)
            (inside / "input").write_text(nonce)
            (inside / "escape").symlink_to(outside)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(str(inside / "host.sock"))
                server.listen(1)
                arguments = {
                    "project": str(inside), "input": "input", "output": "output", "nonce": nonce,
                    "outside": str(outside), "symlink": "escape", "socket": str(inside / "host.sock"),
                    "policy": str(instance / "policy.json"), "omp": str(instance / "bin" / "omp"),
                }
                environment = _environment(instance)
                environment.update({name: "dummy-not-a-real-credential" for name in (
                    "AGENTIC_DUMMY_SECRET", "OPENAI_API_KEY", "PROTON_PASS_CLI_PAT", "SSH_AUTH_SOCK",
                    "DBUS_SESSION_BUS_ADDRESS", "GPG_AGENT_INFO", "DISPLAY", "WAYLAND_DISPLAY",
                )})
                result = subprocess.run(
                    _command(instance, ["/usr/bin/python3", "-I", "-c",
                                        Path(isolation_probe.__file__).read_text(), json.dumps(arguments)]),
                    cwd=project, env=environment, check=False, timeout=90,
                )
                if result.returncode == 0:
                    if outside.read_text() != nonce or (inside / "output").read_text() != nonce:
                        raise ValueError("sandbox scenario modified outside data or lost project output")
                return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, default=Path.home() / ".local/share/agentic-env/isolated-omp",
                        help="Trusted instance outside the project; init refuses existing paths")
    commands = parser.add_subparsers(dest="action", required=True)
    initialize = commands.add_parser("init", help="Download reviewed nono, snapshot OMP and create a new isolated instance")
    initialize.add_argument("--project", type=Path, required=True,
                            help="One existing project, normally beneath ~/code/agent-workspaces")
    initialize.add_argument("--omp", default="omp", help="Standalone OMP executable to snapshot")
    run = commands.add_parser("run", help="Run OMP and its entire process tree under the reviewed policy")
    run.add_argument("arguments", nargs=argparse.REMAINDER, help="OMP arguments after --, including login")
    commands.add_parser("check", help="Run real filesystem, environment, socket, network and command scenarios")
    args = parser.parse_args(argv)
    try:
        _host_check()
        instance = _instance_path(args.instance)
        if args.action == "init":
            _initialize(instance, args.project.expanduser().resolve(strict=True), args.omp)
            return 0
        data = _load(instance)
        project = Path(data["project"])
        if args.action == "check":
            return _check(instance, project)
        arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        return subprocess.run(_command(instance, [str(instance / "bin" / "omp"), *arguments]),
                              cwd=project, env=_environment(instance), check=False).returncode
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        warn(f"Isolated OMP failed (no unsandboxed fallback): {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
