from __future__ import annotations

import unittest
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
    @patch("agentic_env.install_agents.run_remote_script", return_value=True)
    @patch("agentic_env.install_agents.cmd_version_at_least", return_value=True)
    def test_force_reinstalls_even_when_above_floor(
        self, at_least, remote_script, exists, warn
    ) -> None:
        self.assertTrue(install_agents._install_omp(True, force=True))
        remote_script.assert_called_once()

        remote_script.reset_mock()
        self.assertTrue(install_agents._install_omp(True))
        remote_script.assert_not_called()


if __name__ == "__main__":
    unittest.main()
