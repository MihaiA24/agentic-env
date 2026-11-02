"""Real subprocess/HTTP coverage: immutable downloads, not installed-stack reuse."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRIVE = """
import sys
from agentic_env.common import run_remote_script
ok = run_remote_script(label="fixture", url=sys.argv[1],
    expected_sha256=sys.argv[2], interpreter="/bin/sh",
    immutable=sys.argv[3] == "immutable", timeout_sec=5)
raise SystemExit(0 if ok else 1)
"""


class ArtifactHost(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.requests.append(self.path)
        body = self.server.bodies[self.path]
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.path == self.server.blocked:
            self.server.entered.set()
            if not self.server.release.wait(10):
                return
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


@unittest.skipUnless(os.name == "posix", "artifact locks are for POSIX acceptance")
class ArtifactCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cache = self.root / "host-cache"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ArtifactHost)
        self.server.bodies, self.server.requests = {}, []
        self.server.blocked = None
        self.server.entered, self.server.release = threading.Event(), threading.Event()
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.server.release.set)

    def publish(self, path, version):
        body = f'#!/bin/sh\nprintf "{version}" > "$HOME/installed"\n'.encode()
        self.server.bodies[path] = body
        return body

    def start(self, path, body, home, *, immutable=True):
        target = self.root / home
        target.mkdir()
        process = subprocess.Popen(
            [sys.executable, "-c", DRIVE,
             f"http://127.0.0.1:{self.server.server_port}{path}",
             hashlib.sha256(body).hexdigest(), "immutable" if immutable else "floating"],
            cwd=ROOT,
            env={**os.environ, "HOME": str(target), "AGENTIC_ARTIFACT_CACHE": str(self.cache)},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.addCleanup(self.stop, process)
        return process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    def finish(self, process, expected=0):
        out, err = process.communicate(timeout=15)
        self.assertEqual(process.returncode, expected, out + err)

    def entries(self):
        return [p for p in self.cache.iterdir() if not p.suffix]

    def test_fresh_installs_reuse_versions_and_repair_corruption(self):
        old = self.publish("/v1/install.sh", "v1")
        self.finish(self.start("/v1/install.sh", old, "cold"))
        self.finish(self.start("/v1/install.sh", old, "warm"))
        self.assertEqual(self.server.requests.count("/v1/install.sh"), 1)
        self.assertEqual((self.root / "warm/installed").read_text(), "v1")
        # Installations are independent, even though their download was shared.
        (self.root / "cold/installed").write_text("changed installed state")
        self.assertEqual((self.root / "warm/installed").read_text(), "v1")

        new = self.publish("/v2/install.sh", "v2")
        self.finish(self.start("/v2/install.sh", new, "changed-version"))
        self.assertEqual((self.root / "changed-version/installed").read_text(), "v2")
        self.finish(self.start("/v1/install.sh", old, "older-pr"))
        self.assertEqual(self.server.requests.count("/v1/install.sh"), 1)
        self.assertEqual(len(self.entries()), 2)

        entry = next(p for p in self.entries() if p.read_bytes() == old)
        entry.write_bytes(b"corrupt")
        self.finish(self.start("/v1/install.sh", old, "repaired"))
        self.assertEqual(self.server.requests.count("/v1/install.sh"), 2)
        self.assertEqual(entry.read_bytes(), old)
        self.assertEqual((self.root / "repaired/installed").read_text(), "v1")

    def test_same_url_with_new_checksum_retains_old_identity(self):
        old = self.publish("/release", "old")
        self.finish(self.start("/release", old, "old"))
        new = self.publish("/release", "new")
        self.finish(self.start("/release", new, "new"))
        self.finish(self.start("/release", old, "old-again"))
        self.assertEqual((self.root / "old-again/installed").read_text(), "old")
        self.assertEqual(self.server.requests, ["/release", "/release"])

    def test_bad_or_interrupted_download_never_publishes(self):
        body = self.publish("/installer", "valid")
        self.server.bodies["/installer"] = b"invalid bytes"
        self.finish(self.start("/installer", body, "bad"), expected=1)
        self.assertEqual(self.entries(), [])
        self.assertFalse((self.root / "bad/installed").exists())
        self.assertEqual(list(self.cache.glob("*.partial")), [])

        self.server.bodies["/installer"] = body
        self.server.blocked = "/installer"
        interrupted = self.start("/installer", body, "interrupted")
        self.assertTrue(self.server.entered.wait(5))
        interrupted.kill()
        interrupted.communicate(timeout=10)
        self.assertEqual(self.entries(), [])
        self.server.blocked = None
        self.server.release.set()
        self.finish(self.start("/installer", body, "retry"))
        self.assertEqual((self.root / "retry/installed").read_text(), "valid")
        self.assertEqual(list(self.cache.glob("*.partial")), [])

    def test_per_artifact_lock_deduplicates_without_blocking_other_artifacts(self):
        body = self.publish("/one", "one")
        other = self.publish("/two", "two")
        self.server.blocked = "/one"
        first = self.start("/one", body, "first")
        self.assertTrue(self.server.entered.wait(5))
        second = self.start("/one", body, "second")
        independent = self.start("/two", other, "independent")
        # Different artifacts must complete while the first download is blocked.
        self.finish(independent)
        self.assertIsNone(first.poll())
        self.assertIsNone(second.poll())
        self.server.release.set()
        self.finish(first)
        self.finish(second)
        self.assertEqual(self.server.requests.count("/one"), 1)
        self.assertEqual((self.root / "first/installed").read_text(), "one")
        self.assertEqual((self.root / "second/installed").read_text(), "one")

    def test_floating_script_drift_is_not_hidden_by_cache(self):
        body = self.publish("/latest", "first")
        self.finish(self.start("/latest", body, "first", immutable=False))
        self.publish("/latest", "changed")
        self.finish(self.start("/latest", body, "changed", immutable=False), expected=1)
        self.assertEqual(self.server.requests, ["/latest", "/latest"])
        self.assertFalse(self.cache.exists())
        self.assertFalse((self.root / "changed/installed").exists())
