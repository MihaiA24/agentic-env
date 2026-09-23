from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from agentic_env import install_agents


@patch("agentic_env.install_agents.warn")
@patch("agentic_env.install_agents.cmd_exists", return_value=True)
class InstallHermesTests(unittest.TestCase):
    @patch("agentic_env.install_agents.run_remote_script")
    @patch("agentic_env.install_agents.cmd_version_at_least", return_value=True)
    def test_version_at_or_above_floor_is_left_alone(
        self, at_least, remote_script, exists, warn
    ) -> None:
        self.assertTrue(install_agents._install_hermes(True))
        remote_script.assert_not_called()

    @patch("agentic_env.install_agents.run_remote_script", return_value=True)
    @patch("agentic_env.install_agents.cmd_version_at_least", return_value=False)
    def test_version_below_floor_converges_and_fails_when_still_below(
        self, at_least, remote_script, exists, warn
    ) -> None:
        self.assertFalse(install_agents._install_hermes(True))
        remote_script.assert_called_once()
        self.assertIn("--commit", remote_script.call_args.kwargs["interpreter_args"])


@patch("agentic_env.install_agents.warn")
@patch("agentic_env.install_agents.cmd_exists", return_value=True)
class InstallForceTests(unittest.TestCase):
    @patch("agentic_env.install_agents._install_omp_release", return_value=True)
    @patch("agentic_env.install_agents.cmd_version_at_least", return_value=True)
    def test_force_reinstalls_even_when_above_floor(
        self, at_least, release, exists, warn
    ) -> None:
        self.assertTrue(install_agents._install_omp(True, force=True))
        release.assert_called_once()

        release.reset_mock()
        self.assertTrue(install_agents._install_omp(True))
        release.assert_not_called()


class _ReleaseHost(BaseHTTPRequestHandler):
    """Serves `server.routes` ({path: (status, headers, body)}) and logs requests."""

    def _respond(self, with_body: bool) -> None:
        self.server.requests.append((self.command, self.path))
        status, headers, body = self.server.routes.get(self.path, (404, {}, b""))
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if with_body:
            self.wfile.write(body)

    def do_HEAD(self) -> None:
        self._respond(False)

    def do_GET(self) -> None:
        self._respond(True)

    def log_message(self, *args: object) -> None:
        pass


@patch("agentic_env.install_agents.info")
@patch("agentic_env.install_agents.ok")
@patch("agentic_env.install_agents.warn")
class InstallOmpReleaseTests(unittest.TestCase):
    """Drives the real HTTP boundary against a local stand-in for github.com."""

    TAG = "v99.0.0"

    def setUp(self) -> None:
        self.asset = install_agents._omp_asset()
        if self.asset is None:
            self.skipTest("host platform has no OMP release asset")
        server = ThreadingHTTPServer(("127.0.0.1", 0), _ReleaseHost)
        server.routes, server.requests = {}, []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        self.server = server
        self.origin = f"http://127.0.0.1:{server.server_port}"
        self.base = f"{self.origin}/releases"

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.bin = Path(temporary.name) / "bin"
        for patcher in (
            patch.object(install_agents, "OMP_RELEASES_URL", self.base),
            patch.dict(
                os.environ,
                {
                    "PI_INSTALL_DIR": str(self.bin),
                    "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                },
            ),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def publish(self, version: str = "99.0.0", *, digest: str | None = None) -> bytes:
        binary = f"#!/bin/sh\necho omp/{version}\n".encode()
        sums = (
            f"{'0' * 64}  omp-windows-x64.exe\n"
            f"{digest or hashlib.sha256(binary).hexdigest()}  {self.asset}\n"
        ).encode()
        download = f"/releases/download/{self.TAG}"
        self.server.routes.update(
            {
                "/releases/latest": (302, {"Location": f"{self.base}/tag/{self.TAG}"}, b""),
                f"/releases/tag/{self.TAG}": (200, {}, b""),
                f"{download}/SHA256SUMS.txt": (200, {}, sums),
                f"{download}/{self.asset}": (200, {}, binary),
            }
        )
        return binary

    def paths(self) -> list[str]:
        # Python 3.12 follows the redirect with GET, 3.13+ keeps HEAD.
        return [path for _, path in self.server.requests]

    def test_installs_latest_tag_verified_against_published_checksums(
        self, warn, ok, info
    ) -> None:
        binary = self.publish()
        self.assertTrue(install_agents._install_omp(True, force=True))

        installed = self.bin / "omp"
        self.assertEqual(installed.read_bytes(), binary)
        self.assertTrue(installed.stat().st_mode & 0o111)
        # The redirect alone names the release: no REST lookup, and the
        # resolved tag is the one every asset is fetched from.
        self.assertEqual(
            self.paths(),
            [
                "/releases/latest",
                f"/releases/tag/{self.TAG}",
                f"/releases/download/{self.TAG}/SHA256SUMS.txt",
                f"/releases/download/{self.TAG}/{self.asset}",
            ],
        )

    def test_below_floor_update_preserves_existing_executable(self, warn, ok, info) -> None:
        self.bin.mkdir()
        installed = self.bin / "omp"
        previous = b"#!/bin/sh\necho omp/99.0.0\n"
        installed.write_bytes(previous)
        installed.chmod(0o755)
        self.publish("1.0.0")
        self.assertFalse(install_agents._install_omp(True, force=True))
        self.assertEqual(installed.read_bytes(), previous)
        self.assertEqual(sorted(p.name for p in self.bin.iterdir()), ["omp"])

    def test_unverifiable_binary_is_never_installed(self, warn, ok, info) -> None:
        for digest in ("f" * 64, "not-a-sha256"):
            with self.subTest(digest=digest):
                self.publish(digest=digest)
                self.assertFalse(install_agents._install_omp_release())
                self.assertFalse(self.bin.exists())

    def test_failed_update_preserves_existing_executable(self, warn, ok, info) -> None:
        self.bin.mkdir()
        installed = self.bin / "omp"
        installed.write_bytes(b"previous installation")
        installed.chmod(0o755)
        self.publish(digest="f" * 64)
        self.assertFalse(install_agents._install_omp_release())
        self.assertEqual(installed.read_bytes(), b"previous installation")
        self.assertEqual(installed.stat().st_mode & 0o777, 0o755)

    def test_rejects_redirect_that_is_not_a_stable_release_tag(
        self, warn, ok, info
    ) -> None:
        for target in (
            f"{self.base}/tag/{self.TAG}-rc.1",
            f"{self.base}/tag/{self.TAG}/extra",
            self.base,
            f"{self.origin}/fork/releases/tag/{self.TAG}",
        ):
            with self.subTest(target=target):
                self.publish()
                path = target.removeprefix(self.origin) or "/"
                self.server.routes[path] = (200, {}, b"")
                self.server.routes["/releases/latest"] = (302, {"Location": target}, b"")
                self.server.requests.clear()
                self.assertFalse(install_agents._install_omp_release())
                self.assertFalse(any("/download/" in path for path in self.paths()))
                self.assertFalse(self.bin.exists())

    def test_lookup_failure_fails_without_fallback(self, warn, ok, info) -> None:
        self.publish()
        self.server.routes["/releases/latest"] = (403, {}, b"")
        self.assertFalse(install_agents._install_omp_release())
        self.assertEqual(self.server.requests, [("HEAD", "/releases/latest")])
        self.assertFalse(self.bin.exists())


if __name__ == "__main__":
    unittest.main()
