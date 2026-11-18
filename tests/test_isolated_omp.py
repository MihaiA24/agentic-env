from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from agentic_env import isolated_omp


class IsolatedOmpTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.instance = self.root / "instance"

    def seed_instance(self) -> None:
        for name in ("bin", "broker", "runtime"):
            (self.instance / name).mkdir(parents=True)
        for name in ("policy.json", "bin/omp", "bin/nono"):
            (self.instance / name).write_text("trusted content")
        (self.instance / "manifest.json").write_text(json.dumps({
            "project": str(self.project),
            "sha256": {name: isolated_omp._digest(self.instance / name)
                       for name in ("policy.json", "bin/omp", "bin/nono")},
        }))

    def test_changed_policy_or_executable_never_launches(self) -> None:
        self.seed_instance()
        for name in ("policy.json", "bin/nono", "bin/omp"):
            with self.subTest(name=name):
                path = self.instance / name
                original = path.read_bytes()
                path.write_text("unreviewed replacement")
                with patch.object(isolated_omp, "_host_check"), patch.object(subprocess, "run") as launch:
                    self.assertEqual(isolated_omp.main(["--instance", str(self.instance), "run"]), 1)
                    launch.assert_not_called()
                path.write_bytes(original)

    def test_manifest_cannot_omit_integrity_checks(self) -> None:
        self.seed_instance()
        manifest = self.instance / "manifest.json"
        data = json.loads(manifest.read_text())
        del data["sha256"]["policy.json"]
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            isolated_omp._load(self.instance)

    def test_instance_symlinks_and_writable_control_paths_are_rejected(self) -> None:
        alias = self.root / "alias"
        alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "canonical"):
            isolated_omp._instance_path(alias / "control")
        for instance, project in ((self.project / "control", self.project),
                                  (self.root, self.project),
                                  (self.instance, Path.home().resolve())):
            with self.subTest(instance=instance, project=project), self.assertRaises(ValueError):
                isolated_omp._guard_paths(instance, project)
        self.seed_instance()
        (self.instance / "runtime").rmdir()
        (self.instance / "runtime").symlink_to(self.project, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "directory changed"):
            isolated_omp._load(self.instance)

    def test_unsupported_host_never_launches(self) -> None:
        with patch.object(isolated_omp.platform, "system", return_value="Darwin"), \
                patch.object(subprocess, "run") as launch:
            self.assertEqual(isolated_omp.main(["--instance", str(self.instance), "run"]), 1)
            launch.assert_not_called()
        with patch.object(isolated_omp.platform, "system", return_value="Linux"), \
                patch.object(isolated_omp.platform, "machine", return_value="x86_64"), \
                patch.object(isolated_omp.ctypes, "CDLL") as libc:
            libc.return_value.syscall.return_value = 5
            with self.assertRaisesRegex(ValueError, "ABI >= 6"):
                isolated_omp._host_check()

    @unittest.skipUnless(os.name == "posix", "Unix supervisor environment")
    def test_supervisor_child_does_not_inherit_operator_authority(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "NONO_ALLOW": "/",
                                     "NONO_CAPABILITY_ELEVATION": "true", "PATH": str(self.project),
                                     "SSH_AUTH_SOCK": "operator-socket", "PYTHONPATH": "poison"}):
            result = subprocess.run(
                [sys.executable, "-I", "-c", "import json, os; print(json.dumps(dict(os.environ)))"],
                env=isolated_omp._environment(self.instance), capture_output=True, text=True, check=True,
            )
        actual = json.loads(result.stdout)
        for key in ("OPENAI_API_KEY", "NONO_ALLOW", "NONO_CAPABILITY_ELEVATION", "SSH_AUTH_SOCK", "PYTHONPATH"):
            self.assertNotIn(key, actual)
        self.assertEqual(actual["PATH"], "/usr/bin:/bin")
        self.assertEqual(actual["HOME"], str(self.instance / "broker"))

    @unittest.skipUnless(sys.platform == "linux", "Linux ELF launch required")
    def test_initialization_refuses_collision_and_rolls_back_enforcement_failure(self) -> None:
        self.instance.mkdir()
        sentinel = self.instance / "operator-state"
        sentinel.write_text("preserve")
        with self.assertRaises(FileExistsError):
            isolated_omp._initialize(self.instance, self.project, "/usr/bin/true")
        self.assertEqual(sentinel.read_text(), "preserve")
        sentinel.unlink()
        self.instance.rmdir()
        archive_path = self.root / "release.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add("/usr/bin/false", arcname="nono")
        with patch.object(isolated_omp, "verified_download", return_value=nullcontext(archive_path)):
            with self.assertRaises(subprocess.CalledProcessError):
                isolated_omp._initialize(self.instance, self.project, "/usr/bin/true")
        self.assertFalse(self.instance.exists())
        self.assertEqual(list(self.project.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
