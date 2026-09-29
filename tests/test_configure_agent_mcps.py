from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

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

    def test_configure_hermes_is_idempotent_when_already_compliant(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            original = f"""# user-owned formatting
mcp_servers:
  codebase-memory-mcp:
    command: codebase-memory-mcp
    env: {{"USER_OPTION": "keep"}}
  agentmemory:
    command: npx
    args: ["-y", "@agentmemory/mcp@{AGENTMEMORY_VERSION}"]
    timeout: 120
memory:
  provider: agentmemory
  user_option: keep
"""
            path.write_text(original, encoding="utf-8")
            with patch(
                "agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path
            ):
                for dry_run in (False, True):
                    self.assertTrue(configure_agent_mcps.configure_hermes(
                        list(configure_agent_mcps.MCP_SERVERS.values()), dry_run=dry_run
                    ))
                    self.assertEqual(path.read_bytes(), original.encode())
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
                "agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path
            ):
                assert configure_agent_mcps.configure_hermes(
                    [configure_agent_mcps.MCP_SERVERS["agentmemory"]],
                    dry_run=False,
                )
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["mcp_servers"]["agentmemory"]["command"], "npx")
            self.assertEqual(
                parsed["mcp_servers"]["agentmemory"]["args"],
                ["-y", f"@agentmemory/mcp@{AGENTMEMORY_VERSION}"],
            )
            self.assertEqual(parsed["memory"]["provider"], "agentmemory")

    def test_stale_selected_entries_fail_without_partial_writes(self) -> None:
        server = configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]
        missing = configure_agent_mcps.McpServer("missing", "missing-mcp")
        for agent, key in (
            ("hermes", "mcp_servers"),
            ("omp", "mcpServers"),
        ):
            for entry in (
                "not-a-mapping",
                {"command": "stale-command", "env": {"USER_OPTION": "keep"}},
                {"command": server.command, "args": ["--stale"]},
                {"command": server.command, "args": None},
            ):
                with self.subTest(agent=agent, entry=entry), tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / "config"
                    data = {key: {server.name: entry}, "user_option": "keep"}
                    original = (
                        yaml.safe_dump(data, sort_keys=False)
                        if agent == "hermes" else json.dumps(data, indent=4) + "\n"
                    ).encode()
                    path.write_bytes(original)
                    config_patch = (
                        patch("agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path)
                        if agent == "hermes"
                        else patch(
                            "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                            (path,),
                        )
                    )
                    with (
                        config_patch,
                        patch("agentic_env.configure_agent_mcps.warn") as warn,
                    ):
                        configure = (
                            configure_agent_mcps.configure_hermes
                            if agent == "hermes"
                            else configure_agent_mcps.configure_omp
                        )
                        for dry_run in (False, True):
                            self.assertFalse(configure([missing, server], dry_run=dry_run))
                            self.assertEqual(path.read_bytes(), original)
                        diagnostic = " ".join(call.args[0] for call in warn.call_args_list)
                        self.assertIn(str(path), diagnostic)
                        self.assertIn(f"{key}.{server.name}", diagnostic)
                    self.assertFalse(path.with_suffix(path.suffix + ".agentic-env.bak").exists())

    def test_stale_hermes_args_fail_cli_without_adding_missing_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            original = b"""# preserve this file
mcp_servers:
  agentmemory:
    command: npx
    args: ["-y", "@agentmemory/mcp"]
memory:
  provider: agentmemory
"""
            path.write_bytes(original)
            with (
                patch("agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path),
                patch("agentic_env.configure_agent_mcps.warn") as warn,
            ):
                self.assertEqual(configure_agent_mcps.main([
                    "--agent", "hermes", "--server", "all", "--no-skills", "--yes"
                ]), 1)
                self.assertEqual(path.read_bytes(), original)
                diagnostic = " ".join(call.args[0] for call in warn.call_args_list)
                self.assertIn(str(path), diagnostic)
                self.assertIn("mcp_servers.agentmemory", diagnostic)
                self.assertIn("args", diagnostic)

    def test_hermes_provider_conflict_is_reported_without_partial_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yaml"
            original = b"memory:\n  provider: user-memory\n  custom: keep\n"
            path.write_bytes(original)
            with (
                patch("agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path),
                patch("agentic_env.configure_agent_mcps.warn") as warn,
            ):
                self.assertFalse(configure_agent_mcps.configure_hermes(
                    list(configure_agent_mcps.MCP_SERVERS.values()), dry_run=False
                ))
                self.assertEqual(path.read_bytes(), original)
                diagnostic = " ".join(call.args[0] for call in warn.call_args_list)
                for value in (str(path), "memory.provider", "user-memory", "agentmemory"):
                    self.assertIn(value, diagnostic)

    def test_fresh_configs_support_dry_run_and_compliant_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            hermes = Path(temp_dir) / "hermes.yaml"
            omp = Path(temp_dir) / "omp.json"
            with (
                patch("agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", hermes),
                patch(
                    "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                    (omp,),
                ),
            ):
                for configure, path in ((configure_agent_mcps.configure_hermes, hermes), (configure_agent_mcps.configure_omp, omp)):
                    self.assertTrue(configure(list(configure_agent_mcps.MCP_SERVERS.values()), dry_run=True))
                    self.assertFalse(path.exists())
                    self.assertTrue(configure(list(configure_agent_mcps.MCP_SERVERS.values()), dry_run=False))
                    original = path.read_bytes()
                    self.assertTrue(configure(list(configure_agent_mcps.MCP_SERVERS.values()), dry_run=False))
                    self.assertEqual(path.read_bytes(), original)
                    self.assertFalse(path.with_suffix(path.suffix + ".agentic-env.bak").exists())

    def test_hermes_validation_checks_definitions_and_provider(self) -> None:
        server = configure_agent_mcps.MCP_SERVERS["agentmemory"]
        data = {
            "mcp_servers": {
                "agentmemory": {
                    "command": "npx",
                    "args": list(server.args),
                    "env": {"USER_OPTION": "keep"},
                },
            },
            "memory": {"provider": "agentmemory"},
        }
        self.assertTrue(
            configure_agent_mcps.validate_hermes_config(
                data, [server], required_provider="agentmemory"
            )
        )
        for entry in (
            False,
            {"command": "wrong-binary", "args": list(server.args)},
            {"command": "npx", "args": ["-y", "@agentmemory/mcp"]},
        ):
            with self.subTest(entry=entry):
                stale = {**data, "mcp_servers": {"agentmemory": entry}}
                self.assertFalse(
                    configure_agent_mcps.validate_hermes_config(
                        stale, [server], required_provider="agentmemory"
                    )
                )
        conflict = {**data, "memory": {"provider": "user-memory"}}
        self.assertFalse(
            configure_agent_mcps.validate_hermes_config(
                conflict, [server], required_provider="agentmemory"
            )
        )

    def test_configure_hermes_preserves_user_yaml_structures(self) -> None:
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
    jobs:
      - name: user-owned
        prompt: |
          Keep my config
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
                "agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path
            ):
                assert configure_agent_mcps.configure_hermes(
                    [configure_agent_mcps.MCP_SERVERS["agentmemory"]],
                    dry_run=False,
                )

            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
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
                    "jobs": [{"name": "user-owned", "prompt": "Keep my config\n"}],
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
        for original in ("mcp_servers: [\n", "toolsets:\n  - hermes-cli\n  unexpected: mapping\n"):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "config.yaml"
                path.write_text(original, encoding="utf-8")
                with patch(
                    "agentic_env.configure_agent_mcps.HERMES_CONFIG_PATH", path
                ):
                    self.assertFalse(
                        configure_agent_mcps.configure_hermes(
                            [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
                            dry_run=False,
                        )
                    )
                self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_configure_omp_only_adds_codebase_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mcp.json"
            path.write_text("{}", encoding="utf-8")
            with patch(
                "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                (path,),
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
                "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                (path,),
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
                    "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                    (path,),
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
            for name in configure_agent_mcps.OMP_HOOK_FILES:
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
            self.assertEqual(configure_agent_mcps.omp_config_drift(yaml.safe_load(text)), [])
            self.assertIn(str(hooks / "retention-canary.ts"), text)

    def test_converge_omp_agent_config_finds_hooks_in_home_dotfiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            hooks = home / ".dotfiles" / "omp" / "hooks"
            hooks.mkdir(parents=True)
            for name in configure_agent_mcps.OMP_HOOK_FILES:
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
            self.assertEqual(configure_agent_mcps.omp_config_drift(yaml.safe_load(text)), [])
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
            ):
                self.assertFalse(configure_agent_mcps.converge_omp_agent_config(dry_run=False))
            self.assertFalse(config_path.exists())

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
            self.assertIn("compaction.thresholdTokens", mock_warn.call_args[0][0])
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
                "agentic_env.configure_agent_mcps.OMP_MCP_PATHS",
                (path,),
            ):
                self.assertFalse(
                    configure_agent_mcps.configure_omp(
                        [configure_agent_mcps.MCP_SERVERS["codebase-memory-mcp"]],
                        dry_run=False,
                    )
                )
            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
