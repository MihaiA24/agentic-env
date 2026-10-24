from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
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
