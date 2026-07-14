from __future__ import annotations

import unittest
from unittest.mock import patch

from agentic_env import bootstrap


class BootstrapTests(unittest.TestCase):
    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_default_bootstrap_runs_all_phases_in_order(
        self,
        configure_main,
        skills_main,
        agents_main,
    ) -> None:
        agents_main.return_value = 0
        skills_main.return_value = 0
        configure_main.return_value = 0

        result = bootstrap.main([])

        self.assertEqual(result, 0)
        agents_main.assert_called_once_with(["--all", "--yes"])
        skills_main.assert_called_once_with(
            [
                "--all-mcps",
                "--yes",
                "--skill-profile",
                "default",
                "--skill-agent",
                "hermes",
                "--skill-agent",
                "ohmipy",
                "--skill-agent",
                "claude",
                "--skill-agent",
                "codex",
            ]
        )
        configure_main.assert_called_once_with(
            [
                "--yes",
                "--server",
                "lean-ctx",
                "--server",
                "codebase-memory-mcp",
                "--server",
                "agentmemory",
                "--agent",
                "hermes",
                "--agent",
                "omp",
            ]
        )

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_dry_run_does_not_execute_phases(
        self,
        configure_main,
        skills_main,
        agents_main,
    ) -> None:
        result = bootstrap.main(["--dry-run"])

        self.assertEqual(result, 0)
        agents_main.assert_not_called()
        skills_main.assert_not_called()
        configure_main.assert_not_called()

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_skip_install_agents_omits_phase(
        self,
        configure_main,
        skills_main,
        agents_main,
    ) -> None:
        agents_main.return_value = 0
        skills_main.return_value = 0
        configure_main.return_value = 0

        result = bootstrap.main(["--skip-install-agents"])

        self.assertEqual(result, 0)
        agents_main.assert_not_called()
        skills_main.assert_called_once()
        configure_main.assert_called_once()

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_rejects_unknown_server(
        self,
        configure_main,
        skills_main,
        agents_main,
    ) -> None:
        agents_main.return_value = 0
        skills_main.return_value = 0
        configure_main.return_value = 0

        result = bootstrap.main(["--server", "not-a-server"])

        self.assertEqual(result, 1)
        agents_main.assert_not_called()
        skills_main.assert_not_called()
        configure_main.assert_not_called()

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_no_phases_selected_is_noop_success(
        self,
        configure_main,
        skills_main,
        agents_main,
    ) -> None:
        result = bootstrap.main(
            [
                "--skip-install-agents",
                "--skip-install-skills",
                "--skip-configure",
            ]
        )

        self.assertEqual(result, 0)
        agents_main.assert_not_called()
        skills_main.assert_not_called()
        configure_main.assert_not_called()


if __name__ == "__main__":
    unittest.main()
