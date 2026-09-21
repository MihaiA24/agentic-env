from __future__ import annotations

import unittest

from agentic_env.common import version_at_least


class VersionFloorTests(unittest.TestCase):
    def test_reads_the_reported_version_out_of_real_cli_banners(self) -> None:
        for output, floor in (
            ("omp/18.2.2", "18.1.14"),
            ("2.1.263 (Claude Code)", "2.1.258"),
            ("codex-cli 0.154.0", "0.153.4"),
            # Hermes prints a date-like build stamp after the version.
            ("Hermes Agent v0.21.0 (2026.8.31) · upstream 97962358", "0.21.0"),
            ("codebase-memory-mcp 0.9.0", "0.9.0"),
            ("0.9.29", "0.9.29"),
        ):
            with self.subTest(output=output):
                self.assertTrue(version_at_least(output, floor))

    def test_below_floor_fails(self) -> None:
        self.assertFalse(version_at_least("omp/18.1.13", "18.1.14"))
        self.assertFalse(version_at_least("codex-cli 0.99.0", "1.0.0"))
        # Components compare numerically, not lexicographically.
        self.assertFalse(version_at_least("omp/18.9.0", "18.10.0"))

    def test_unparseable_output_fails_closed(self) -> None:
        self.assertFalse(version_at_least("command not found", "1.0.0"))
        self.assertFalse(version_at_least("", "1.0.0"))


if __name__ == "__main__":
    unittest.main()
