from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
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
