#!/usr/bin/env python3
"""Drive agentic-env through its existing CLIs in a checkout-owned sandbox."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
PROFILE = "agentic-env-" + hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:12]
BASE = ROOT / ".verifier" / PROFILE
DATA = BASE / "workspace"
EVIDENCE = BASE / "evidence"
ENTRIES = {
    "bootstrap": "bootstrap", "install-agents": "install_agents",
    "install-skills": "install_skills_mcps", "configure": "configure_agent_mcps",
    "configure-acp": "configure_acp",
    "stack-doctor": "stack_doctor", "drift": "skill_drift", "update": "update_agentic_stack",
}
SUITES = {
    "all": ["tests"], "copy": ["tests/test_copy_skills.py"],
    "pickers": ["tests/test_install_skills_mcps.py", "-k", "guided"],
    "configure": ["tests/test_configure_agent_mcps.py"],
    "bootstrap": ["tests/test_bootstrap.py"], "drift": ["tests/test_skill_drift.py"],
    "doctor": ["tests/test_stack_doctor.py"], "verifier": ["tests/test_verifier.py"],
}


def emit(value: object) -> None:
    print(json.dumps(value, indent=2))


def safe_paths() -> None:
    # Never follow a workspace/evidence replacement into another checkout or HOME.
    paths = [ROOT / ".verifier", BASE, DATA, EVIDENCE, BASE / "owner.json", BASE / "lock",
             BASE / "cache", BASE / "cache/uv", BASE / "cache/npm", BASE / "cache/python",
             DATA / "home", DATA / "skills", DATA / "acp", DATA / "venv", DATA / "npm", DATA / "tools", DATA / "bin"]
    home = DATA / "home"
    paths.extend(home / name for name in (".config", ".local", ".local/share", ".npmrc", ".jetbrains", ".t3"))
    # External version probes can create executable links; protect writable
    # directories and managed configs, not harmless references to executables.
    paths.extend(path for path in home.rglob("*") if path.is_dir())
    for name in (".omp", ".pi", ".hermes", ".jetbrains", ".t3"):
        paths.extend((home / name).rglob("*"))
    paths.extend((DATA / "acp").rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Refusing symlink {path}; restore this checkout's own verifier directory.")


def fingerprint() -> str:
    files = {ROOT / "pyproject.toml", ROOT / "uv.lock"}
    for directory in (ROOT / "agentic_env", ROOT / "tests", ROOT / "omp", Path(__file__).parent.parent):
        files.update(p for p in directory.rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.suffix != ".pyc")
    files.update(ROOT.glob("*.sh"))
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(os.fsencode(path.relative_to(ROOT)))
        digest.update(b"\0" + str(path.stat().st_mode & 0o777).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def owner(required: bool = True) -> dict[str, Any]:
    safe_paths()
    path = BASE / "owner.json"
    if not path.exists():
        if required or BASE.exists():
            raise ValueError(f"No ownership record at {path}; do not attach. Inspect the directory, then use a fresh checkout.")
        return {}
    record = json.loads(path.read_text())
    if not isinstance(record, dict):
        raise ValueError(f"Invalid ownership record at {path}; inspect it before using this workspace.")
    if record.get("checkout") != str(ROOT) or record.get("profile") != PROFILE:
        raise ValueError(f"Workspace belongs to {record.get('checkout')!r}; use that checkout's verifier, not this one.")
    return record


@contextmanager
def locked():
    safe_paths()
    if BASE.exists():
        owner()
    else:
        BASE.mkdir(parents=True)
        (BASE / "owner.json").write_text(json.dumps({"checkout": str(ROOT), "profile": PROFILE}))
    with (BASE / "lock").open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            raise ValueError(f"Verifier busy (PID {handle.read().strip()}); wait for that command to exit; do not attach.") from None
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        try:
            yield
        finally:
            handle.seek(0)
            handle.truncate()


def environment() -> dict[str, str]:
    home = DATA / "home"
    env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TERM", "TMPDIR", "SYSTEMROOT") if key in os.environ}
    env.update({
        "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"), "XDG_CACHE_HOME": str(BASE / "cache"),
        "UV_PROJECT_ENVIRONMENT": str(DATA / "venv"), "UV_CACHE_DIR": str(BASE / "cache/uv"),
        "UV_NO_CONFIG": "1", "UV_TOOL_DIR": str(DATA / "tools"), "UV_TOOL_BIN_DIR": str(DATA / "bin"),
        "UV_PYTHON_INSTALL_DIR": str(BASE / "cache/python"),
        "NPM_CONFIG_CACHE": str(BASE / "cache/npm"), "NPM_CONFIG_PREFIX": str(DATA / "npm"),
        "NPM_CONFIG_USERCONFIG": str(home / ".npmrc"), "GIT_CONFIG_NOSYSTEM": "1",
        "AGENTIC_ENV_ROOT": str(ROOT), "PYTHONUNBUFFERED": "1", "NO_COLOR": "1",
        "COMPOSE_PROJECT_NAME": PROFILE,
    })
    return env


def inventory() -> dict[str, Any]:
    result = {}
    for directory in (DATA / "skills", DATA / "home", DATA / "acp"):
        if directory.is_symlink():
            raise ValueError(f"Refusing symlink {directory}; cleanup the owned workspace first.")
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            relative = str(path.relative_to(DATA))
            if path.is_symlink():
                result[relative] = {"symlink": os.readlink(path)}
            elif path.is_file():
                result[relative] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


def port_owners(port: int) -> list[dict[str, Any]]:
    if not shutil.which("lsof"):
        raise ValueError("Port inspection needs lsof; install it, then rerun doctor --port PORT.")
    result = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fpcu"], capture_output=True, text=True)
    if result.returncode not in (0, 1) or result.stderr.strip():
        raise ValueError(f"Cannot establish port ownership: {result.stderr.strip()}; inspect with lsof before driving.")
    owners = []
    for line in result.stdout.splitlines():
        if line.startswith("p"):
            owners.append({"pid": int(line[1:]), "owned": False})
        elif owners and line[:1] in ("c", "u"):
            owners[-1][{"c": "command", "u": "uid"}[line[0]]] = line[1:]
    for item in owners:
        cwd = subprocess.run(["lsof", "-a", "-p", str(item["pid"]), "-d", "cwd", "-Fn"], capture_output=True, text=True)
        item["cwd"] = next((s[1:] for s in cwd.stdout.splitlines() if s.startswith("n")), "unknown")
    return owners


def doctor(port: int | None = None) -> dict[str, Any]:
    record = owner(required=False)
    current = fingerprint()
    state = DATA / "build.json"
    if state.is_symlink():
        raise ValueError(f"Refusing symlink {state}; restore the owned workspace.")
    built = json.loads(state.read_text()) if state.exists() else {}
    if not isinstance(built, dict):
        raise ValueError(f"Invalid build record at {state}; run cleanup and launch again.")
    python = DATA / "venv/bin/python"
    listeners = port_owners(port) if port is not None else []
    fresh = bool(record and built.get("fingerprint") == current and python.is_file())
    return {
        "checkout": str(ROOT), "profile": PROFILE, "data_directory": str(DATA),
        "evidence_directory": str(EVIDENCE), "process": "short-lived CLI; no persistent instance",
        "ports": [] if port is None else [{"port": port, "owners": listeners}],
        "port_owner": "not applicable: this repository declares no TCP listeners" if port is None else listeners,
        "build": "current" if fresh else "stale" if built else "not-launched",
        "fingerprint": current, "built_fingerprint": built.get("fingerprint"),
        "ready": fresh and not listeners,
        "next": "drive a mapped feature" if fresh and not listeners else
                "Do not attach to these listeners; stop them from their owning checkout." if listeners else
                "Run ./.agents/skills/verify-agentic-env/verifier/control.py launch, then doctor; stale builds are not evidence.",
    }


def require_current() -> str:
    report = doctor()
    if not report["ready"]:
        raise ValueError(report["next"])
    return report["fingerprint"]


def run(command: list[str], label: str, timeout: float, *, building: bool = False) -> int:
    before = fingerprint() if building else require_current()
    EVIDENCE.mkdir(exist_ok=True)
    target = EVIDENCE / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-") + label + "-" + uuid.uuid4().hex[:6])
    target.mkdir()
    metadata: dict[str, Any] = {"checkout": str(ROOT), "profile": PROFILE, "command": command, "cwd": str(ROOT),
                "fingerprint": before, "started": datetime.now(timezone.utc).isoformat(),
                "before": inventory(), "kind": "setup" if building else "regression-test" if label == "tests" else "user-path"}
    code = 1
    with (target / "stdout.txt").open("w") as stdout, (target / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=environment(), stdin=subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 130 if isinstance(exc, KeyboardInterrupt) else 124
            metadata["error"] = "cancelled" if code == 130 else f"deadline exceeded ({timeout}s); inspect logs, not fixed sleeps"
    after = fingerprint()
    metadata.update({"exit_code": code, "finished": datetime.now(timezone.utc).isoformat(),
                     "after": inventory(), "source_unchanged": after == before,
                     "valid_evidence": not building and after == before and code not in (124, 130)})
    (target / "result.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print((target / "stdout.txt").read_text(), end="")
    print((target / "stderr.txt").read_text(), end="", file=sys.stderr)
    print(f"\nEvidence: {target}")
    if after != before:
        raise ValueError("Source changed during the command; evidence invalid. Run launch and repeat the user path.")
    return code


def cli(entry: str, style: str) -> list[str]:
    prefix = ["uv", "run", "--frozen"]
    if style == "console":
        name = {"install-skills": "install-skills-mcps", "configure": "configure-agent-mcps", "update": "update-stack", "drift": "skill-drift"}.get(entry, entry)
        return prefix + ["agentic-" + name]
    return prefix + ["python", "-m", "agentic_env." + ENTRIES[entry]]


def drive_command(args: argparse.Namespace) -> list[str]:
    if args.action == "copy":
        command = ["uv", "run", "--frozen", "python"]
        command += ["-I", "-S", str(ROOT / "agentic_env/copy_skills.py")] if args.entry == "script" else ["-m", "agentic_env.copy_skills"]
        command += ["--skills-dir", str(DATA / "skills")]
        if not args.all:
            for skill in args.skill if args.skill is not None else ["writing-for-agents"]:
                command += ["--skill", skill]
        return command
    if args.action == "tests":
        return ["uv", "run", "--frozen", "pytest", "-q", "-p", "no:cacheprovider", *SUITES[args.suite]]
    command = cli(args.action if args.action != "help" else args.command, args.entry)
    if args.action == "help":
        return command + ["--help"]
    if args.action == "bootstrap":
        command += ["--summary-format", args.format]
        if args.mode == "plan":
            command += ["--dry-run"]
        else:
            command += ["--skip-" + phase for phase in ("install-agents", "install-skills", "configure", "doctor")]
    if args.action == "configure":
        command += ["--yes", "--agent", args.agent, "--server", args.server]
        if args.no_skills:
            command += ["--no-skills"]
        if args.dry_run:
            command += ["--dry-run"]
    if args.action == "configure-acp":
        executable = shutil.which("omp")
        if executable is None:
            raise ValueError("ACP verification needs the real omp executable on host PATH; install OMP, then retry.")
        command += ["--omp", str(Path(executable).absolute())]
        for client in args.client:
            command += ["--client", client]
        if args.mode == "export":
            command += ["--output-dir", str(DATA / "acp")]
        if args.dry_run:
            command += ["--dry-run"]
    if args.action == "drift":
        command += ["--offline", "--no-upstream", "--no-installed"]
        for pack in args.pack or []:
            command += ["--pack", pack]
        if args.format == "json":
            command += ["--json"]
    if args.action == "install-skills":
        command += ["--yes", "--skills-dir", str(DATA / "skills"), "--skill-pack", args.pack, "--skill", args.skill]
    return command


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples (from the checkout):
  V=./.agents/skills/verify-agentic-env/verifier/control.py
  "$V" launch
  "$V" doctor
  "$V" drive copy --skill writing-for-agents
  "$V" drive inspect
  "$V" logs
  "$V" cleanup --dry-run

No service or port is invented: these are synchronous CLI processes.
Evidence survives cleanup; host HOME/configuration and credentials are not inherited.""")
    p.add_argument("--timeout", type=float, default=180, help="Observable process-exit deadline in seconds, not a readiness sleep (default: 180)")
    subs = p.add_subparsers(dest="operation", required=True)
    d = subs.add_parser("doctor", help="Read-only checkout ownership, source/build freshness and optional listener ownership")
    d.add_argument("--port", type=int, help="Inspect an explicitly relevant TCP port with lsof; any listener is foreign (we start no server)")
    subs.add_parser("launch", help="Sync this checkout's uv environment and record its exact source fingerprint; no daemon")
    drive = subs.add_parser("drive", help="Drive real commands in the owned sandbox; each command records actions, output, exit and file hashes")
    actions = drive.add_subparsers(dest="action", required=True)
    copy = actions.add_parser("copy", help="Run the dependency-free copier into workspace/skills; collisions/errors are preserved, not hidden")
    selection = copy.add_mutually_exclusive_group()
    selection.add_argument("--skill", action="append", help="Repeat or comma-separate; default: writing-for-agents; an empty string exercises the error path")
    selection.add_argument("--all", action="store_true", help="Copy every locally packaged skill and report remote-only exclusions")
    copy.add_argument("--entry", choices=("script", "module"), default="script", help="Direct isolated Python script (-I -S), or Python module")
    copy.add_argument("--dry-run", action="store_true", help="Print the wrapper's plan without running/copying; NOT application evidence")
    actions.add_parser("inspect", help="Read persisted sandbox file hashes after a user path (not an action or eval setter)")
    tests = actions.add_parser("tests", help="Reuse repository pytest suites, including its existing prompt-driven PTY harness")
    tests.add_argument("--suite", choices=tuple(SUITES), default="all", help="Existing suite to run (default: all); picker tests mock install boundaries, not live provisioning proof")
    for entry in ("bootstrap", "configure", "configure-acp", "drift", "stack-doctor", "help", "install-skills"):
        sub = actions.add_parser(entry, help={
            "bootstrap": "Safe bootstrap plans or real all-skipped reports; never provisions the host",
            "configure": "Write/read sandbox MCP configuration using the real configurator",
            "configure-acp": "Configure sandbox ACP clients or export native JSON using the real host OMP executable",
            "drift": "Offline repository-source checks; never accepts/rewrites a baseline",
            "stack-doctor": "Diagnose sandbox stack; missing unprovisioned binaries/config may fail",
            "help": "Exercise a management CLI's own help entry point",
            "install-skills": "Native custom-directory install of a local pack (requires npm/network); never selects agent roots",
        }[entry])
        sub.add_argument("--entry", choices=("module", "console"), default="module", help="Checkout module or checkout uv environment's installed console command")
        if entry == "bootstrap":
            sub.add_argument("--mode", choices=("plan", "skip"), default="plan", help="plan uses app --dry-run; skip really executes an all-skipped workflow")
            sub.add_argument("--format", choices=("json", "text"), default="json", help="App report format")
        elif entry == "configure":
            sub.add_argument("--agent", choices=("omp", "hermes", "all"), default="omp", help="Sandbox configuration target")
            sub.add_argument("--server", choices=("codebase-memory-mcp", "agentmemory", "all"), default="codebase-memory-mcp", help="MCP entry to configure")
            sub.add_argument("--no-skills", action="store_true", help="Exercise app flag that skips matching skill descriptors")
            sub.add_argument("--dry-run", action="store_true", help="App dry run; compare before/after hashes to establish what it skips")
        elif entry == "configure-acp":
            sub.add_argument("--client", action="append", choices=("pycharm", "t3code"), required=True, help="Sandbox client; repeat to select both")
            sub.add_argument("--mode", choices=("native", "export"), default="native", help="Native sandbox settings or JSON exports in workspace/acp")
            sub.add_argument("--dry-run", action="store_true", help="App preflight without configuration writes or backups")
        elif entry == "drift":
            sub.add_argument("--pack", action="append", help="Manifest pack name; repeat to scope source checks")
            sub.add_argument("--format", choices=("json", "text"), default="json", help="App report format")
        elif entry == "help":
            sub.add_argument("command", choices=tuple(ENTRIES), help="Management command whose --help to execute")
        elif entry == "install-skills":
            sub.add_argument("--pack", choices=("mattpocock", "pstack", "agentic-env"), default="mattpocock", help="Locally packaged pack only")
            sub.add_argument("--skill", default="writing-for-agents", help="Skill name(s) in this pack; invalid/empty values exercise errors")
            sub.add_argument("--dry-run", action="store_true", help="Print wrapper plan; no npm/network/copy, NOT application evidence")
    logs = subs.add_parser("logs", help="Read retained evidence, including after cleanup")
    logs.add_argument("--run", help="Evidence directory basename (default: latest)")
    cleanup = subs.add_parser("cleanup", help="Remove only this checkout's owned workspace/cache; never evidence or foreign processes")
    cleanup.add_argument("--dry-run", action="store_true", help="Show exact removals without deleting anything")
    return p


