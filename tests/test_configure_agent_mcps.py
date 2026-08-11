from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import configure_agent_mcps


class ConfigureAgentMcpsTests(unittest.TestCase):
    def test_write_atomic_text_atomicity_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mcp.json"
            path.write_text('{"old": true}\n', encoding="utf-8")

            assert configure_agent_mcps._write_atomic_text(path, '{"new": true}\n', dry_run=False)

            assert path.read_text(encoding="utf-8") == '{"new": true}\n'
            backup = path.with_suffix(path.suffix + ".agentic-env.bak")
            assert backup.read_text(encoding="utf-8") == '{"old": true}\n'

    def test_install_skill_atomic_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "hermes"
            skill = configure_agent_mcps.SKILLS["lean-ctx"]

            assert configure_agent_mcps._install_skill(root, skill, dry_run=False) is True
            skill_path = root / skill.name / "SKILL.md"
            assert skill_path.read_text(encoding="utf-8") == skill.body.rstrip() + "\n"

            assert configure_agent_mcps._install_skill(root, skill, dry_run=False) is True
            assert skill_path.read_text(encoding="utf-8") == skill.body.rstrip() + "\n"

    def test_parse_yaml_roundtrip_and_scalar_types(self) -> None:
        raw = """mcp_servers:
  lean-ctx:
    command: lean-ctx
  agentmemory:
    command: npx
    args: [\"-y\", \"@agentmemory/mcp\"]
memory:
  provider: agentmemory
flags: [\"-a\", \"-b\"]
enabled: true
count: 3
pi: 3.14
nullish: null
"""
        parsed = configure_agent_mcps._parse_yaml_config(raw)

        self.assertEqual(
            parsed["mcp_servers"]["agentmemory"],
            {"command": "npx", "args": ["-y", "@agentmemory/mcp"]},
        )
        self.assertEqual(parsed["memory"]["provider"], "agentmemory")
        self.assertEqual(parsed["flags"], ["-a", "-b"])
        self.assertEqual(parsed["enabled"], True)
        self.assertEqual(parsed["count"], 3)
        self.assertAlmostEqual(parsed["pi"], 3.14)
        self.assertIsNone(parsed["nullish"])

        dumped = configure_agent_mcps._dump_yaml_config(parsed)
        self.assertIn("agentmemory:", dumped)
        self.assertIn('args: ["-y", "@agentmemory/mcp"]', dumped)

    def test_configure_hermes_is_idempotent_when_already_compliant(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                """mcp_servers:
  lean-ctx:
    command: lean-ctx
  codebase-memory-mcp:
    command: codebase-memory-mcp
  agentmemory:
    command: npx
    args: [\"-y\", \"@agentmemory/mcp\"]
memory:
  provider: agentmemory
""",
                encoding="utf-8",
            )
            with patch(
                "agentic_env.configure_agent_mcps._HERMES_CONFIG_ADAPTER",
                configure_agent_mcps._HermesConfigAdapter(path=path),
            ):
                assert configure_agent_mcps.configure_hermes(
                    [
                        configure_agent_mcps.MCP_SERVERS["lean-ctx"],
                        configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"],
                        configure_agent_mcps.MCP_SERVERS["agentmemory"],
                    ],
                    dry_run=False,
                )
            parsed = configure_agent_mcps._parse_yaml_config(path.read_text(encoding="utf-8"))
            self.assertEqual(len(parsed), 2)
            self.assertIn("mcp_servers", parsed)
            self.assertIn("memory", parsed)
            self.assertEqual(
                set(parsed["mcp_servers"].keys()),
                {"lean-ctx", "codebase-memory-mcp", "agentmemory"},
            )
            self.assertEqual(parsed["memory"]["provider"], "agentmemory")
            self.assertFalse(path.with_suffix(path.suffix + ".agentic-env.bak").exists())

    def test_configure_hermes_adds_missing_entries_and_sets_memory_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                """mcp_servers:
  lean-ctx:
    command: lean-ctx
""",
                encoding="utf-8",
            )
            with patch(
                "agentic_env.configure_agent_mcps._HERMES_CONFIG_ADAPTER",
                configure_agent_mcps._HermesConfigAdapter(path=path),
            ):
                assert configure_agent_mcps.configure_hermes(
                    [configure_agent_mcps.MCP_SERVERS["agentmemory"]],
                    dry_run=False,
                )
            parsed = configure_agent_mcps._parse_yaml_config(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["mcp_servers"]["agentmemory"]["command"], "npx")
            self.assertEqual(
                parsed["mcp_servers"]["agentmemory"]["args"],
                ["-y", "@agentmemory/mcp"],
            )
            self.assertEqual(parsed["memory"]["provider"], "agentmemory")

    def test_configure_hermes_rejects_malformed_yaml_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            original = "mcp_servers: [\n"
            path.write_text(original, encoding="utf-8")
            with patch(
                "agentic_env.configure_agent_mcps._HERMES_CONFIG_ADAPTER",
                configure_agent_mcps._HermesConfigAdapter(path=path),
            ):
                self.assertFalse(
                    configure_agent_mcps.configure_hermes(
                        [configure_agent_mcps.MCP_SERVERS["lean-ctx"]],
                        dry_run=False,
                    )
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_configure_omp_only_adds_codebase_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mcp.json"
            path.write_text("{}", encoding="utf-8")
            with patch(
                "agentic_env.configure_agent_mcps._OMP_CONFIG_ADAPTERS",
                [configure_agent_mcps._OmpConfigAdapter(path=path)],
            ):
                assert configure_agent_mcps.configure_omp(
                    [
                        configure_agent_mcps.MCP_SERVERS["lean-ctx"],
                        configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"],
                        configure_agent_mcps.MCP_SERVERS["agentmemory"],
                    ],
                    dry_run=False,
                )
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["mcpServers"],
                {"codebase-memory-mcp": {"command": "codebase-memory-mcp"}},
            )

    def test_install_skills_omits_lean_ctx_and_agentmemory_on_omp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "skills"
            with patch(
                "agentic_env.configure_agent_mcps.OMP_SKILL_ROOTS",
                (root,),
            ):
                assert configure_agent_mcps.install_skills(
                    ["omp"],
                    ["lean-ctx", "codebase-memory-mcp", "agentmemory", "ponytail"],
                    dry_run=False,
                )

            self.assertFalse((root / "lean-ctx").exists())
            self.assertFalse((root / "agentmemory").exists())
            self.assertTrue((root / "codebase-memory-mcp" / "SKILL.md").is_file())
            self.assertTrue((root / "ponytail" / "SKILL.md").is_file())

    def test_configure_omp_rejects_non_object_root_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mcp.json"
            original = "[]"
            path.write_text(original, encoding="utf-8")
            with patch(
                "agentic_env.configure_agent_mcps._OMP_CONFIG_ADAPTERS",
                [configure_agent_mcps._OmpConfigAdapter(path=path)],
            ):
                self.assertFalse(
                    configure_agent_mcps.configure_omp(
                        [configure_agent_mcps.MCP_SERVERS["lean-ctx"]],
                        dry_run=False,
                    )
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_builtin_skill_bodies_are_loaded_from_assets(self) -> None:
        for name, skill in configure_agent_mcps.SKILLS.items():
            descriptor_path = configure_agent_mcps._skill_body_path(name)
            self.assertEqual(skill.body, descriptor_path.read_text(encoding="utf-8"))

    @patch("agentic_env.configure_agent_mcps.warn")
    def test_missing_skill_body_uses_fallback(self, mock_warn) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "agentic_env.configure_agent_mcps._SKILL_BODY_DIR",
                Path(temp_dir),
            ):
                body = configure_agent_mcps._load_skill_body("lean-ctx")

            self.assertIn("Built-in skill body is unavailable", body)
            mock_warn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
