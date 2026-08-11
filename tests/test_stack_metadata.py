from __future__ import annotations

import hashlib
import io
import tarfile
import tempfile

import unittest
from unittest.mock import patch
from pathlib import Path

from agentic_env import (
    configure_agent_mcps,
    install_agents,
    install_skills_mcps,
    stack_metadata,
)
from agentic_env import update_agentic_stack
from agentic_env.common import install_pinned_binary_archive
from agentic_env.remote_install_contract import validate_remote_contract


class StackMetadataTests(unittest.TestCase):
    def test_remote_contracts_are_canonical(self) -> None:
        assert validate_remote_contract(
            stack_metadata.AGENTS_INSTALL_REMOTE_CONTRACT,
            scope="agentic-install-agents",
        )
        assert validate_remote_contract(
            stack_metadata.SKILLS_INSTALL_REMOTE_CONTRACT,
            scope="agentic-install-skills-mcps",
        )
        assert validate_remote_contract(
            stack_metadata.UPDATE_REMOTE_CONTRACT, scope="agentic-update-stack"
        )

    def test_install_modules_reference_canonical_metadata(self) -> None:
        assert (
            install_agents._REMOTE_INSTALL_CONTRACT
            is stack_metadata.AGENTS_INSTALL_REMOTE_CONTRACT
        )
        assert (
            install_skills_mcps._REMOTE_INSTALL_CONTRACT
            is stack_metadata.SKILLS_INSTALL_REMOTE_CONTRACT
        )
        assert (
            update_agentic_stack._REMOTE_INSTALL_CONTRACT
            is stack_metadata.UPDATE_REMOTE_CONTRACT
        )

        assert install_agents.HERMES_INSTALL_URL == stack_metadata.HERMES_INSTALL_URL
        assert install_agents.OMP_INSTALL_URL == stack_metadata.OMP_INSTALL_URL
        assert (
            install_agents.OPENAI_CODEX_PACKAGE == stack_metadata.OPENAI_CODEX_PACKAGE
        )
        assert install_agents.CLAUDE_INSTALL_URL == stack_metadata.CLAUDE_INSTALL_URL
        assert (
            install_skills_mcps.SKILL_AGENT_LOOKUP == stack_metadata.SKILL_AGENT_LOOKUP
        )
        assert (
            install_skills_mcps.SKILL_AGENT_CLI_NAMES
            == stack_metadata.SKILL_AGENT_CLI_NAMES
        )
        assert install_skills_mcps.SKILL_AGENTS == stack_metadata.SKILL_AGENTS
        assert (
            install_skills_mcps.SKILLS_CLI_PACKAGE == stack_metadata.SKILLS_CLI_PACKAGE
        )
        assert (
            install_skills_mcps.AGENTMEMORY_NPM_PACKAGE
            == stack_metadata.AGENTMEMORY_NPM_PACKAGE
        )
        assert (
            install_skills_mcps.CODEBASE_MEMORY_ARCHIVES
            is stack_metadata.CODEBASE_MEMORY_ARCHIVES
        )
        assert install_skills_mcps.LEAN_CTX_ARCHIVES is stack_metadata.LEAN_CTX_ARCHIVES
        assert (
            update_agentic_stack.AGENTMEMORY_NPM_PACKAGE
            == stack_metadata.AGENTMEMORY_NPM_PACKAGE
        )
        assert (
            update_agentic_stack.SKILLS_CLI_PACKAGE == stack_metadata.SKILLS_CLI_PACKAGE
        )
        assert (
            update_agentic_stack.STACK_VERSION_FRAGMENTS
            is stack_metadata.STACK_VERSION_FRAGMENTS
        )

        assert (
            configure_agent_mcps.AGENT_CHOICES == stack_metadata.CONFIGURE_AGENT_CHOICES
        )

    def test_install_skills_npx_command_uses_canonical_cli_package(self) -> None:
        with patch("agentic_env.install_skills_mcps.cmd_exists") as cmd_exists:
            cmd_exists.side_effect = lambda name: True if name == "npm" else False
            with patch("agentic_env.install_skills_mcps.run") as run:
                result = install_skills_mcps._install_skill_package(
                    "dummy", ["skill-1"], ["hermes"]
                )
                assert result is True
                run.assert_called_once_with(
                    [
                        "npx",
                        "--yes",
                        stack_metadata.SKILLS_CLI_PACKAGE,
                        "add",
                        "dummy",
                        "--global",
                        "--yes",
                        "--skill",
                        "skill-1",
                        "--agent",
                        "hermes-agent",
                    ]
                )

    def test_update_skills_and_codex_converge_through_pinned_installers(self) -> None:
        with (
            patch("agentic_env.update_agentic_stack.cmd_exists", return_value=True),
            patch(
                "agentic_env.update_agentic_stack.cmd_version_matches",
                side_effect=[False, True],
            ),
            patch("agentic_env.update_agentic_stack.run") as run,
        ):
            assert update_agentic_stack._update_skills() is True
            run.assert_called_once_with(
                ["npm", "install", "-g", stack_metadata.SKILLS_CLI_PACKAGE]
            )

        with (
            patch("agentic_env.update_agentic_stack.cmd_exists", return_value=True),
            patch(
                "agentic_env.install_agents._install_codex", return_value=True
            ) as install,
        ):
            assert update_agentic_stack._update_codex() is True
            install.assert_called_once_with(True)

    def test_agent_installers_pass_immutable_upstream_refs(self) -> None:
        with (
            patch(
                "agentic_env.install_agents.cmd_version_matches",
                side_effect=[False, True],
            ),
            patch("agentic_env.install_agents.cmd_exists", return_value=False),
            patch(
                "agentic_env.install_agents.run_remote_script", return_value=True
            ) as remote,
        ):
            assert install_agents._install_hermes(True) is True
            assert remote.call_args.kwargs["interpreter_args"] == [
                "--skip-setup",
                "--commit",
                stack_metadata.HERMES_COMMIT,
            ]

        with (
            patch(
                "agentic_env.install_agents.cmd_version_matches",
                side_effect=[False, True],
            ),
            patch("agentic_env.install_agents.cmd_exists", return_value=False),
            patch(
                "agentic_env.install_agents.run_remote_script", return_value=True
            ) as remote,
        ):
            assert install_agents._install_omp(True) is True
            assert remote.call_args.kwargs["interpreter_args"] == [
                "--ref",
                stack_metadata.OMP_REF,
            ]

        with (
            patch(
                "agentic_env.install_agents.cmd_version_matches",
                side_effect=[False, True],
            ),
            patch("agentic_env.install_agents.cmd_exists", return_value=False),
            patch(
                "agentic_env.install_agents.run_remote_script", return_value=True
            ) as remote,
        ):
            assert install_agents._install_claude(True) is True
            assert remote.call_args.kwargs["interpreter_args"] == [
                stack_metadata.CLAUDE_VERSION
            ]

    def test_release_archive_contract_covers_supported_hosts(self) -> None:
        platforms = {
            ("darwin", "amd64"),
            ("darwin", "arm64"),
            ("linux", "amd64"),
            ("linux", "arm64"),
        }
        assert set(stack_metadata.LEAN_CTX_ARCHIVES) == platforms
        assert {key[:2] for key in stack_metadata.CODEBASE_MEMORY_ARCHIVES} == platforms
        assert {key[2] for key in stack_metadata.CODEBASE_MEMORY_ARCHIVES} == {
            False,
            True,
        }
        for _, checksum in (
            *stack_metadata.LEAN_CTX_ARCHIVES.values(),
            *stack_metadata.CODEBASE_MEMORY_ARCHIVES.values(),
        ):
            assert len(checksum) == 64
            int(checksum, 16)

    def test_pinned_archive_installs_only_verified_binary(self) -> None:
        archive_data = io.BytesIO()
        binary_data = b"curated binary"
        with tarfile.open(fileobj=archive_data, mode="w:gz") as archive:
            member = tarfile.TarInfo("release/tool")
            member.size = len(binary_data)
            archive.addfile(member, io.BytesIO(binary_data))
        payload = archive_data.getvalue()

        with (
            tempfile.TemporaryDirectory() as home,
            patch.object(Path, "home", return_value=Path(home)),
            patch(
                "agentic_env.common.urllib.request.urlopen",
                return_value=io.BytesIO(payload),
            ),
        ):
            assert install_pinned_binary_archive(
                label="tool",
                binary="tool",
                url="https://example.invalid/tool.tar.gz",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
            )
            installed = Path(home) / ".local" / "bin" / "tool"
            assert installed.read_bytes() == binary_data
            assert installed.stat().st_mode & 0o111


if __name__ == "__main__":
    unittest.main()
