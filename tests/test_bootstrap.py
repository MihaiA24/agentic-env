from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from agentic_env import bootstrap, common


def _run_json(argv: list[str]) -> tuple[int, dict, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = bootstrap.main([*argv, "--summary-format", "json"])
    # json.loads on the whole stream proves stdout is exactly one JSON document.
    return code, json.loads(stdout.getvalue()), stderr.getvalue()


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

    @patch("agentic_env.bootstrap.install_agents.main")
    @patch("agentic_env.bootstrap.install_skills_mcps.main")
    @patch("agentic_env.bootstrap.stack_doctor.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_json_dry_run_plans_phases_and_explains_skips(
        self,
        configure_main,
        doctor_main,
        skills_main,
        agents_main,
    ) -> None:
        code, summary, stderr = _run_json(["--dry-run", "--skip-doctor"])

        self.assertEqual(code, 0)
        for phase_main in (agents_main, skills_main, configure_main, doctor_main):
            phase_main.assert_not_called()
        self.assertEqual(summary["status"], "partial")
        self.assertTrue(summary["dry_run"])
        phases = {phase["name"]: phase for phase in summary["phases"]}
        self.assertEqual(list(phases), ["install-agents", "install-skills", "configure", "doctor"])
        self.assertEqual(phases["install-agents"]["argv"], ["--all", "--yes"])
        self.assertEqual(
            [(p["requested"], p["executed"], p["skipped"]) for p in summary["phases"]],
            [(True, False, False)] * 3 + [(False, False, True)],
        )
        self.assertIsNone(phases["configure"]["skipped_reason"])
        reason = phases["doctor"]["skipped_reason"]
        self.assertIn("--skip-doctor", reason)
        self.assertIn("omit", reason)
        self.assertIn("install-agents", stderr)

    @patch("agentic_env.bootstrap.install_agents.main", return_value=0)
    @patch("agentic_env.bootstrap.install_skills_mcps.main", return_value=0)
    @patch("agentic_env.bootstrap.stack_doctor.main", return_value=0)
    @patch("agentic_env.bootstrap.configure_agent_mcps.main", return_value=0)
    def test_json_success_reports_every_phase_executed(self, *_phase_mains) -> None:
        code, summary, _stderr = _run_json([])

        self.assertEqual(code, 0)
        self.assertEqual(summary["status"], "ok")
        self.assertFalse(summary["dry_run"])
        for phase in summary["phases"]:
            self.assertTrue(phase["executed"])
            self.assertFalse(phase["skipped"])
            self.assertIsNone(phase["error"])
            self.assertIsInstance(phase["duration_ms"], int)

    @patch("agentic_env.bootstrap.install_agents.main", return_value=3)
    @patch("agentic_env.bootstrap.install_skills_mcps.main", side_effect=RuntimeError("boom"))
    @patch("agentic_env.bootstrap.stack_doctor.main")
    @patch("agentic_env.bootstrap.configure_agent_mcps.main")
    def test_json_reports_failures_and_skips_and_keeps_running_later_phases(
        self,
        configure_main,
        doctor_main,
        _skills_main,
        _agents_main,
    ) -> None:
        def noisy_doctor(_argv: list[str]) -> int:
            print("doctor progress")
            common.ok("doctor console line")
            return 0

        doctor_main.side_effect = noisy_doctor

        code, summary, stderr = _run_json(["--skip-configure"])

        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        phases = {phase["name"]: phase for phase in summary["phases"]}
        self.assertEqual(phases["install-agents"]["error"], "phase returned non-zero")
        self.assertTrue(phases["install-agents"]["executed"])
        self.assertIn("RuntimeError: boom", phases["install-skills"]["error"])
        self.assertTrue(phases["install-skills"]["executed"])
        configure_main.assert_not_called()
        self.assertTrue(phases["configure"]["skipped"])
        self.assertFalse(phases["configure"]["executed"])
        self.assertIn("--skip-configure", phases["configure"]["skipped_reason"])
        self.assertTrue(phases["doctor"]["executed"])
        self.assertIsNone(phases["doctor"]["error"])
        self.assertIn("doctor progress", stderr)
        self.assertIn("doctor console line", stderr)

        # The shared console is not left pointing at stderr after a JSON run.
        after = io.StringIO()
        with redirect_stdout(after):
            common.ok("after json run")
        self.assertIn("after json run", after.getvalue())

    def test_json_redirects_inherited_child_stdout(self) -> None:
        script = """
import subprocess, sys
from agentic_env import bootstrap
def doctor(argv):
    subprocess.run([sys.executable, '-c', 'print("child progress")'], check=True)
    return 7
bootstrap.stack_doctor.main = doctor
raise SystemExit(bootstrap.main([
    '--skip-install-agents', '--skip-install-skills', '--skip-configure',
    '--verbose', '--summary-format', 'json',
]))
"""
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "failed")
        self.assertIn("child progress", result.stderr)


if __name__ == "__main__":
    unittest.main()
