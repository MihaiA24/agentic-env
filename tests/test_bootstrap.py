from __future__ import annotations

import unittest
from unittest.mock import patch

from agentic_env import bootstrap


class BootstrapTests(unittest.TestCase):
    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_default_bootstrap_runs_all_phases_in_order(
        self,
        configure_main,
        doctor_main,
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
                "claude",
                "--skill-agent",
                "codex",
            ]
        )
        configure_main.assert_called_once_with(
            [
                "--yes",
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

    def test_bootstrap_plan_default_has_non_interactive_yes(self) -> None:
        plan = bootstrap._bootstrap_plan(bootstrap._parse([]))
        assert plan is not None

        self.assertIn("--yes", plan[0].argv)
        self.assertIn("--yes", plan[1].argv)
        self.assertIn("--yes", plan[2].argv)

    def test_interactive_bootstrap_plan_lets_the_install_phases_prompt(self) -> None:
        plan = bootstrap._bootstrap_plan(bootstrap._parse(["--interactive"]))
        assert plan is not None

        self.assertEqual(plan[0].argv, [])
        self.assertEqual(plan[1].argv, [])
        self.assertIn("--yes", plan[2].argv)

    @patch("agentic_env.bootstrap.interactive", return_value=False)
    def test_interactive_bootstrap_requires_a_terminal(self, _mock_interactive) -> None:
        self.assertEqual(bootstrap.main(["--interactive"]), 1)

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_dry_run_does_not_execute_phases(
        self,
        configure_main,
        doctor_main,
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
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_rejects_unknown_skill_agent(
        self,
        configure_main,
        doctor_main,
        skills_main,
        agents_main,
    ) -> None:
        result = bootstrap.main(["--skill-agent", "bad-agent"])

        self.assertEqual(result, 1)
        agents_main.assert_not_called()
        skills_main.assert_not_called()
        configure_main.assert_not_called()

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_rejects_unknown_server(
        self,
        configure_main,
        doctor_main,
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
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_skip_install_agents_omits_phase(
        self,
        configure_main,
        doctor_main,
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
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_skip_install_skills_and_configure_omit_those_phases(
        self,
        configure_main,
        doctor_main,
        skills_main,
        agents_main,
    ) -> None:
        agents_main.return_value = 0

        result = bootstrap.main(["--skip-install-skills", "--skip-configure"])

        self.assertEqual(result, 0)
        agents_main.assert_called_once()
        skills_main.assert_not_called()
        configure_main.assert_not_called()

    def test_no_phases_selected_is_noop_success(self) -> None:
        result = bootstrap.main(
            [
                "--skip-install-agents",
                "--skip-install-skills",
                "--skip-configure",
                "--skip-doctor",
            ]
        )

        self.assertEqual(result, 0)

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_rejects_empty_skill_profile(
        self,
        configure_main,
        doctor_main,
        skills_main,
        agents_main,
    ) -> None:
        agents_main.return_value = 0
        skills_main.return_value = 0
        configure_main.return_value = 0

        result = bootstrap.main(["--skill-profile", ""])

        self.assertEqual(result, 1)
        agents_main.assert_not_called()
        skills_main.assert_not_called()
        configure_main.assert_not_called()

    def test_bootstrap_plan_marks_requested_and_skipped_phases(self) -> None:
        args = bootstrap._parse(["--skip-install-agents"])
        plan = bootstrap._bootstrap_plan(args)

        assert plan is not None
        self.assertEqual([phase.requested for phase in plan], [False, True, True, True])
        self.assertIsNone(plan[1].skipped_reason)
        self.assertIsNotNone(plan[0].skipped_reason)
        self.assertIn("--skip-install-agents", plan[0].skipped_reason)


if __name__ == "__main__":
    unittest.main()
