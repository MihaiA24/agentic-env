from __future__ import annotations

import unittest
from unittest.mock import patch

from agentic_env import configure_agent_mcps, install_agents, install_skills_mcps, stack_metadata
from agentic_env import update_agentic_stack
from agentic_env.remote_install_contract import validate_remote_contract


class StackMetadataTests(unittest.TestCase):
    def test_remote_contracts_are_canonical(self) -> None:
        assert (
            validate_remote_contract(
                stack_metadata.AGENTS_INSTALL_REMOTE_CONTRACT, scope="agentic-install-agents"
            )
        )
        assert (
            validate_remote_contract(
                stack_metadata.SKILLS_INSTALL_REMOTE_CONTRACT,
                scope="agentic-install-skills-mcps",
            )
        )
        assert (
            validate_remote_contract(stack_metadata.UPDATE_REMOTE_CONTRACT, scope="agentic-update-stack")
        )

    def test_install_modules_reference_canonical_metadata(self) -> None:
        assert install_agents._REMOTE_INSTALL_CONTRACT is stack_metadata.AGENTS_INSTALL_REMOTE_CONTRACT
        assert install_skills_mcps._REMOTE_INSTALL_CONTRACT is stack_metadata.SKILLS_INSTALL_REMOTE_CONTRACT
        assert update_agentic_stack._REMOTE_INSTALL_CONTRACT is stack_metadata.UPDATE_REMOTE_CONTRACT

        assert install_agents.HERMES_INSTALL_URL == stack_metadata.HERMES_INSTALL_URL
        assert install_agents.OMP_INSTALL_URL == stack_metadata.OMP_INSTALL_URL
        assert install_agents.OPENAI_CODEX_PACKAGE == stack_metadata.OPENAI_CODEX_PACKAGE
        assert install_agents.CLAUDE_INSTALL_URL == stack_metadata.CLAUDE_INSTALL_URL
        assert install_skills_mcps.SKILL_AGENT_LOOKUP == stack_metadata.SKILL_AGENT_LOOKUP
        assert install_skills_mcps.SKILL_AGENT_CLI_NAMES == stack_metadata.SKILL_AGENT_CLI_NAMES
        assert install_skills_mcps.SKILL_AGENTS == stack_metadata.SKILL_AGENTS
        assert install_skills_mcps.SKILLS_CLI_PACKAGE == stack_metadata.SKILLS_CLI_PACKAGE
        assert install_skills_mcps.AGENTMEMORY_NPM_PACKAGE == stack_metadata.AGENTMEMORY_NPM_PACKAGE
        assert (
            install_skills_mcps.AGENTMEMORY_PI_INDEX_TS
            == stack_metadata.AGENTMEMORY_PI_INDEX_TS
        )
        assert install_skills_mcps.CODEBASE_MEMORY_INSTALL == stack_metadata.CODEBASE_MEMORY_INSTALL
        assert install_skills_mcps.LEAN_CTX_INSTALL_SCRIPT == stack_metadata.LEAN_CTX_INSTALL_SCRIPT
        assert (
            update_agentic_stack.AGENTMEMORY_NPM_PACKAGE
            == stack_metadata.AGENTMEMORY_NPM_PACKAGE
        )
        assert update_agentic_stack.OPENAI_CODEX_PACKAGE == stack_metadata.OPENAI_CODEX_PACKAGE
        assert update_agentic_stack.SKILLS_CLI_PACKAGE == stack_metadata.SKILLS_CLI_PACKAGE
        assert list(update_agentic_stack.UPDATE_STEPS) == list(stack_metadata.UPDATE_STEPS)

        assert configure_agent_mcps.AGENT_CHOICES == stack_metadata.CONFIGURE_AGENT_CHOICES

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

    def test_update_skills_and_codex_commands_use_canonical_packages(self) -> None:
        with patch("agentic_env.update_agentic_stack.cmd_exists") as cmd_exists:
            cmd_exists.side_effect = lambda name: True if name == "npm" else False
            with patch("agentic_env.update_agentic_stack.run") as run:
                assert update_agentic_stack._update_skills() is True
                run.assert_called_once_with(
                    [
                        "npx",
                        "--yes",
                        stack_metadata.SKILLS_CLI_PACKAGE,
                        "update",
                        "-g",
                        "-y",
                    ]
                )

        with patch("agentic_env.update_agentic_stack.cmd_exists") as cmd_exists:
            cmd_exists.side_effect = lambda name: True if name in {"codex", "npm"} else False
            with patch("agentic_env.update_agentic_stack.run") as run:
                assert update_agentic_stack._update_codex() is True
                run.assert_called_once_with(
                    ["npm", "update", "-g", stack_metadata.OPENAI_CODEX_PACKAGE]
                )


if __name__ == "__main__":
    unittest.main()
