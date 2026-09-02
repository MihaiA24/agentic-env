from __future__ import annotations

import contextlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import configure_agent_mcps, stack_doctor
from agentic_env.common import console
from agentic_env.install_skills_mcps import profile_skills


def _skill(root: Path, name: str) -> None:
    (root / name).mkdir(parents=True, exist_ok=True)
    (root / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")


class _Host:
    """Compliant fixture tree; tests break one thing at a time."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.mcp_paths = (root / "omp" / "mcp.json", root / "pi" / "mcp.json")
        self.skill_roots = (root / "omp" / "skills", root / "pi" / "skills")
        self.agent_config = root / "omp" / "config.yml"
        self.claude_json = root / ".claude.json"
        self.claude_skills = root / "claude" / "skills"
        self.hermes_config = root / "hermes" / "config.yaml"
        self.hermes_skills = root / "hermes" / "skills"
        hooks = root / "hooks"
        hooks.mkdir()
        for name in configure_agent_mcps._OMP_HOOK_FILES:
            (hooks / name).write_text("// hook\n", encoding="utf-8")
        for path in self.mcp_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.write_mcp(path, gated=True)
        extensions = "extensions:\n" + "".join(
            f"  - {hooks / name}\n" for name in configure_agent_mcps._OMP_HOOK_FILES
        )
        self.agent_config.write_text(
            configure_agent_mcps._OMP_AGENT_CONFIG_TEMPLATE.format(extensions=extensions),
            encoding="utf-8",
        )
        self.claude_json.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        for name in profile_skills("default"):
            _skill(self.claude_skills, name)
        for skills_root in self.skill_roots:
            for name in ("codebase-memory-mcp", "ponytail"):
                _skill(skills_root, name)
        self.hermes_config.parent.mkdir(parents=True)
        self.hermes_config.write_text(
            "mcp_servers:\n  codebase-memory-mcp:\n    command: codebase-memory-mcp\n"
            "  agentmemory:\n    command: npx\n",
            encoding="utf-8",
        )
        for name in configure_agent_mcps.SKILLS:
            _skill(self.hermes_skills, name)

    @staticmethod
    def write_mcp(path: Path, *, gated: bool, extra: dict[str, object] | None = None) -> None:
        servers: dict[str, object] = {"codebase-memory-mcp": {"command": "codebase-memory-mcp"}}
        servers.update(extra or {})
        data = {"mcpServers": servers, "disabledServers": ["codebase-memory-mcp"] if gated else []}
        path.write_text(json.dumps(data), encoding="utf-8")

    def patched(self, *, missing_commands: tuple[str, ...] = ()) -> contextlib.ExitStack:
        stack = contextlib.ExitStack()
        for target, value in (
            ("agentic_env.configure_agent_mcps.OMP_MCP_PATHS", self.mcp_paths),
            ("agentic_env.configure_agent_mcps.OMP_SKILL_ROOTS", self.skill_roots),
            ("agentic_env.configure_agent_mcps.OMP_AGENT_CONFIG_PATH", self.agent_config),
            ("agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", self.hermes_config),
            ("agentic_env.configure_agent_mcps.HERMES_SKILL_ROOT", self.hermes_skills),
            ("agentic_env.stack_doctor.CLAUDE_USER_CONFIG_PATH", self.claude_json),
            ("agentic_env.stack_doctor.CLAUDE_SKILL_ROOT", self.claude_skills),
        ):
            stack.enter_context(patch(target, value))
        stack.enter_context(
            patch("agentic_env.stack_doctor.cmd_exists", lambda name: name not in missing_commands)
        )
        stack.enter_context(patch("agentic_env.stack_doctor.cmd_version_matches", lambda *_: True))
        return stack


def _run(host: _Host, **kwargs: object) -> tuple[int, str]:
    with host.patched(**kwargs), console.capture() as capture:
        code = stack_doctor.main([])
    return code, capture.get()


class StackDoctorTests(unittest.TestCase):
    def test_compliant_host_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            code, output = _run(_Host(Path(temp_dir)))
        self.assertEqual(code, 0)
        self.assertIn("stack OK", output)
        self.assertNotIn("TODO secondary", output)

    def test_ungated_server_fails_with_corrective_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.write_mcp(host.mcp_paths[1], gated=False)
            code, output = _run(host)
        self.assertEqual(code, 1)
        self.assertIn("not in disabledServers", output)
        self.assertIn(stack_doctor.FIX_CONFIGURE, output)

    def test_claude_import_interception_prose_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.claude_json.write_text(
                json.dumps({"mcpServers": {"lean-ctx": {"command": "lean-ctx", "instructions": "shadow mode: ctx_read"}}}),
                encoding="utf-8",
            )
            code, output = _run(host)
        self.assertEqual(code, 1)
        self.assertIn("lean-ctx", output)

    def test_missing_secondary_only_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.hermes_config.unlink()
            code, output = _run(host, missing_commands=("hermes", "codex"))
        self.assertEqual(code, 0)
        self.assertIn("TODO secondary", output)
        self.assertIn("hermes on PATH", output)


if __name__ == "__main__":
    unittest.main()
