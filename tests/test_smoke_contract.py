from __future__ import annotations

from pathlib import Path
import unittest


class SmokeContractTests(unittest.TestCase):
    @classmethod
    def _smoke_script(cls) -> str:
        return (
            Path(__file__).resolve().parents[0]
            / ".."
            / "docker-smoke-test.sh"
        ).resolve().read_text(encoding="utf-8")

    @classmethod
    def _readme_path(cls) -> Path:
        return (Path(__file__).resolve().parents[1] / "README.md").resolve()

    def test_smoke_script_keeps_required_binary_checks(self) -> None:
        script = self._smoke_script()
        for command in (
            "agentic-bootstrap",
            "agentic-install-agents",
            "agentic-install-skills-mcps",
            "agentic-configure-agent-mcps",
            "agentic-update-stack",
            "agentic-stack-doctor",
            "hermes",
            "omp",
            "codex",
            "claude",
            "codebase-memory-mcp",
            "agentmemory",
        ):
            self.assertIn(f"require_command {command}", script)
        self.assertNotIn("require_command lean-ctx", script)

    def test_smoke_script_runs_doctor_and_pins_hermes_artifacts(self) -> None:
        script = self._smoke_script()

        # OMP wiring (mcp.json gate, config.yml contract, hooks, roster) is the doctor's job.
        self.assertIn('run_cmd "agentic-stack-doctor"', script)
        self.assertIn('run_cmd "uv run --script stack-doctor.py --help"', script)
        self.assertIn("agentic_env.stack_doctor", script)
        self.assertIn(
            "for (const name of ['codebase-memory-mcp', 'agentmemory']) {",
            script,
        )
        self.assertNotIn("lean-ctx", script)  # doctor owns that check (hermes warn, OMP fail)
        self.assertIn(
            "if (!/^\\s*provider:\\s*agentmemory\\s*$/m.test(text)) {",
            script,
        )
        self.assertNotIn("path.join(home, '.omp', 'agent', 'mcp.json')", script)

    def test_readme_smoke_contract_stays_explicit(self) -> None:
        readme = self._readme_path().read_text(encoding="utf-8")

        self.assertIn("Current smoke contract", readme)
        self.assertIn("agentic-configure-agent-mcps", readme)
        self.assertIn("agentic-stack-doctor", readme)
        self.assertIn("codebase-memory-mcp", readme)
        self.assertIn("agentmemory", readme)
        self.assertIn("agentic-bootstrap", readme)
        self.assertNotIn("lean-ctx doctor", readme)
        # bootstrap takes no --yes; it forwards --yes to phases internally
        self.assertNotIn("agentic-bootstrap --yes", readme)


if __name__ == "__main__":
    unittest.main()
