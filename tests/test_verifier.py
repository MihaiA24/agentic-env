from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


CONTROL = Path(__file__).resolve().parents[1] / ".agents/skills/verify-agentic-env/verifier/control.py"

# A real child writes to the configured storage boundaries without installing
# anything. These tests exercise wrapper isolation, not uv or product behavior.
_STORAGE_PROBE = """\
import os
from pathlib import Path
for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME",
            "UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_TOOL_DIR", "UV_TOOL_BIN_DIR",
            "NPM_CONFIG_CACHE", "NPM_CONFIG_PREFIX"):
    directory = Path(os.environ[key])
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "child-wrote.txt").write_text("child data\\n")
Path(os.environ["NPM_CONFIG_USERCONFIG"]).write_text("child config\\n")
python = Path(os.environ["UV_PROJECT_ENVIRONMENT"]) / "bin/python"
python.parent.mkdir(parents=True, exist_ok=True)
python.write_text("fixture interpreter\\n")
"""


class VerifierSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name).resolve()
        self.root = self.temporary / "checkout"
        fake_control = self.root / CONTROL.relative_to(CONTROL.parents[4])
        fake_control.parent.mkdir(parents=True)
        shutil.copyfile(CONTROL, fake_control)
        spec = importlib.util.spec_from_file_location("verifier_control", fake_control)
        assert spec is not None and spec.loader is not None
        self.control = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.control)
        self.base = self.control.BASE
        self.data = self.control.DATA
        self.evidence = self.control.EVIDENCE

        (self.root / "agentic_env").mkdir()
        self.source = self.root / "agentic_env/example.py"
        self.source.write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
        (self.root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        binaries = self.temporary / "bin"
        binaries.mkdir()
        uv = binaries / "uv"
        uv.write_text(f"#!{sys.executable}\n" + _STORAGE_PROBE, encoding="utf-8")
        uv.chmod(0o755)
        environment = patch.dict(os.environ, {
            "PATH": str(binaries) + os.pathsep + os.environ.get("PATH", os.defpath),
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.seed_current_workspace()

    def seed_current_workspace(self) -> None:
        self.evidence.mkdir(parents=True, exist_ok=True)
        (self.data / "home").mkdir(parents=True, exist_ok=True)
        python = self.data / "venv/bin/python"
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("fixture interpreter\n", encoding="utf-8")
        (self.base / "owner.json").write_text(json.dumps({
            "checkout": str(self.root), "profile": self.control.PROFILE,
        }), encoding="utf-8")
        (self.data / "build.json").write_text(json.dumps({
            "fingerprint": self.control.fingerprint(),
        }), encoding="utf-8")

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = self.control.main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_actual_source_edit_stales_build_and_refuses_driver(self) -> None:
        code, stdout, _ = self.invoke("doctor")
        self.assertEqual(code, 0)
        previous = json.loads(stdout)
        self.assertTrue(previous["ready"])

        self.source.write_text("VALUE = 2\n", encoding="utf-8")
        code, stdout, _ = self.invoke("doctor")
        report = json.loads(stdout)
        self.assertEqual(code, 1)
        self.assertEqual(report["build"], "stale")
        self.assertFalse(report["ready"])
        self.assertNotEqual(report["fingerprint"], previous["fingerprint"])
        self.assertEqual(self.invoke("drive", "copy")[0], 1)
        self.assertFalse((self.data / "home/child-wrote.txt").exists())
        self.assertEqual(list(self.evidence.iterdir()), [])

    def test_foreign_ownership_refuses_launch_drive_and_cleanup(self) -> None:
        owner_path = self.base / "owner.json"
        foreign_record = json.dumps({
            "checkout": str(self.temporary / "other-checkout"), "profile": self.control.PROFILE,
        })
        owner_path.write_text(foreign_record, encoding="utf-8")
        keep = self.data / "keep.txt"
        keep.write_bytes(b"foreign workspace\n")
        evidence = self.evidence / "keep.txt"
        evidence.write_bytes(b"foreign evidence\n")
        cache = self.base / "cache/keep.txt"
        cache.parent.mkdir()
        cache.write_bytes(b"foreign cache\n")
        for arguments in (("launch",), ("drive", "copy"), ("cleanup", "--dry-run"),
                          ("cleanup",), ("doctor",)):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.invoke(*arguments)[0], 1)
                self.assertEqual(owner_path.read_text(encoding="utf-8"), foreign_record)
                self.assertEqual(keep.read_bytes(), b"foreign workspace\n")
                self.assertEqual(evidence.read_bytes(), b"foreign evidence\n")
                self.assertEqual(cache.read_bytes(), b"foreign cache\n")
                self.assertFalse((self.data / "home/child-wrote.txt").exists())

    def test_symlinked_storage_never_writes_or_deletes_foreign_files(self) -> None:
        # Establish that the child probe really writes on an ordinary launch.
        self.assertEqual(self.invoke("launch")[0], 0)
        self.assertEqual((self.base / "cache/uv/child-wrote.txt").read_text(), "child data\n")
        paths = [self.root / ".verifier", self.base, self.data, self.evidence,
                 self.base / "cache", self.base / "cache/uv", self.base / "cache/npm",
                 self.base / "cache/python", self.data / "home", self.data / "home/.config",
                 self.data / "home/.local/share", self.data / "home/.npmrc", self.data / "skills",
                 self.data / "venv", self.data / "npm", self.data / "tools", self.data / "bin",
                 self.base / "owner.json", self.base / "lock"]
        for index, link in enumerate(paths):
            with self.subTest(path=link.relative_to(self.root)):
                self.seed_current_workspace()
                foreign = self.temporary / f"foreign-{index}"
                foreign.mkdir()
                keep = foreign / "keep.txt"
                content = (self.base / "owner.json").read_bytes() if link.name == "owner.json" else b"keep\n"
                keep.write_bytes(content)
                is_file = link.name in ("owner.json", "lock", ".npmrc")
                if link.is_dir():
                    shutil.rmtree(link)
                elif link.exists():
                    link.unlink()
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(keep if is_file else foreign, target_is_directory=not is_file)
                try:
                    for arguments in (("launch",), ("drive", "copy"), ("cleanup",)):
                        with self.subTest(arguments=arguments):
                            self.assertEqual(self.invoke(*arguments)[0], 1)
                            self.assertEqual(keep.read_bytes(), content)
                            self.assertEqual(list(foreign.iterdir()), [keep])
                finally:
                    link.unlink()

    def test_runtime_executable_links_allow_inspection_and_safe_cleanup(self) -> None:
        executable = self.temporary / "external-executable"
        executable.write_bytes(b"external executable\n")
        link = self.data / "home/.codex/tmp/run/apply_patch"
        link.parent.mkdir(parents=True)
        link.symlink_to(executable)
        self.assertEqual(self.invoke("doctor")[0], 0)
        self.assertEqual(self.invoke("drive", "inspect")[0], 0)
        observation = next(self.evidence.glob("*/state.json"))
        self.assertEqual(json.loads(observation.read_text())["files"][
            "home/.codex/tmp/run/apply_patch"
        ], {"symlink": str(executable)})
        self.assertEqual(self.invoke("cleanup", "--dry-run")[0], 0)
        self.assertTrue(link.is_symlink())
        self.assertEqual(self.invoke("cleanup")[0], 0)
        self.assertFalse(self.data.exists())
        self.assertEqual(executable.read_bytes(), b"external executable\n")
        self.assertTrue(observation.is_file())

    def test_cleanup_dry_run_preserves_files_and_cleanup_retains_real_evidence(self) -> None:
        keep = self.data / "skills/keep.txt"
        keep.parent.mkdir()
        keep.write_bytes(b"workspace content\n")
        cache = self.base / "cache/uv/cache.bin"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"cache content\n")
        self.assertEqual(self.invoke("drive", "inspect")[0], 0)
        state = next(self.evidence.glob("*/state.json"))
        evidence_bytes = state.read_bytes()

        self.assertEqual(self.invoke("cleanup", "--dry-run")[0], 0)
        self.assertEqual(keep.read_bytes(), b"workspace content\n")
        self.assertEqual(cache.read_bytes(), b"cache content\n")
        self.assertEqual(state.read_bytes(), evidence_bytes)
        self.assertEqual(self.invoke("cleanup")[0], 0)
        self.assertFalse(self.data.exists())
        self.assertFalse((self.base / "cache").exists())
        self.assertEqual(state.read_bytes(), evidence_bytes)
        self.assertEqual(self.invoke("logs", "--run", state.parent.name)[0], 0)

    def test_concurrent_lock_refuses_drive_and_cleanup_without_mutation(self) -> None:
        keep = self.data / "keep.txt"
        keep.write_bytes(b"busy workspace\n")
        lock = self.base / "lock"
        holder_code = (
            "import fcntl, os, sys\n"
            "with open(sys.argv[1], 'a+') as handle:\n"
            "    fcntl.flock(handle, fcntl.LOCK_EX)\n"
            "    handle.write(str(os.getpid())); handle.flush()\n"
            "    print('ready', flush=True)\n"
            "    sys.stdin.read()\n"
        )
        with subprocess.Popen([sys.executable, "-I", "-c", holder_code, str(lock)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as holder:
            try:
                ready, _, _ = select.select([holder.stdout], [], [], 5)
                self.assertTrue(ready, "lock holder did not become ready")
                self.assertEqual(holder.stdout.readline(), "ready\n")
                for arguments in (("drive", "copy"), ("cleanup",)):
                    with self.subTest(arguments=arguments):
                        self.assertEqual(self.invoke(*arguments)[0], 1)
                        self.assertEqual(keep.read_bytes(), b"busy workspace\n")
                        self.assertEqual(lock.read_text(), str(holder.pid))
                        self.assertEqual(list(self.evidence.iterdir()), [])
                        self.assertFalse((self.data / "home/child-wrote.txt").exists())
            finally:
                holder.communicate(input="", timeout=5)
        self.assertEqual(self.invoke("drive", "inspect")[0], 0)

    @unittest.skipUnless(shutil.which("lsof"), "listener ownership requires lsof")
    def test_doctor_reports_and_refuses_actual_foreign_listener(self) -> None:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            code, stdout, _ = self.invoke("doctor", "--port", str(port))
            report = json.loads(stdout)
            self.assertEqual(code, 1)
            self.assertFalse(report["ready"])
            self.assertEqual(report["build"], "current")
            owners = report["ports"][0]["owners"]
            mine = [owner for owner in owners if owner["pid"] == os.getpid()]
            self.assertTrue(mine, "doctor omitted the listening process")
            self.assertFalse(mine[0]["owned"])
            self.assertTrue(mine[0]["command"])


if __name__ == "__main__":
    unittest.main()