def main(argv: list[str] | None = None) -> int:
    p = parser()
    args = p.parse_args(argv)
    if args.timeout <= 0:
        p.error("--timeout must be positive; use a bounded process-exit deadline")
    if args.operation == "doctor" and args.port is not None and not 1 <= args.port <= 65535:
        p.error("--port must be between 1 and 65535; use the app's actual port")
    try:
        if args.operation == "doctor":
            report = doctor(args.port)
            emit(report)
            return 0 if report["ready"] else 1
        if args.operation == "logs":
            owner()
            candidates = sorted(EVIDENCE.iterdir()) if EVIDENCE.exists() else []
            target = EVIDENCE / args.run if args.run else candidates[-1] if candidates else None
            if target is None or target.parent != EVIDENCE or target.is_symlink() or not target.is_dir():
                raise ValueError("No such evidence run; use the basename printed by a drive command (or run a feature first).")
            for name in ("result.json", "stdout.txt", "stderr.txt", "state.json"):
                path = target / name
                if path.is_file():
                    print(f"--- {path} ---\n{path.read_text()}")
            return 0
        if args.operation == "cleanup" and args.dry_run:
            owner()
            emit({"would_remove": [str(DATA), str(BASE / "cache")], "preserved": str(EVIDENCE)})
            return 0
        with locked():
            if args.operation == "cleanup":
                for path in (DATA, BASE / "cache"):
                    if path.is_symlink():
                        raise ValueError(f"Refusing symlink {path}; inspect its owner instead.")
                    if path.exists():
                        shutil.rmtree(path)
                emit({"removed": [str(DATA), str(BASE / "cache")], "preserved": str(EVIDENCE)})
                return 0
            if args.operation == "launch":
                (DATA / "home").mkdir(parents=True, exist_ok=True)
                state = DATA / "build.json"
                if state.exists() or state.is_symlink():
                    state.unlink()
                code = run(["uv", "sync", "--frozen"], "launch", args.timeout, building=True)
                if code == 0:
                    state.write_text(json.dumps({"fingerprint": fingerprint()}) + "\n")
                    emit(doctor())
                return code
            require_current()
            if args.action == "inspect":
                return inspect_state()
            command = drive_command(args)
            if args.action in ("copy", "install-skills") and args.dry_run:
                emit({"command": command, "executed": False, "evidence": False, "next": "Omit --dry-run to exercise the application."})
                return 0
            return run(command, args.action, args.timeout)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Verifier: {exc}", file=sys.stderr)
        return 1


def inspect_state() -> int:
    # Read only, after actions; retained independently of the mutable workspace.
    EVIDENCE.mkdir(exist_ok=True)
    target = EVIDENCE / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-inspect-") + uuid.uuid4().hex[:6])
    target.mkdir()
    report = {"kind": "observation-only", "doctor": doctor(), "files": inventory()}
    (target / "state.json").write_text(json.dumps(report, indent=2) + "\n")
    emit(report)
    print(f"Evidence: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
