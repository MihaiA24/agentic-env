from __future__ import annotations

import json
import os
import shutil
import subprocess
import shlex
import sys
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

    def test_explicit_update_uses_only_existing_isolated_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host = root / "host"
            host.mkdir()
            isolated = root / "isolated"
            executable = isolated / ".local" / "bin" / "agentic-update-stack"
            executable.parent.mkdir(parents=True)
            executable.write_text(
                '#!/bin/sh\nset -eu\n'
                'test -z "${AGENTIC_HOST_SECRET:-}"\n'
                'printf updated > "$HOME/update-marker"\n',
                encoding="utf-8",
            )
            executable.chmod(0o755)
            env = {
                **os.environ,
                "HOME": str(host),
                "AGENTIC_HOST_SECRET": "must-not-leak",
                "AGENTIC_PREREQ_PATH": os.defpath,
                "GITHUB_SHA": "fixture",
            }
            for target, expected in ((root / "missing", 1), (host, 1), (isolated, 0)):
                with self.subTest(target=target):
                    result = subprocess.run(
                        ["/bin/sh", str(WRAPPER), "--update"],
                        env={**env, "AGENTIC_SMOKE_HOME": str(target)},
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertFalse((host / "update-marker").exists())
            self.assertEqual((isolated / "update-marker").read_text(), "updated")

    def test_only_download_content_is_shared_between_fresh_acceptance_homes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            checkout = root / "checkout"
            checkout.mkdir()
            shutil.copyfile(WRAPPER, checkout / WRAPPER.name)
            (checkout / "docker-smoke-test.sh").write_text(
                f'exec {shlex.quote(sys.executable)} {shlex.quote(str(checkout / "probe.py"))}\n',
                encoding="utf-8",
            )
            (checkout / "probe.py").write_text(
                "import json, os\n"
                "from pathlib import Path\n"
                "npm = Path(os.environ['npm_config_cache'])\n"
                "assert not (npm / '_npx' / 'executed').exists()\n"
                "assert not (npm / '_logs' / 'prior-log').exists()\n"
                "for name in ('_npx', '_logs'):\n"
                "    (npm / name).mkdir(parents=True, exist_ok=True)\n"
                "    (npm / name / 'executed').write_text('fresh execution')\n"
                "paths = [Path(os.environ['UV_CACHE_DIR']), npm / '_cacache']\n"
                "if 'AGENTIC_ARTIFACT_CACHE' in os.environ:\n"
                "    paths.append(Path(os.environ['AGENTIC_ARTIFACT_CACHE']))\n"
                "    paths.append(Path(os.environ['UV_PYTHON_CACHE_DIR']))\n"
                "warm = [(path / 'download').exists() for path in paths]\n"
                "for path in paths:\n"
                "    path.mkdir(parents=True, exist_ok=True)\n"
                "    (path / 'download').write_text('reusable bytes')\n"
                "print(json.dumps({'env': dict(os.environ), 'warm': warm}))\n",
                encoding="utf-8",
            )
            host = root / "host"
            host.mkdir()
            for cached in (False, True):
                cache = root / "shared-target"
                inherited = {
                    **os.environ,
                    "HOME": str(host),
                    "GITHUB_SHA": "fixture",
                    "SKIP_INSTALL": "0",
                    "AGENTIC_PREREQ_PATH": os.defpath,
                    "AGENTIC_HOST_SECRET": "must-not-leak",
                    "AGENTIC_ARTIFACT_CACHE": str(host / "foreign-artifacts"),
                    "UV_CACHE_DIR": str(host / "foreign-uv"),
                    "UV_PYTHON_CACHE_DIR": str(host / "foreign-python-downloads"),
                    "UV_TOOL_DIR": str(host / "foreign-tools"),
                    "npm_config_cache": str(host / "foreign-npm"),
                    "npm_config_userconfig": str(host / ".npmrc"),
                    "npm_config_//registry.npmjs.org/:_authToken": "must-not-leak",
                    "AGENTIC_ACCEPTANCE_CACHE": str(cache) if cached else "",
                }
                for run in range(2):
                    with self.subTest(cached=cached, run=run):
                        home = root / f"home-{cached}-{run}"
                        result = subprocess.run(
                            ["/bin/sh", str(checkout / WRAPPER.name)],
                            env={**inherited, "AGENTIC_SMOKE_HOME": str(home)},
                            capture_output=True, text=True, timeout=10,
                        )
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        observed = json.loads(result.stdout.splitlines()[-1])
                        environment = observed["env"]
                        self.assertNotIn("AGENTIC_HOST_SECRET", environment)
                        self.assertNotIn("AGENTIC_ACCEPTANCE_CACHE", environment)
                        self.assertNotIn("npm_config_//registry.npmjs.org/:_authToken", environment)
                        self.assertEqual(environment["npm_config_cache"], str(home / ".cache/npm"))
                        self.assertEqual(environment["npm_config_userconfig"], str(home / ".npmrc"))
                        self.assertEqual(environment["UV_TOOL_DIR"], str(home / ".local/share/uv/tools"))
                        self.assertEqual(environment["UV_PYTHON_INSTALL_DIR"], str(home / ".local/share/uv/python"))
                        self.assertEqual(environment["UV_PROJECT_ENVIRONMENT"], str(home / ".venv"))
                        npm_content = home / ".cache/npm/_cacache"
                        if cached:
                            self.assertEqual(environment["AGENTIC_ARTIFACT_CACHE"], str(cache / "artifacts"))
                            self.assertEqual(environment["UV_CACHE_DIR"], str(cache / "uv"))
                            self.assertEqual(environment["UV_PYTHON_CACHE_DIR"], str(cache / "python-downloads"))
                            self.assertTrue(npm_content.is_symlink())
                            self.assertEqual(npm_content.resolve(), cache / "npm/_cacache")
                            self.assertEqual(observed["warm"], [bool(run)] * 4)
                        else:
                            self.assertNotIn("AGENTIC_ARTIFACT_CACHE", environment)
                            self.assertNotIn("UV_PYTHON_CACHE_DIR", environment)
                            self.assertEqual(environment["UV_CACHE_DIR"], str(home / ".cache/uv"))
                            self.assertFalse(npm_content.is_symlink())
                            self.assertEqual(observed["warm"], [False, False])
                        self.assertFalse((home / ".cache/npm/_npx").is_symlink())
                        self.assertFalse((home / ".cache/npm/_logs").is_symlink())
            self.assertEqual(sorted(path.name for path in cache.iterdir()), ["artifacts", "npm", "python-downloads", "uv"])
            self.assertEqual(sorted(path.name for path in (cache / "npm").iterdir()), ["_cacache"])
            self.assertEqual(list(host.iterdir()), [])

    def test_cache_rejects_relative_checkout_and_acceptance_home_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            checkout = root / "checkout"
            checkout.mkdir()
            shutil.copyfile(WRAPPER, checkout / WRAPPER.name)
            (checkout / "docker-smoke-test.sh").write_text("exit 0\n", encoding="utf-8")
            host = root / "host"
            host.mkdir()
            alias = root / "checkout-alias"
            alias.symlink_to(checkout, target_is_directory=True)
            unsafe = root / "symlinked-leaf"
            unsafe.mkdir()
            (unsafe / "uv").symlink_to(checkout, target_is_directory=True)
            foreign = root / "another-worktree"
            subprocess.run(["git", "init", "-q", str(foreign)], check=True, timeout=10)
            for index, cache in enumerate(("relative", "/", str(host), str(checkout / "cache"),
                                            str(alias / "cache"), str(unsafe), str(foreign / "cache"),
                                            "acceptance-home")):
                home = root / f"isolated-{index}"
                selected = str(home / "cache") if cache == "acceptance-home" else cache
                result = subprocess.run(
                    ["/bin/sh", str(checkout / WRAPPER.name)],
                    env={**os.environ, "HOME": str(host), "GITHUB_SHA": "fixture",
                         "SKIP_INSTALL": "0",
                         "AGENTIC_SMOKE_HOME": str(home), "AGENTIC_ACCEPTANCE_CACHE": selected},
                    capture_output=True, text=True, timeout=10,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


@unittest.skipUnless(os.name == "posix", "smoke runner needs a POSIX shell")
class ChecksOnlyTests(unittest.TestCase):
    def test_checks_do_not_update_and_skill_drift_fails_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            binaries = home / "bin"
            binaries.mkdir()
            # External programs are isolated: an accidental update changes a marker.
            command = (
                '#!/bin/sh\n'
                'case "${0##*/}:$*" in\n'
                '  agentic-update-stack:--help) exit 0 ;;\n'
                '  agentic-update-stack:*) printf updated > "$HOME/update-marker" ;;\n'
                '  agentic-skill-drift:"--no-upstream --skill-profile default") exit "$DRIFT_EXIT" ;;\n'
                'esac\n'
                'exit 0\n'
            )
            names = (
                "uv node npm npx curl git bash tar gzip xz unzip ps make cc c++ "
                "hermes omp codex claude codebase-memory-mcp agentmemory "
                "agentic-bootstrap agentic-install-agents agentic-install-skills-mcps "
                "agentic-configure-agent-mcps agentic-update-stack agentic-stack-doctor "
                "agentic-skill-drift"
            )
            for name in names.split():
                path = binaries / name
                path.write_text(command, encoding="utf-8")
                path.chmod(0o755)
            (binaries / "python3").symlink_to(sys.executable)
            env = {
                **os.environ,
                "HOME": str(home),
                "PATH": f"{binaries}{os.pathsep}{os.defpath}",
                "TMPDIR": str(home),
                "SKIP_INSTALL": "1",
            }
            for drift_exit in ("0", "1", "2"):
                with self.subTest(drift_exit=drift_exit):
                    result = subprocess.run(
                        ["/bin/sh", str(WRAPPER.with_name("docker-smoke-test.sh"))],
                        env={**env, "DRIFT_EXIT": drift_exit},
                        capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(
                        result.returncode, 0 if drift_exit == "0" else 1,
                        result.stdout + result.stderr,
                    )
                    self.assertFalse((home / "update-marker").exists())
