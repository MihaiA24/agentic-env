from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import configure_agent_mcps
from agentic_env.stack_metadata import AGENTMEMORY_VERSION


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
            skill = configure_agent_mcps.SKILLS["codebase-memory-mcp"]

            assert configure_agent_mcps._install_skill(root, skill, dry_run=False) is True
            skill_path = root / skill.name / "SKILL.md"
            assert skill_path.read_text(encoding="utf-8") == skill.body.rstrip() + "\n"

            assert configure_agent_mcps._install_skill(root, skill, dry_run=False) is True
            assert skill_path.read_text(encoding="utf-8") == skill.body.rstrip() + "\n"

    def test_parse_yaml_roundtrip_and_scalar_types(self) -> None:
        raw = """mcp_servers:
  codebase-memory-mcp:
    command: codebase-memory-mcp
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
        self.assertEqual(configure_agent_mcps._parse_yaml_config(dumped), parsed)

    def test_configure_hermes_is_idempotent_when_already_compliant(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                """mcp_servers:
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
                {"codebase-memory-mcp", "agentmemory"},
            )
            self.assertEqual(parsed["memory"]["provider"], "agentmemory")
            self.assertFalse(path.with_suffix(path.suffix + ".agentic-env.bak").exists())

    def test_configure_hermes_adds_missing_entries_and_sets_memory_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                """mcp_servers:
  codebase-memory-mcp:
    command: codebase-memory-mcp
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
                ["-y", f"@agentmemory/mcp@{AGENTMEMORY_VERSION}"],
            )
            self.assertEqual(parsed["memory"]["provider"], "agentmemory")

    def test_configure_hermes_preserves_scalar_block_lists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            path.write_text(
                """toolsets:
- hermes-cli
- terminal
platform_toolsets:
  darwin:
    - browser
  linux:
  - shell
mcp_servers:
  user-owned:
    command: user-mcp
    args:
    - --endpoint=https://example.test:443
    - 'Authorization: user-owned'
    - 'it''s quoted'
    - "line\\nfeed # literal"  # trailing comment
    transport: stdio
discord:
  allowed_channels:
  - "guild:channel"
display:
  hidden_tools:
    - terminal
  memory_notifications: 'off'  # string, not a boolean
auxiliary:
  extra_body: {}
database:
  journal_mode: "wal"  # Supported values: "wal", "delete"
  timeout: 60  # seconds
