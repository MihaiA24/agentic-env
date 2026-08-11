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
            "hermes",
            "omp",
            "codex",
            "claude",
            "lean-ctx",
            "codebase-memory-mcp",
            "agentmemory",
        ):
            self.assertIn(f"require_command {command}", script)

    def test_smoke_script_keeps_config_artifact_assertions(self) -> None:
        script = self._smoke_script()

        self.assertIn(
            "for (const name of ['lean-ctx', 'codebase-memory-mcp', 'agentmemory']) {",
            script,
        )
        self.assertIn(
            "if (!/^\\s*provider:\\s*agentmemory\\s*$/m.test(text)) {",
            script,
        )
        self.assertNotIn("const settings = path.join(home, '.pi', 'agent', 'settings.json');", script)
        self.assertNotIn("extensions/agentmemory", script)
        self.assertNotIn("missing OMP agentmemory extension index.ts", script)
        self.assertIn("for (const mcpPath of [", script)
        self.assertIn("path.join(home, '.omp', 'agent', 'mcp.json'),", script)
        self.assertIn("path.join(home, '.pi', 'agent', 'mcp.json'),", script)
        self.assertIn("if (!mcp.mcpServers['codebase-memory-mcp']) {", script)
        self.assertIn("for (const name of ['agentmemory', 'lean-ctx']) {", script)
        self.assertIn("if (mcp.mcpServers[name]) {", script)
        self.assertIn("path.join(home, '.hermes', 'skills'), ['lean-ctx', 'codebase-memory-mcp', 'agentmemory', 'ponytail']", script)
        self.assertIn("path.join(home, '.omp', 'agent', 'skills'), ['codebase-memory-mcp', 'ponytail']", script)
        self.assertIn("path.join(home, '.pi', 'agent', 'skills'), ['codebase-memory-mcp', 'ponytail']", script)

    def test_readme_smoke_contract_stays_explicit(self) -> None:
        readme = self._readme_path().read_text(encoding="utf-8")

        self.assertIn("Current smoke contract", readme)
        self.assertIn("agentic-configure-agent-mcps", readme)
        self.assertIn("lean-ctx", readme)
        self.assertIn("codebase-memory-mcp", readme)
        self.assertIn("agentmemory", readme)
        self.assertIn("agentic-bootstrap --yes", readme)


if __name__ == "__main__":
    unittest.main()
