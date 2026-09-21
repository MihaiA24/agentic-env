from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "agentic_env/vendored/mattpocock/skills/code-review/scripts/review_snapshot.py"


class ReviewSnapshotTests(unittest.TestCase):
    def test_frozen_wip_includes_selected_changes_without_staging_user_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()

            def git(*args: str) -> bytes:
                return subprocess.check_output(
                    ["git", "-C", str(repo), "-c", "user.name=Snapshot Test",
                     "-c", "user.email=snapshot@example.invalid", "-c", "commit.gpgsign=false",
                     "-c", "core.hooksPath=/dev/null", *args], stderr=subprocess.PIPE,
                )

            def snapshot(destination: Path, *args: str) -> subprocess.CompletedProcess:
                return subprocess.run(
                    [sys.executable, str(SCRIPT), *args, "--output", str(destination)],
                    cwd=repo, capture_output=True, text=True,
                )

            git("init", "-q")
            for name in ("tracked.txt", "deleted.txt", "unrelated.txt"):
                (repo / name).write_text("original\n")
            (repo / ".gitignore").write_text("ignored.txt\n")
            (repo / ".gitattributes").write_text("tracked.txt export-ignore\n")
            git("add", ".")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD").decode().strip()
            (repo / "committed.txt").write_text("committed change\n")
            git("add", "committed.txt")
            git("commit", "-qm", "intended committed change")
            (repo / "staged.txt").write_text("staged change\n")
            git("add", "staged.txt")
            (repo / "tracked.txt").write_text("unstaged change\n")
            (repo / "deleted.txt").unlink()
            (repo / "untracked.txt").write_text("new change\n")
            (repo / "ignored.txt").write_text("private ignored content\n")
            (repo / "unrelated.txt").write_text("unrelated user work\n")
            before = git("status", "--porcelain=v1", "-z")
            index = (repo / ".git/index").read_bytes()
            output = root / "wip"
            selected = ("committed.txt", "staged.txt", "tracked.txt", "deleted.txt", "untracked.txt")
            args = ["--base", base, "--mode", "wip"]
            for path in selected:
                args.extend(["--path", path])
            result = snapshot(output, *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            patch = (output / "diff.patch").read_text()
            for path in selected:
                self.assertIn(path, patch)
            self.assertNotIn("unrelated.txt", patch)
            self.assertEqual((output / "tree/unrelated.txt").read_text(), "original\n")
            self.assertEqual((output / "tree/tracked.txt").read_text(), "unstaged change\n")
            self.assertFalse((output / "tree/deleted.txt").exists())
            self.assertFalse((output / "tree/ignored.txt").exists())
            self.assertEqual(git("status", "--porcelain=v1", "-z"), before)
            self.assertEqual((repo / ".git/index").read_bytes(), index)
            (repo / "tracked.txt").write_text("later edit\n")
            self.assertEqual((output / "tree/tracked.txt").read_text(), "unstaged change\n")
            manifest = json.loads(result.stdout)
            self.assertEqual(manifest["scope"], list(selected))
            checked = subprocess.run([sys.executable, str(SCRIPT), "--verify", str(output)], capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            (output / "tree/tracked.txt").write_text("tampered snapshot\n")
            checked = subprocess.run([sys.executable, str(SCRIPT), "--verify", str(output)], capture_output=True)
            self.assertNotEqual(checked.returncode, 0)
            ref_output = root / "refs"
            result = snapshot(ref_output, "--base", base, "--mode", "refs")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("committed.txt", (ref_output / "diff.patch").read_text())
            self.assertNotIn("staged.txt", (ref_output / "diff.patch").read_text())
            self.assertEqual((ref_output / "tree/tracked.txt").read_text(), "original\n")
            result = snapshot(root / "unscoped", "--base", base)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "unscoped").exists())
            result = snapshot(root / "escape", "--base", base, "--path", "../outside")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "escape").exists())
