from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[1] / "clean-acceptance.sh"


@unittest.skipUnless(os.name == "posix" and os.geteuid() != 0, "acceptance needs a non-root POSIX user")
class CleanAcceptanceTests(unittest.TestCase):
    def test_transport_survives_isolation_without_inheriting_host_git_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script_dir = root / "checkout" / "agentic-env"
            script_dir.mkdir(parents=True)
            shutil.copyfile(WRAPPER, script_dir / WRAPPER.name)
            (script_dir / "docker-smoke-test.sh").write_text(
                'set -eu\n'
                'printf "transport=%s\\n" "$(git config --get http.version)"\n'
                'if git config --get agentic.host-only; then exit 1; fi\n'
                'test "$GIT_CONFIG_NOSYSTEM" = 1\n'
                'test "$GIT_CONFIG_GLOBAL" = /dev/null\n',
                encoding="utf-8",
            )
            host_home = root / "host"
            host_home.mkdir()
            (host_home / ".gitconfig").write_text(
                "[http]\nversion = HTTP/2\n[agentic]\nhost-only = true\n",
                encoding="utf-8",
            )
            smoke_home = root / "isolated"
            env = {
                **os.environ,
                "HOME": str(host_home),
                "AGENTIC_SMOKE_HOME": str(smoke_home),
                "AGENTIC_SMOKE_REVISION": "fixture",
                "AGENTIC_PREREQ_PATH": os.defpath,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "agentic.host-only",
                "GIT_CONFIG_VALUE_0": "true",
            }
            for mode in ("0", "1"):
                with self.subTest(skip_install=mode):
                    result = subprocess.run(
                        ["/bin/sh", str(script_dir / WRAPPER.name)],
                        env={**env, "SKIP_INSTALL": mode},
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("transport=HTTP/1.1\n", result.stdout)
            self.assertEqual(
                (host_home / ".gitconfig").read_text(encoding="utf-8"),
                "[http]\nversion = HTTP/2\n[agentic]\nhost-only = true\n",
            )
