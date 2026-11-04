from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import shlex
import tempfile
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "local-ci.sh"


class LocalCiAttestationTests(unittest.TestCase):
    def test_attestation_survives_its_own_commit_and_nothing_else(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)

            def commit(message: str) -> None:
                for args in (["add", "."], ["commit", "-qm", message]):
                    subprocess.run(
                        ["git", "-C", str(repo), "-c", "user.name=Local CI Test",
                         "-c", "user.email=local-ci@example.invalid", "-c", "commit.gpgsign=false",
                         "-c", "core.hooksPath=/dev/null", *args],
                        check=True, capture_output=True, timeout=10,
                    )

            def verify(ref: str = "HEAD") -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["/bin/sh", str(repo / SCRIPT.name), "--verify", ref],
                    capture_output=True, text=True, timeout=10,
                )

            subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=10)
            shutil.copyfile(SCRIPT, repo / SCRIPT.name)
            (repo / "code.txt").write_text("v1\n", encoding="utf-8")
            commit("change")
            unattested = verify()
            self.assertEqual(unattested.returncode, 1)
            match = re.search(r"tree ([0-9a-f]{40,64})", unattested.stderr)
            assert match, unattested.stderr

            (repo / "local-ci.attestation").write_text(f"tree {match[1]}\n", encoding="utf-8")
            commit("attest")
            self.assertEqual(verify().returncode, 0, verify().stderr)

            (repo / "code.txt").write_text("v2\n", encoding="utf-8")
            commit("unchecked change")
            self.assertEqual(verify().returncode, 1)
            self.assertEqual(verify("HEAD~1").returncode, 0)



_GATE_COMMAND = """\
import json
import os
from pathlib import Path
import re
import sys
import time

name = Path(sys.argv[0]).name
args = sys.argv[1:]
state = Path(os.environ["FAKE_GATE_STATE"])
owner = os.environ["FAKE_GATE_OWNER"]

def record(kind, **values):
    event = json.dumps(dict(kind=kind, owner=owner, **values)) + "\\n"
    descriptor = os.open(state / "events.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, event.encode())
    finally:
        os.close(descriptor)

if name == "uname":
    print({"-s": "Darwin", "-m": "arm64", "-r": "fixture"}[args[0]])
elif name == "sw_vers":
    print("15.0")
elif name == "uv":
    cache = Path(os.environ["UV_CACHE_DIR"])
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "download").write_text("cached dependency")
    record("unit", cache=str(cache), python_cache=os.environ["UV_PYTHON_CACHE_DIR"],
           environment=os.environ["UV_PROJECT_ENVIRONMENT"], cwd=os.getcwd())
elif name == "bun":
    record("hooks")
elif name == "native-acceptance":
    home = Path(os.environ["AGENTIC_SMOKE_HOME"])
    mode = "update" if args else "checks" if os.environ.get("SKIP_INSTALL") == "1" else "fresh"
    steps = home / "steps"
    prior = steps.read_text().splitlines() if steps.exists() else []
    assert prior == {"fresh": [], "update": ["fresh"], "checks": ["fresh", "update"]}[mode]
    home.mkdir(parents=True, exist_ok=True)
    steps.write_text("\\n".join([*prior, mode]) + "\\n")
    record("native", mode=mode, home=str(home), cache=os.environ["AGENTIC_ACCEPTANCE_CACHE"])
elif name == "docker":
    if args == ["info"]:
        sys.exit(0)
    if args[0] == "compose":
        project = args[args.index("--project-name") + 1]
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", project), "invalid Compose project name"
        assert os.environ["COMPOSE_PROJECT_NAME"] == project
        assert args[args.index("--env-file") + 1] == "/dev/null"
        assert Path(args[args.index("--file") + 1]).is_file()
        if "down" in args:
            assert "--rmi" not in args
            own = [path for path in (state / "containers").iterdir()
                   if path.name.startswith(project + "-")]
            assert not own
            record("down", project=project)
            sys.exit(0)
        container = args[args.index("--name") + 1]
        volume = args[args.index("--volume") + 1]
        assert args[args.index("--env") + 1] == "AGENTIC_ACCEPTANCE_CACHE=/var/cache/agentic-env"
        service = args[-3]
        # Model Compose's project-scoped build resources, not an installed stack.
        image = project + ("-arch-amd64" if service == "fresh-install-arch" else "-debian-amd64")
        (state / "images" / image).touch(exist_ok=False)
        data = dict(owner=owner, project=project, service=service, modes=[])
        with (state / "containers" / container).open("x") as stream:
            json.dump(data, stream)
        (state / "created" / container).touch(exist_ok=False)
        record("create", container=container, project=project, image=image, service=service, volume=volume)
    elif args[0] == "exec":
        container = args[3] if args[1] == "-e" else args[1]
        path = state / "containers" / container
        data = json.loads(path.read_text())
        assert data["owner"] == owner
        mode = "update" if "--update" in args else "checks" if "SKIP_INSTALL=1" in args else "fresh"
        assert data["modes"] == {"fresh": [], "update": ["fresh"], "checks": ["fresh", "update"]}[mode]
        if mode == "fresh":
            deadline = time.monotonic() + 10
            expected = int(os.environ["FAKE_GATE_CONTAINERS"])
            while len(list((state / "created").iterdir())) < expected:
                assert time.monotonic() < deadline, "acceptance legs were serialized"
                time.sleep(0.01)
            # An Arch container remains alive while another leg is removed.
            if data["service"] == "fresh-install-arch":
                while not list((state / "removed").iterdir()):
                    assert time.monotonic() < deadline, "no independently completed leg"
                    time.sleep(0.01)
        data["modes"].append(mode)
        path.write_text(json.dumps(data))
        record("exec", container=container, mode=mode)
        if data["service"] == os.environ.get("FAKE_GATE_FAIL_SERVICE") and mode == "update":
            sys.exit(7)
    elif args[:2] == ["image", "rm"]:
        project = os.environ["COMPOSE_PROJECT_NAME"]
        assert set(args[2:]) == {project + "-debian-amd64", project + "-arch-amd64"}
        for image in args[2:]:
            (state / "images" / image).unlink()
        record("remove-images", project=project)
    elif args[:2] == ["rm", "-f"]:
        container = args[2]
        path = state / "containers" / container
        record("remove-attempt", container=container, owned=path.exists())
        data = json.loads(path.read_text())
        assert data["owner"] == owner, "removed another gate's container"
        record("remove", container=container, alive=[p.name for p in path.parent.iterdir()])
        (state / "removed" / container).write_text("owned")
        path.unlink()
    else:
        raise AssertionError(args)
else:
    raise AssertionError(name)
"""


