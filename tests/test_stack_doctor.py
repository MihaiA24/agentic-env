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
        for name in configure_agent_mcps.OMP_HOOK_FILES:
            (hooks / name).write_text("// hook\n", encoding="utf-8")
        for path in self.mcp_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.write_mcp(path, gated=True)
        extensions = "extensions:\n" + "".join(
            f"  - {hooks / name}\n" for name in configure_agent_mcps.OMP_HOOK_FILES
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
            f"  agentmemory:\n    command: npx\n    args: {json.dumps(list(configure_agent_mcps.MCP_SERVERS['agentmemory'].args))}\n"
            "memory:\n  provider: agentmemory\n",
            encoding="utf-8",
        )
        for name in configure_agent_mcps.SKILLS:
            _skill(self.hermes_skills, name)

    @staticmethod
    def write_mcp(
        path: Path,
        *,
        gated: bool,
        extra: dict[str, object] | None = None,
        disabled: list[str] | None = None,
    ) -> None:
        servers: dict[str, object] = {"codebase-memory-mcp": {"command": "codebase-memory-mcp"}}
        servers.update(extra or {})
        if disabled is None:
            disabled = ["codebase-memory-mcp", "node_repl", *configure_agent_mcps.OMP_EXCLUDED_SERVERS] if gated else []
        data = {"mcpServers": servers, "disabledServers": disabled}
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
        stack.enter_context(patch("agentic_env.stack_doctor.cmd_version_at_least", lambda *_: True))
        return stack


def _run(host: _Host, **kwargs: object) -> tuple[int, str]:
    with host.patched(**kwargs), console.capture() as capture:
        code = stack_doctor.main([])
    return code, capture.get()


