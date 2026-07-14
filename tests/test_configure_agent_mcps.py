from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
