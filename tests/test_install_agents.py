from __future__ import annotations

import unittest
from unittest.mock import patch

from agentic_env import install_agents


@patch("agentic_env.install_agents.warn")
@patch("agentic_env.install_agents.cmd_exists", return_value=True)
@patch("agentic_env.install_agents.cmd_version_matches", return_value=False)
class InstallHermesTests(unittest.TestCase):
    @patch("agentic_env.install_agents.run_remote_script")
    @patch("agentic_env.install_agents._hermes_checkout_ahead_of_pin", return_value=True)
    def test_checkout_ahead_of_pin_is_tolerated_without_reinstall(
        self, ahead, remote_script, version_matches, exists, warn
    ) -> None:
        self.assertTrue(install_agents._install_hermes(True))
        remote_script.assert_not_called()
        self.assertIn("drift above the pin is tolerated", warn.call_args.args[0])

    @patch("agentic_env.install_agents.run_remote_script", return_value=True)
    @patch("agentic_env.install_agents._hermes_checkout_ahead_of_pin", return_value=False)
    def test_checkout_behind_pin_converges_and_fails_on_mismatch(
        self, ahead, remote_script, version_matches, exists, warn
    ) -> None:
        self.assertFalse(install_agents._install_hermes(True))
        remote_script.assert_called_once()
        self.assertIn(
            "--commit", remote_script.call_args.kwargs["interpreter_args"]
        )


if __name__ == "__main__":
    unittest.main()