class StackDoctorTests(unittest.TestCase):
    def test_compliant_host_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            with host.patched():
                checks = stack_doctor.run_checks()
                self.assertEqual(stack_doctor.report(checks), 0)
            self.assertEqual([check for check in checks if not check.ok], [])

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

    def test_claude_import_excluded_server_fails_without_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.claude_json.write_text(
                json.dumps({"mcpServers": {"lean-ctx": {"command": "lean-ctx"}}}),
                encoding="utf-8",
            )
            code, output = _run(host)
        self.assertEqual(code, 1)
        self.assertIn("excluded servers absent", output)
        self.assertIn("mcpServers.lean-ctx", output)

    def test_node_repl_builtin_must_be_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.write_mcp(
                host.mcp_paths[0], gated=True,
                disabled=["codebase-memory-mcp", *configure_agent_mcps.OMP_EXCLUDED_SERVERS],
            )
            code, output = _run(host)
        self.assertEqual(code, 1)
        self.assertIn("node_repl gated", output)

    def test_excluded_names_must_stay_disabled_even_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.write_mcp(host.mcp_paths[0], gated=True, disabled=["codebase-memory-mcp", "node_repl"])
            original = host.mcp_paths[0].read_bytes()
            with host.patched():
                failures = [check for check in stack_doctor.run_checks() if not check.ok]
                self.assertEqual(stack_doctor.report(failures), 1)
            for name in configure_agent_mcps.OMP_EXCLUDED_SERVERS:
                self.assertTrue(any(name in check.detail and check.mandatory for check in failures))
            self.assertEqual(host.mcp_paths[0].read_bytes(), original)

    def test_wrong_omp_definition_fails_without_repair(self) -> None:
        for entry in (
            {"command": "wrong-binary"},
            {"command": "codebase-memory-mcp", "args": ["--wrong"]},
            "not-a-mapping",
        ):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temp_dir:
                host = _Host(Path(temp_dir))
                path = host.mcp_paths[0]
                host.write_mcp(path, gated=True, extra={"codebase-memory-mcp": entry})
                original = path.read_bytes()
                with host.patched():
                    failures = [check for check in stack_doctor.run_checks() if not check.ok]
                    self.assertEqual(stack_doctor.report(failures), 1)
                self.assertTrue(any(check.mandatory and "mcpServers.codebase-memory-mcp" in check.fix for check in failures))
                self.assertTrue(all(stack_doctor.FIX_CONFIGURE not in check.fix for check in failures))
                self.assertEqual(path.read_bytes(), original)

    def test_method_order_requires_exact_sequence_but_accepts_yaml_forms(self) -> None:
        method_block = "  methodOrder:\n    - handoff\n    - remote\n    - soft\n"
        cases = (
            ("", False),
            ("  methodOrder: []\n", False),
            ("  methodOrder: [remote, handoff, soft]\n", False),
            ("  methodOrder: [handoff, remote]\n", False),
            ("  methodOrder: '[handoff, remote, soft]'\n", False),
            ("  methodOrder: [handoff, remote, soft] # ordered fallback\n", True),
            ("  'methodOrder': ['handoff', \"remote\", soft]\n", True),
            ("  methodOrder: # fallback order\n    - 'handoff' # primary\n    - \"remote\"\n    - soft # final\n", True),
            ("  methodOrder:\n  - handoff\n  - remote\n  - soft\n", True),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            template = host.agent_config.read_text(encoding="utf-8")
            # Unrelated user-owned YAML structures must be tolerated, not rejected.
            template += "custom:\n  jobs:\n    - name: user-owned\n      prompt: |\n        Keep my config\n"
            for replacement, compliant in cases:
                with self.subTest(replacement=replacement):
                    original = template.replace(method_block, replacement).encode()
                    host.agent_config.write_bytes(original)
                    code, _ = _run(host)
                    self.assertEqual(code, 0 if compliant else 1)
                    self.assertEqual(host.agent_config.read_bytes(), original)

    def test_claude_skill_root_must_be_enabled_without_rewriting_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            original = host.agent_config.read_text(encoding="utf-8").replace(
                "  enableClaudeUser: true\n", ""
            )
            host.agent_config.write_text(original, encoding="utf-8")
            code, output = _run(host)
            self.assertEqual(code, 1)
            self.assertIn("skills.enableClaudeUser", output)
            self.assertEqual(host.agent_config.read_text(encoding="utf-8"), original)

            host.agent_config.write_text(
                original.replace("skills:\n", "skills:\n  enableClaudeUser: true\n"),
                encoding="utf-8",
            )
            code, _ = _run(host)
            self.assertEqual(code, 0)

    def test_agent_config_rejects_false_comment_and_nested_skill_root_without_rewriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            template = host.agent_config.read_text(encoding="utf-8")
            cases = (
                (
                    template.replace(
                        "  enableClaudeUser: true\n",
                        "  enableClaudeUser: false # enableClaudeUser: true\n",
                    ),
                    1,
                ),
                (
                    template.replace(
                        "  enableClaudeUser: true\n",
                        "  nested:\n    enableClaudeUser: true\n",
                    ),
                    1,
                ),
                (
                    template.replace(
                        "  enableClaudeUser: true\n",
                        "  enableClaudeUser: 1\n",
                    ),
                    1,
                ),
                (
                    template.replace(
                        "  backend: mnemopi\n",
                        '  backend: "mnemopi" # configured backend\n',
                    ),
                    0,
                ),
                (
                    template.replace(
                        "  enableClaudeUser: true\n",
                        "  enableClaudeUser: true # configured skill root\n",
                    ),
                    0,
                ),
            )
            for config, expected_code in cases:
                with self.subTest(config=config):
                    host.agent_config.write_text(config, encoding="utf-8")
                    original = host.agent_config.read_bytes()
                    code, _ = _run(host)
                    self.assertEqual(code, expected_code)
                    self.assertEqual(host.agent_config.read_bytes(), original)

    def test_hermes_lean_ctx_entry_only_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            host.hermes_config.write_text(
                host.hermes_config.read_text(encoding="utf-8").replace(
                    "\nmemory:\n", "\n  lean-ctx:\n    command: lean-ctx\nmemory:\n"
                ),
                encoding="utf-8",
            )
            code, output = _run(host)
        self.assertEqual(code, 0)
        self.assertIn("TODO secondary", output)
        self.assertIn("no lean-ctx", output)

    def test_hermes_definition_and_provider_drift_only_warn_without_repair(self) -> None:
        cases = (
            ("    command: npx\n", "    command: wrong-binary\n", "mcp_servers.agentmemory"),
            (
                json.dumps(list(configure_agent_mcps.MCP_SERVERS["agentmemory"].args)),
                '["-y", "@agentmemory/mcp"]',
                "mcp_servers.agentmemory",
            ),
            ("  provider: agentmemory\n", "  provider: user-memory\n", "memory.provider"),
            ("  provider: agentmemory\n", "", "memory.provider"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            template = host.hermes_config.read_text(encoding="utf-8")
            for old, new, entry in cases:
                with self.subTest(entry=entry, replacement=new):
                    original = template.replace(old, new).encode()
                    host.hermes_config.write_bytes(original)
                    with host.patched():
                        failures = [check for check in stack_doctor.run_checks() if not check.ok]
                        self.assertEqual(stack_doctor.report(failures), 0)
                    self.assertTrue(failures)
                    self.assertTrue(all(not check.mandatory for check in failures))
                    self.assertTrue(any(entry in check.detail or entry in check.name for check in failures))
                    if new:
                        self.assertTrue(any(entry in check.fix for check in failures))
                        self.assertTrue(all(stack_doctor.FIX_CONFIGURE not in check.fix for check in failures))
                    self.assertEqual(host.hermes_config.read_bytes(), original)

    def test_hermes_names_in_comments_or_non_mappings_are_not_wiring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            host = _Host(Path(temp_dir))
            original = b"""# mcp_servers: codebase-memory-mcp, agentmemory
# memory.provider: agentmemory
mcp_servers:
  codebase-memory-mcp: disabled
  agentmemory: false
memory:
  provider: agentmemory
"""
            host.hermes_config.write_bytes(original)
            with host.patched():
                failures = [check for check in stack_doctor.run_checks() if not check.ok]
                self.assertEqual(stack_doctor.report(failures), 0)
            self.assertTrue(all(not check.mandatory for check in failures))
            for name in configure_agent_mcps.MCP_SERVERS:
                self.assertTrue(any(name in check.name or name in check.detail for check in failures))
            self.assertEqual(host.hermes_config.read_bytes(), original)

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
