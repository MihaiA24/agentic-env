from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentic_env.copy_skills import copy_skill_packages

SCRIPT = Path(__file__).resolve().parents[1] / "agentic_env/copy_skills.py"


class CopySkillTests(unittest.TestCase):
    def copy(self, destination: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", "-S", str(SCRIPT), "--skills-dir", str(destination), *args],
            cwd=destination.parent,
            env={**os.environ, "PATH": ""},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_plain_python_copies_complete_roster_and_reports_remote_exclusions(self) -> None:
        manifest = json.loads(SCRIPT.with_name("skill-packs.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "another harness's skills"
            result = self.copy(destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = set()
            for pack in manifest["packs"]:
                for skill in pack["skills"]:
                    name = skill["name"] if isinstance(skill, dict) else skill
                    if not pack["source"].startswith("./"):
                        self.assertIn(name, result.stdout)
                        continue
                    expected.add(name)
                    source = SCRIPT.parent / pack["source"][2:] / name
                    files = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
                    installed = destination / name
                    self.assertEqual(
                        files,
                        {p.relative_to(installed) for p in installed.rglob("*") if p.is_file()},
                    )
                    for relative in files:
                        self.assertEqual(
                            (installed / relative).read_bytes(), (source / relative).read_bytes()
                        )
                        self.assertEqual(
                            (installed / relative).stat().st_mode & 0o111,
                            (source / relative).stat().st_mode & 0o111,
                        )
            self.assertEqual({p.name for p in destination.iterdir()}, expected)

    def test_filter_and_late_collision_preserve_local_changes_without_partial_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            result = self.copy(destination, "--skill", "writing-for-agents")
            self.assertEqual(result.returncode, 0, result.stderr)
            local_skill = destination / "writing-for-agents/SKILL.md"
            local_skill.write_text("Local edits", encoding="utf-8")
            unrelated = destination / "notes.txt"
            unrelated.write_text("Keep me", encoding="utf-8")
            result = self.copy(destination)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(
                {p.name for p in destination.iterdir()}, {"writing-for-agents", "notes.txt"}
            )
            self.assertEqual(local_skill.read_text(encoding="utf-8"), "Local edits")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "Keep me")

    def test_unavailable_and_empty_selections_never_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            for selection in ("tdd,ponytail", " , "):
                with self.subTest(selection=selection):
                    result = self.copy(destination, "--skill", selection)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(destination.exists())

    def test_copy_into_source_is_rejected_before_recursing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "SKILL.md").write_text("Source skill", encoding="utf-8")
            destination = source / "nested skills"
            with self.assertRaises(ValueError):
                copy_skill_packages([source], destination)
            self.assertFalse(destination.exists())
