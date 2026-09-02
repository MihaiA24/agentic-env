from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import install_skills_mcps


class InstallSkillsMcpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state = (
            install_skills_mcps._SKILL_PACKS,
            install_skills_mcps._SKILL_PACK_ALIASES,
            install_skills_mcps._SKILL_PACK_PROFILES,
        )

    def tearDown(self) -> None:
        (
            install_skills_mcps._SKILL_PACKS,
            install_skills_mcps._SKILL_PACK_ALIASES,
            install_skills_mcps._SKILL_PACK_PROFILES,
        ) = self._state

    def test_load_skill_pack_config_rejects_invalid_profiles_and_duplicates(self) -> None:
        invalid_profiles = {
            "packs": [
                {
                    "name": "mattpocock",
                    "source": "mattpocock/skills",
                }
            ],
            "profiles": {"default": ["missing"]},
        }
        invalid_duplicates = {
            "packs": [
                {
                    "name": "mattpocock",
                    "source": "mattpocock/skills",
                },
                {
                    "name": "mattpocock",
                    "source": "other/source",
                },
            ],
        }

        for payload in (invalid_profiles, invalid_duplicates):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "skill-packs.json"
                path.write_text(json.dumps(payload), encoding="utf-8")

                self.assertFalse(install_skills_mcps._load_skill_pack_config(path))
                self.assertEqual(install_skills_mcps._SKILL_PACKS, self._state[0])
                self.assertEqual(
                    install_skills_mcps._SKILL_PACK_ALIASES,
                    self._state[1],
                )
                self.assertEqual(
                    install_skills_mcps._SKILL_PACK_PROFILES,
                    self._state[2],
                )

    def test_parse_skill_selectors_resolves_aliases_and_validates_agents(self) -> None:
        payload = {
            "packs": [
                {
                    "name": "mattpocock",
                    "source": "mattpocock/skills",
                    "label": "mattpocock skills",
                    "aliases": ["mattpocock", "mattpocock/skills"],
                },
                {
                    "name": "ponytail",
                    "source": "DietrichGebert/ponytail",
                    "label": "ponytail skill",
                    "aliases": ["ponytail", "dietrichgebert/ponytail"],
                },
            ],
            "profiles": {"default": ["mattpocock", "ponytail"]},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "skill-packs.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertTrue(install_skills_mcps._load_skill_pack_config(path))

            pack_selection = install_skills_mcps._parse_skill_packs(
                ["mattpocock", "dietrichgebert/ponytail", "missing"]
            )
            self.assertEqual(
                pack_selection.selected,
                ("mattpocock", "ponytail"),
            )
            self.assertEqual(pack_selection.unknown, ("missing",))

            agent_selection = install_skills_mcps._parse_skill_agents([
                "hermes,claude,ghost"
            ])
            self.assertEqual(agent_selection.selected, ("hermes", "claude"))
            self.assertEqual(agent_selection.unknown, ("ghost",))

            skill_names = install_skills_mcps._parse_skill_names(["tdd,wayfinder", "tdd"])
            self.assertEqual(skill_names.selected, ("tdd", "wayfinder"))

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills")
    @patch("agentic_env.install_skills_mcps._install_codebase_memory")
    @patch("agentic_env.install_skills_mcps._install_agentmemory")
    def test_main_with_unknown_skill_pack_selection_aborts_without_installs(
        self,
        mock_install_agentmemory,
        mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        result = install_skills_mcps.main(["--skill-pack", "does-not-exist", "--yes"])

        self.assertEqual(result, 1)
        mock_install_skills.assert_not_called()
        mock_install_codebase_memory.assert_not_called()
        mock_install_agentmemory.assert_not_called()

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills")
    @patch("agentic_env.install_skills_mcps._install_codebase_memory")
    @patch("agentic_env.install_skills_mcps._install_agentmemory")
    def test_build_plan_skips_invalid_skill_agents(
        self,
        mock_install_agentmemory,
        mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        result = install_skills_mcps.main(["--skill-agent", "nope", "--yes"])

        self.assertEqual(result, 1)
        mock_install_skills.assert_not_called()
        mock_install_codebase_memory.assert_not_called()
        mock_install_agentmemory.assert_not_called()

    @patch("agentic_env.install_skills_mcps._configure_hermes_agentmemory", return_value=True)
    @patch("agentic_env.install_skills_mcps.cmd_version_matches")
    @patch("agentic_env.install_skills_mcps._install_npm_global", return_value=True)
    @patch("agentic_env.install_skills_mcps.cmd_exists", return_value=True)
    def test_install_agentmemory_only_configures_hermes(
        self,
        _mock_cmd_exists,
        _mock_install_npm_global,
        _mock_version_matches,
        mock_configure_hermes,
    ) -> None:
        _mock_version_matches.side_effect = [False, True]
        self.assertTrue(install_skills_mcps._install_agentmemory(non_interactive=True))

        mock_configure_hermes.assert_called_once_with()



if __name__ == "__main__":
    unittest.main()
