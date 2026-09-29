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


class _ReleaseHost(BaseHTTPRequestHandler):
    """Serves `server.routes` ({path: (status, headers, body)}) and logs requests."""

    def _respond(self, with_body: bool) -> None:
        self.server.requests.append((self.command, self.path))
        status, headers, body = self.server.routes.get(self.path, (404, {}, b""))
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        if "Content-Length" not in headers:
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

    def installed_entries(self) -> list[str]:
        # Includes .omp.* temporaries: a failed install must leave none behind.
        return sorted(os.listdir(self.bin)) if self.bin.exists() else []

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

    def test_force_updates_a_compliant_install_but_default_leaves_it_alone(self, warn, ok, info) -> None:
        self.bin.mkdir()
        installed = self.bin / "omp"
        previous = b"#!/bin/sh\necho omp/99.0.0\n"
        installed.write_bytes(previous)
        installed.chmod(0o755)
        replacement = self.publish("99.0.1")

        self.assertTrue(install_agents._install_omp(True))
        self.assertEqual(installed.read_bytes(), previous)
        self.assertEqual(self.server.requests, [])

        self.assertTrue(install_agents._install_omp(True, force=True))
        self.assertEqual(installed.read_bytes(), replacement)

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

    def test_shadowed_or_missing_path_omp_fails_without_touching_it(
        self, warn, ok, info
    ) -> None:
        shadow_dir = self.bin.parent / "shadow"
        shadow_dir.mkdir()
        shadow = shadow_dir / "omp"
        stale = b"#!/bin/sh\necho omp/1.0.0\n"
        shadow.write_bytes(stale)
        shadow.chmod(0o755)
        empty_dir = self.bin.parent / "empty"
        empty_dir.mkdir()
        binary = self.publish()
        for path in (f"{shadow_dir}{os.pathsep}{self.bin}", str(empty_dir)):
            with self.subTest(path=path), patch.dict(os.environ, {"PATH": path}):
                self.assertFalse(install_agents._install_omp(True, force=True))
                self.assertEqual((self.bin / "omp").read_bytes(), binary)
                self.assertEqual(shadow.read_bytes(), stale)

    def test_unverifiable_binary_is_never_installed(self, warn, ok, info) -> None:
        asset_path = f"/releases/download/{self.TAG}/{self.asset}"
        for digest, fetches_asset in (("f" * 64, True), ("not-a-sha256", False)):
            with self.subTest(digest=digest):
                self.publish(digest=digest)
                self.server.requests.clear()
                self.assertFalse(install_agents._install_omp_release())
                self.assertEqual(asset_path in self.paths(), fetches_asset)
                self.assertEqual(self.installed_entries(), [])

    def test_failed_update_preserves_existing_executable(self, warn, ok, info) -> None:
        self.bin.mkdir()
        installed = self.bin / "omp"
        installed.write_bytes(b"previous installation")
        installed.chmod(0o755)
        asset_path = f"/releases/download/{self.TAG}/{self.asset}"
        for failure in ("checksum mismatch", "truncated body", "missing asset"):
            with self.subTest(failure=failure):
                binary = self.publish()
                if failure == "checksum mismatch":
                    self.publish(digest="f" * 64)
                elif failure == "truncated body":
                    headers = {"Content-Length": str(len(binary))}
                    self.server.routes[asset_path] = (200, headers, binary[:-4])
                elif failure == "missing asset":
                    del self.server.routes[asset_path]
                self.assertFalse(install_agents._install_omp_release())
                self.assertEqual(installed.read_bytes(), b"previous installation")
                self.assertEqual(installed.stat().st_mode & 0o777, 0o755)
                self.assertEqual(self.installed_entries(), ["omp"])

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