gateway:
known_plugin_toolsets:
- custom-plugin
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

            parsed = configure_agent_mcps._parse_yaml_config(
                path.read_text(encoding="utf-8")
            )
            self.assertEqual(parsed["toolsets"], ["hermes-cli", "terminal"])
            self.assertEqual(
                parsed["platform_toolsets"],
                {"darwin": ["browser"], "linux": ["shell"]},
            )
            self.assertEqual(
                parsed["mcp_servers"]["user-owned"],
                {
                    "command": "user-mcp",
                    "args": [
                        "--endpoint=https://example.test:443",
                        "Authorization: user-owned",
                        "it's quoted",
                        "line\nfeed # literal",
                    ],
                    "transport": "stdio",
                },
            )
            self.assertEqual(
                parsed["mcp_servers"]["agentmemory"]["args"],
                ["-y", f"@agentmemory/mcp@{AGENTMEMORY_VERSION}"],
            )
            self.assertEqual(
                parsed["discord"]["allowed_channels"], ["guild:channel"]
            )
            self.assertEqual(parsed["display"]["hidden_tools"], ["terminal"])
            self.assertEqual(parsed["known_plugin_toolsets"], ["custom-plugin"])
            self.assertEqual(parsed["display"]["memory_notifications"], "off")
            self.assertEqual(parsed["auxiliary"]["extra_body"], {})
            self.assertEqual(parsed["database"], {"journal_mode": "wal", "timeout": 60})
            self.assertIsNone(parsed["gateway"])

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
                        [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
                        dry_run=False,
                    )
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_configure_hermes_rejects_non_scalar_block_lists_without_writing(
        self,
    ) -> None:
        originals = (
            """toolsets:
- name: hermes-cli
""",
            """toolsets:
  - hermes-cli
  unexpected: mapping
""",
        )
        for original in originals:
            with (
                self.subTest(original=original),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                path = Path(temp_dir) / "config.yaml"
                path.write_text(original, encoding="utf-8")
                with patch(
                    "agentic_env.configure_agent_mcps._HERMES_CONFIG_ADAPTER",
                    configure_agent_mcps._HermesConfigAdapter(path=path),
                ):
                    self.assertFalse(
                        configure_agent_mcps.configure_hermes(
                            [
                                configure_agent_mcps.MCP_SERVERS[
                                    "codebase-memory-mcp"
                                ]
                            ],
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

    def test_configure_omp_removes_excluded_entries_from_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mcp.json"
            path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "agentmemory": {"command": "agentmemory"},
                            "lean-ctx": {"command": "lean-ctx-mcp"},
                            "user-owned": {"command": "keep-me"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "agentic_env.configure_agent_mcps._OMP_CONFIG_ADAPTERS",
                [configure_agent_mcps._OmpConfigAdapter(path=path)],
            ):
                assert configure_agent_mcps.configure_omp(
                    [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
                    dry_run=False,
                )
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["mcpServers"],
                {
                    "codebase-memory-mcp": {"command": "codebase-memory-mcp"},
                    "user-owned": {"command": "keep-me"},
                },
            )

    def test_configure_omp_gates_default_off_servers(self) -> None:
        for existing, expected_disabled in (
            ({}, ["codebase-memory-mcp", "node_repl", "agentmemory", "lean-ctx"]),
            (
                {"disabledServers": ["node_repl"]},
                ["node_repl", "codebase-memory-mcp", "agentmemory", "lean-ctx"],
            ),
        ):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "mcp.json"
                path.write_text(json.dumps(existing), encoding="utf-8")
                with patch(
                    "agentic_env.configure_agent_mcps._OMP_CONFIG_ADAPTERS",
                    [configure_agent_mcps._OmpConfigAdapter(path=path)],
                ):
                    assert configure_agent_mcps.configure_omp(
                        [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
                        dry_run=False,
                    )
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("codebase-memory-mcp", parsed["mcpServers"])
                self.assertEqual(parsed["disabledServers"], expected_disabled)

    def test_converge_omp_agent_config_seeds_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotfiles = Path(temp_dir) / "dotfiles"
            hooks = dotfiles / "omp" / "hooks"
            hooks.mkdir(parents=True)
            for name in configure_agent_mcps._OMP_HOOK_FILES:
                (hooks / name).write_text("// hook\n", encoding="utf-8")
            config_path = Path(temp_dir) / "config.yml"
            with (
                patch(
                    "agentic_env.configure_agent_mcps.OMP_AGENT_CONFIG_PATH",
                    config_path,
                ),
                patch.dict(
                    "os.environ", {"AGENTIC_DOTFILES_ROOT": str(dotfiles)}
                ),
            ):
                assert configure_agent_mcps.converge_omp_agent_config(dry_run=False)
            text = config_path.read_text(encoding="utf-8")
            self.assertEqual(configure_agent_mcps.omp_config_drift(text), [])
            self.assertIn(str(hooks / "retention-canary.ts"), text)

    def test_converge_omp_agent_config_finds_hooks_in_home_dotfiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            hooks = home / ".dotfiles" / "omp" / "hooks"
            hooks.mkdir(parents=True)
            for name in configure_agent_mcps._OMP_HOOK_FILES:
                (hooks / name).write_text("// hook\n", encoding="utf-8")
            config_path = Path(temp_dir) / "config.yml"
            with (
                patch("agentic_env.configure_agent_mcps.OMP_AGENT_CONFIG_PATH", config_path),
                patch("agentic_env.configure_agent_mcps.Path.home", lambda: home),
                patch("agentic_env.configure_agent_mcps.Path.cwd", lambda: Path(temp_dir)),
                patch.dict("os.environ", {"AGENTIC_DOTFILES_ROOT": ""}),
            ):
                assert configure_agent_mcps.converge_omp_agent_config(dry_run=False)
            text = config_path.read_text(encoding="utf-8")
            self.assertEqual(configure_agent_mcps.omp_config_drift(text), [])
            self.assertIn(str(hooks / "verification-recorder.ts"), text)

    def test_converge_omp_agent_config_refuses_to_seed_without_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            home.mkdir()
            config_path = Path(temp_dir) / "config.yml"
            with (
                patch("agentic_env.configure_agent_mcps.OMP_AGENT_CONFIG_PATH", config_path),
                patch("agentic_env.configure_agent_mcps.Path.home", lambda: home),
                patch("agentic_env.configure_agent_mcps.Path.cwd", lambda: Path(temp_dir)),
                patch("agentic_env.configure_agent_mcps.__file__", str(Path(temp_dir) / "pkg" / "x.py")),
                patch.dict("os.environ", {"AGENTIC_DOTFILES_ROOT": ""}),
                patch("agentic_env.configure_agent_mcps.warn") as mock_warn,
            ):
                self.assertFalse(configure_agent_mcps.converge_omp_agent_config(dry_run=False))
            self.assertFalse(config_path.exists())
            self.assertIn("omp/hooks not found", mock_warn.call_args[0][0])

    def test_converge_omp_agent_config_warns_on_drift_without_rewriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            original = "memory:\n  backend: mnemopi\n"
            config_path.write_text(original, encoding="utf-8")
            with (
                patch(
                    "agentic_env.configure_agent_mcps.OMP_AGENT_CONFIG_PATH",
                    config_path,
                ),
                patch("agentic_env.configure_agent_mcps.warn") as mock_warn,
            ):
                assert configure_agent_mcps.converge_omp_agent_config(dry_run=False)
            mock_warn.assert_called_once()
            self.assertIn("compaction.thresholdTokens: 150000", mock_warn.call_args[0][0])
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)

    def test_install_skills_omits_agentmemory_on_omp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "skills"
            with patch(
                "agentic_env.configure_agent_mcps.OMP_SKILL_ROOTS",
                (root,),
            ):
                assert configure_agent_mcps.install_skills(
                    ["omp"],
                    ["codebase-memory-mcp", "agentmemory", "ponytail"],
                    dry_run=False,
                )

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
                        [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
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
                body = configure_agent_mcps._load_skill_body("codebase-memory-mcp")

            self.assertIn("Built-in skill body is unavailable", body)
            mock_warn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
