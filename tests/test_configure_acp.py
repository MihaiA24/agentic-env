from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import configure_acp


class ConfigureAcpTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.omp = self.root / "bin with spaces" / "omp"
        self.omp.parent.mkdir()
        self.omp.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.omp.chmod(0o755)
        self.t3_home = self.root / "custom-t3"
        environment = patch.dict(os.environ, {
            "HOME": str(self.home),
            "T3CODE_HOME": str(self.t3_home),
            "PATH": str(self.omp.parent),
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.pycharm = self.home / ".jetbrains" / "acp.json"
        self.t3 = self.t3_home / "userdata" / "settings.json"
        self.clients = ["--client", "pycharm", "--client", "t3code"]

    def write_json(self, path: Path, data: object) -> bytes:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (json.dumps(data, indent=4) + "\n").encode()
        path.write_bytes(content)
        return content

    def test_native_merge_preserves_settings_and_matching_entry_bytes(self) -> None:
        originals = {
            self.pycharm: self.write_json(self.pycharm, {
                "theme": "dark", "agent_servers": {"Other": {"command": "keep"}},
            }),
            self.t3: self.write_json(self.t3, {
                "editor": {"fontSize": 16},
                "providerInstances": {"other": {"driver": "keep"}},
            }),
        }
        self.assertEqual(configure_acp.main(self.clients), 0)
        pycharm = json.loads(self.pycharm.read_text(encoding="utf-8"))
        t3 = json.loads(self.t3.read_text(encoding="utf-8"))
        self.assertEqual(pycharm["theme"], "dark")
        self.assertEqual(pycharm["agent_servers"]["Other"], {"command": "keep"})
        self.assertEqual(t3["editor"], {"fontSize": 16})
        self.assertEqual(t3["providerInstances"]["other"], {"driver": "keep"})
        self.assertEqual(pycharm["agent_servers"]["Oh My Pi"]["command"], str(self.omp))
        self.assertEqual(t3["providerInstances"]["acpRegistry_omp"]["config"]["commandPath"], str(self.omp))
        pycharm["agent_servers"]["Oh My Pi"]["env"] = {"USER_OPTION": "keep"}
        t3_entry = t3["providerInstances"]["acpRegistry_omp"]
        t3_entry["userOption"] = "keep"
        t3_entry["config"]["env"] = {"USER_OPTION": "keep"}
        matching = {
            self.pycharm: self.write_json(self.pycharm, pycharm),
            self.t3: self.write_json(self.t3, t3),
        }
        for dry_run in ([], ["--dry-run"]):
            self.assertEqual(configure_acp.main(self.clients + dry_run), 0)
            for path, content in matching.items():
                self.assertEqual(path.read_bytes(), content)
                backup = path.with_suffix(path.suffix + ".agentic-env.bak")
                self.assertEqual(backup.read_bytes(), originals[path])

    def test_conflicts_preflight_all_clients_before_writing(self) -> None:
        self.assertEqual(configure_acp.main(self.clients), 0)
        template = json.loads(self.t3.read_text(encoding="utf-8"))
        pycharm_original = self.write_json(self.pycharm, {"userSetting": "keep"})
        for field, value in (("enabled", 1), ("config", {"commandPath": "different-omp"})):
            with self.subTest(field=field):
                data = json.loads(json.dumps(template))
                data["providerInstances"]["acpRegistry_omp"][field] = value
                t3_original = self.write_json(self.t3, data)
                for dry_run in ([], ["--dry-run"]):
                    self.assertEqual(configure_acp.main(self.clients + dry_run), 1)
                    self.assertEqual(self.pycharm.read_bytes(), pycharm_original)
                    self.assertEqual(self.t3.read_bytes(), t3_original)
                self.assertFalse(self.pycharm.with_suffix(".json.agentic-env.bak").exists())
                self.assertFalse(self.t3.with_suffix(".json.agentic-env.bak").exists())

    def test_malformed_selected_config_prevents_other_client_write(self) -> None:
        original = self.write_json(self.pycharm, {"userSetting": "keep"})
        self.t3.parent.mkdir(parents=True)
        for malformed in (
            "{", "[]", '{"providerInstances": null}',
            '{"providerInstances": {"acpRegistry_omp": null}}',
        ):
            with self.subTest(malformed=malformed):
                self.t3.write_text(malformed, encoding="utf-8")
                for dry_run in ([], ["--dry-run"]):
                    self.assertEqual(configure_acp.main(self.clients + dry_run), 1)
                    self.assertEqual(self.pycharm.read_bytes(), original)
                    self.assertEqual(self.t3.read_text(encoding="utf-8"), malformed)
                self.assertFalse(self.pycharm.with_suffix(".json.agentic-env.bak").exists())
        self.assertEqual(configure_acp.main(["--client", "pycharm", "--dry-run"]), 0)
        self.assertEqual(self.pycharm.read_bytes(), original)

    def test_dry_run_creates_nothing_and_export_uses_exact_directory(self) -> None:
        destination = self.root / "exports" / "chosen"
        self.assertEqual(configure_acp.main(self.clients + ["--dry-run"]), 0)
        self.assertEqual(configure_acp.main(self.clients + [
            "--output-dir", str(destination), "--dry-run",
        ]), 0)
        self.assertFalse(self.pycharm.parent.exists())
        self.assertFalse(self.t3_home.exists())
        self.assertFalse(destination.parent.exists())

        self.assertEqual(configure_acp.main(self.clients + [
            "--client", "pycharm", "--output-dir", str(destination),
            "--omp", str(self.omp),
        ]), 0)
        self.assertEqual(sorted(path.name for path in destination.iterdir()), ["pycharm.json", "t3code.json"])
        pycharm = json.loads((destination / "pycharm.json").read_text(encoding="utf-8"))
        t3 = json.loads((destination / "t3code.json").read_text(encoding="utf-8"))
        self.assertEqual(pycharm["agent_servers"]["Oh My Pi"]["command"], str(self.omp))
        self.assertEqual(t3["providerInstances"]["acpRegistry_omp"]["config"]["commandPath"], str(self.omp))
        self.assertFalse(self.pycharm.parent.exists())
        self.assertFalse(self.t3_home.exists())

    def test_export_collisions_preflight_before_any_file_is_written(self) -> None:
        destination = self.root / "exports"
        destination.mkdir()
        collision = destination / "t3code.json"
        for symlink in (False, True):
            with self.subTest(symlink=symlink):
                if symlink:
                    collision.symlink_to(self.root / "missing.json")
                else:
                    collision.write_bytes(b"user-owned contents\n")
                for dry_run in ([], ["--dry-run"]):
                    self.assertEqual(configure_acp.main(self.clients + [
                        "--output-dir", str(destination), *dry_run,
                    ]), 1)
                    self.assertFalse((destination / "pycharm.json").exists())
                    self.assertEqual([path.name for path in destination.iterdir()], ["t3code.json"])
                    if symlink:
                        self.assertTrue(collision.is_symlink())
                        self.assertFalse((self.root / "missing.json").exists())
                    else:
                        self.assertEqual(collision.read_bytes(), b"user-owned contents\n")
                collision.unlink()

    def test_export_never_overwrites_a_file_created_after_preflight(self) -> None:
        destination = self.root / "exports"
        collision = destination / "pycharm.json"
        open_path = Path.open

        def create_competing_file(path: Path, mode: str = "r", *args, **kwargs):
            if path == collision and mode == "x":
                collision.write_bytes(b"created by another process\n")
            return open_path(path, mode, *args, **kwargs)

        with patch.object(Path, "open", new=create_competing_file):
            self.assertEqual(configure_acp.main([
                "--client", "pycharm", "--output-dir", str(destination),
            ]), 1)
        self.assertEqual(collision.read_bytes(), b"created by another process\n")
        self.assertEqual([path.name for path in destination.iterdir()], ["pycharm.json"])

    def test_native_symlink_chain_keeps_links_and_backs_up_target(self) -> None:
        target = self.root / "dotfiles" / "acp.json"
        original = self.write_json(target, {"userOption": "keep"})
        inner = self.root / "inner.json"
        inner.symlink_to(Path("dotfiles") / "acp.json")
        self.pycharm.parent.mkdir(parents=True)
        self.pycharm.symlink_to(inner)
        self.assertEqual(configure_acp.main(["--client", "pycharm"]), 0)
        self.assertTrue(self.pycharm.is_symlink())
        self.assertTrue(inner.is_symlink())
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["userOption"], "keep")
        self.assertEqual(target.with_suffix(".json.agentic-env.bak").read_bytes(), original)
        self.assertEqual([path.name for path in self.pycharm.parent.iterdir()], ["acp.json"])

    def test_dangling_native_link_and_parent_fail_before_other_client_write(self) -> None:
        original = self.write_json(self.pycharm, {"userOption": "keep"})
        self.t3_home.mkdir()
        missing = self.root / "absent" / "settings.json"
        for dangling_parent in (False, True):
            with self.subTest(dangling_parent=dangling_parent):
                if dangling_parent:
                    link = self.t3.parent
                    link.symlink_to(self.root / "missing-directory", target_is_directory=True)
                else:
                    self.t3.parent.mkdir()
                    link = self.t3
                    link.symlink_to(missing)
                for dry_run in ([], ["--dry-run"]):
                    self.assertEqual(configure_acp.main(self.clients + dry_run), 1)
                    self.assertEqual(self.pycharm.read_bytes(), original)
                    self.assertTrue(link.is_symlink())
                    self.assertFalse(missing.parent.exists())
                    self.assertFalse((self.root / "missing-directory").exists())
                    self.assertFalse(self.pycharm.with_suffix(".json.agentic-env.bak").exists())
                link.unlink()
                if not dangling_parent:
                    self.t3.parent.rmdir()

    def test_non_directory_parent_fails_before_other_client_write(self) -> None:
        original = self.write_json(self.pycharm, {"userOption": "keep"})
        self.t3_home.mkdir()
        self.t3.parent.write_bytes(b"not a directory")
        for dry_run in ([], ["--dry-run"]):
            self.assertEqual(configure_acp.main(self.clients + dry_run), 1)
            self.assertEqual(self.pycharm.read_bytes(), original)
            self.assertEqual(self.t3.parent.read_bytes(), b"not a directory")
            self.assertFalse(self.pycharm.with_suffix(".json.agentic-env.bak").exists())

    def test_aliased_native_destinations_are_not_overwritten(self) -> None:
        target = self.root / "shared.json"
        original = self.write_json(target, {"userOption": "keep"})
        for path in (self.pycharm, self.t3):
            path.parent.mkdir(parents=True)
            path.symlink_to(target)
        self.assertEqual(configure_acp.main(self.clients), 1)
        self.assertEqual(target.read_bytes(), original)
        self.assertTrue(self.pycharm.is_symlink())
        self.assertTrue(self.t3.is_symlink())
        self.assertFalse(target.with_suffix(".json.agentic-env.bak").exists())

    def test_missing_executable_prevents_all_writes(self) -> None:
        destination = self.root / "exports"
        self.assertEqual(configure_acp.main(self.clients + ["--omp", "missing-omp"]), 1)
        self.assertEqual(configure_acp.main(self.clients + [
            "--output-dir", str(destination), "--omp", "missing-omp",
        ]), 1)
        self.assertFalse(self.pycharm.parent.exists())
        self.assertFalse(self.t3_home.exists())
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