@unittest.skipUnless(os.name == "posix", "local gate needs a POSIX shell")
class LocalCiGateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "checkout"
        self.repo.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        command = self.bin / "gate-command"
        command.write_text(f"#!{sys.executable}\n" + _GATE_COMMAND, encoding="utf-8")
        command.chmod(0o755)
        for name in ("docker", "uv", "bun", "uname", "sw_vers", "native-acceptance"):
            (self.bin / name).symlink_to(command)
        self.state = self.root / "state"
        for directory in ("containers", "created", "images", "removed"):
            (self.state / directory).mkdir(parents=True)
        shutil.copyfile(SCRIPT, self.repo / SCRIPT.name)
        shutil.copyfile(SCRIPT.with_name("docker-compose.yml"), self.repo / "docker-compose.yml")
        (self.repo / "clean-acceptance.sh").write_text(
            f"exec {shlex.quote(str(self.bin / 'native-acceptance'))} \"$@\"\n", encoding="utf-8",
        )
        self.host = self.root / "host"
        self.host.mkdir()
        scratch = self.root / "scratch"
        scratch.mkdir()
        self.environment = {
            **os.environ,
            "HOME": str(self.host),
            "TMPDIR": str(scratch),
            "PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', os.defpath)}",
            "AGENTIC_PREREQ_PATH": str(self.bin),
            "XDG_CACHE_HOME": str(self.root / "xdg-cache"),
            "COMPOSE_PROJECT_NAME": "must-not-inherit",
            "SKIP_INSTALL": "1",
            "AGENTIC_ACCEPTANCE_CACHE": str(self.host / "foreign-cache"),
            "FAKE_GATE_STATE": str(self.state),
            "FAKE_GATE_CONTAINERS": "2",
            "FAKE_GATE_OWNER": "single",
        }
        self.environment.pop("AGENTIC_CI_CACHE_ROOT", None)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, timeout=10)
        for arguments in (["add", "."], ["commit", "-qm", "gate fixture"]):
            subprocess.run(
                ["git", "-C", str(self.repo), "-c", "user.name=Local CI Test",
                 "-c", "user.email=local-ci@example.invalid", "-c", "commit.gpgsign=false",
                 "-c", "core.hooksPath=/dev/null", *arguments],
                check=True, capture_output=True, timeout=10,
            )

    def events(self) -> list[dict]:
        return [json.loads(line) for line in (self.state / "events.jsonl").read_text().splitlines()]

    def test_concurrent_gates_own_resources_and_share_only_target_downloads(self) -> None:
        cache = self.root / "external cache"
        cache.mkdir()
        alias = self.root / "cache-alias"
        alias.symlink_to(cache, target_is_directory=True)
        commands = []
        for owner in ("first", "second"):
            process = subprocess.Popen(
                ["/bin/sh", str(self.repo / SCRIPT.name)],
                env={**self.environment, "FAKE_GATE_OWNER": owner, "FAKE_GATE_CONTAINERS": "4",
                     "AGENTIC_CI_CACHE_ROOT": str(alias)},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            commands.append(process)
            self.addCleanup(lambda child=process: child.kill() if child.poll() is None else None)
        for process in commands:
            stdout, stderr = process.communicate(timeout=25)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        events = self.events()
        created = [event for event in events if event["kind"] == "create"]
        removed = [event for event in events if event["kind"] == "remove"]
        self.assertEqual(len(created), 4)
        self.assertEqual(len({event["project"] for event in created}), 2)
        self.assertEqual(len({event["image"] for event in created}), 4)
        self.assertEqual(len({event["container"] for event in created}), 4)
        self.assertEqual({event["container"] for event in created}, {event["container"] for event in removed})
        self.assertTrue(all(event["owned"] for event in events if event["kind"] == "remove-attempt"))
        self.assertEqual({event["project"] for event in events if event["kind"] == "down"},
                         {event["project"] for event in created})
        first_removed = removed[0]
        foreign = {event["container"] for event in created if event["owner"] != first_removed["owner"]}
        self.assertTrue(foreign.intersection(first_removed["alive"]))
        for event in created:
            target = "arch-amd64" if event["service"] == "fresh-install-arch" else "debian-amd64"
            self.assertEqual(event["volume"], f"{cache / target}:/var/cache/agentic-env")
            modes = [item["mode"] for item in events
                     if item["kind"] == "exec" and item["container"] == event["container"]]
            self.assertEqual(modes, ["fresh", "update", "checks"])
            for leaf in ("artifacts", "uv", "python-downloads", "npm/_cacache"):
                self.assertEqual((cache / target / leaf).stat().st_mode & 0o7777, 0o1777)
        native = [event for event in events if event["kind"] == "native"]
        self.assertEqual(len({event["home"] for event in native}), 2)
        self.assertEqual({event["cache"] for event in native}, {str(cache / "macos-arm64")})
        for owner in ("first", "second"):
            self.assertEqual([event["mode"] for event in native if event["owner"] == owner],
                             ["fresh", "update", "checks"])
        units = [event for event in events if event["kind"] == "unit"]
        self.assertEqual({event["cache"] for event in units}, {str(cache / "host-Darwin-arm64/uv")})
        self.assertEqual({event["python_cache"] for event in units},
                         {str(cache / "host-Darwin-arm64/python-downloads")})
        self.assertEqual(len({event["environment"] for event in units}), 2)
        for event in units:
            self.assertFalse(Path(event["cwd"]).exists())
            self.assertFalse(Path(event["environment"]).exists())
        self.assertEqual(list((self.state / "containers").iterdir()), [])
        self.assertEqual(list((self.state / "images").iterdir()), [])
        self.assertTrue((self.repo / "local-ci.attestation").is_file())
        self.assertTrue((cache / "host-Darwin-arm64/uv/download").is_file())

    def test_failed_leg_keeps_failure_and_default_external_cache(self) -> None:
        result = subprocess.run(
            ["/bin/sh", str(self.repo / SCRIPT.name)],
            env={**self.environment, "FAKE_GATE_FAIL_SERVICE": "fresh-install-arch"},
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Failed: arch", result.stderr)
        self.assertFalse((self.repo / "local-ci.attestation").exists())
        events = self.events()
        created = [event for event in events if event["kind"] == "create"]
        self.assertEqual(len(created), 2)
        self.assertEqual(len([event for event in events if event["kind"] == "remove"]), 2)
        self.assertEqual(list((self.state / "containers").iterdir()), [])
        self.assertEqual(list((self.state / "images").iterdir()), [])
        arch = next(event["container"] for event in created if event["service"] == "fresh-install-arch")
        self.assertEqual([event["mode"] for event in events
                          if event["kind"] == "exec" and event["container"] == arch], ["fresh", "update"])
        cache = self.root / "xdg-cache/agentic-env/local-ci"
        self.assertTrue((cache / "host-Darwin-arm64/uv/download").is_file())
        self.assertTrue((cache / "debian-amd64/artifacts").is_dir())

    def test_cache_override_rejects_relative_worktree_and_home_roots(self) -> None:
        alias = self.root / "checkout-alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        unsafe = self.root / "symlinked-leaf"
        (unsafe / "debian-amd64").mkdir(parents=True)
        (unsafe / "debian-amd64/uv").symlink_to(self.repo, target_is_directory=True)
        disposable = self.root / "scratch/agentic-env-local-ci.previous/cache"
        for cache in ("relative", "/", str(self.host), str(self.repo / "cache"),
                      str(alias / "cache"), str(disposable), str(unsafe)):
            with self.subTest(cache=cache):
                result = subprocess.run(
                    ["/bin/sh", str(self.repo / SCRIPT.name)],
                    env={**self.environment, "AGENTIC_CI_CACHE_ROOT": cache},
                    capture_output=True, text=True, timeout=10,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.state / "events.jsonl").exists())
