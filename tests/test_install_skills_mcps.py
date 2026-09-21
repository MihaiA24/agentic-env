from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import install_skills_mcps


class InstallSkillsMcpsTests(unittest.TestCase):

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

                self.assertIsNone(install_skills_mcps.load_skill_manifest(path))

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
            manifest = install_skills_mcps.load_skill_manifest(path)
            assert manifest is not None

            pack_selection = install_skills_mcps._parse_skill_packs(
                ["mattpocock", "dietrichgebert/ponytail", "missing"], manifest
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

    def test_vendored_pack_skills_exist_at_resolved_source(self) -> None:
        """A `./` source must resolve inside the package and carry every
        roster skill; a bad re-copy would otherwise fail only at install time."""
        manifest = install_skills_mcps.load_skill_manifest(install_skills_mcps._SKILL_PACK_CONFIG_PATH)
        assert manifest is not None
        vendored = [pack for pack in manifest.packs.values() if pack.source.startswith("./")]
        self.assertTrue(vendored)
        for pack in vendored:
            source = Path(manifest.source(pack.name))
            self.assertTrue(source.is_absolute())
            self.assertTrue(source.is_relative_to(install_skills_mcps._SKILL_PACK_CONFIG_PATH.parent))
            missing = [s for s in pack.skills if not (source / s / "SKILL.md").is_file()]
            self.assertEqual(missing, [], f"{pack.name}: roster skills missing from {source}")

    def test_npx_skills_floor_is_checked_before_installing(self) -> None:
        floor = install_skills_mcps.STACK_VERSION_FLOORS["skills"]
        for version, status, expected in (
            ("0.0.0", 0, False),
            ("unknown", 0, False),
            (floor, 1, False),
            (floor, 0, True),
            ("999.0.0", 0, True),
        ):
            with self.subTest(version=version, status=status), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                npx = root / "npx"
                npx.write_text(
                    f"#!{sys.executable}\n"
                    "import os, sys\n"
                    "from pathlib import Path\n"
                    "if '--version' in sys.argv:\n"
                    "    print(os.environ['SKILLS_TEST_VERSION'])\n"
                    "    sys.exit(int(os.environ['SKILLS_TEST_STATUS']))\n"
                    "Path(__file__).with_name('installed').touch()\n",
                    encoding="utf-8",
                )
                npx.chmod(0o755)
                (root / "npm").symlink_to(npx)
                with patch.dict(os.environ, {
                    "PATH": temp,
                    "SKILLS_TEST_VERSION": version,
                    "SKILLS_TEST_STATUS": str(status),
                }):
                    result = install_skills_mcps._install_skill_package(
                        "example/pack#v1", ["example"], ["claude"]
                    )
                self.assertEqual(result, expected)
                self.assertEqual((root / "installed").exists(), expected)

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
    @patch("agentic_env.install_skills_mcps.cmd_version_at_least")
    @patch("agentic_env.install_skills_mcps._install_npm_global", return_value=True)
    @patch("agentic_env.install_skills_mcps.cmd_exists", return_value=True)
    def test_install_agentmemory_only_configures_hermes(
        self,
        _mock_cmd_exists,
        _mock_install_npm_global,
        _mock_version_at_least,
        mock_configure_hermes,
    ) -> None:
        _mock_version_at_least.side_effect = [False, True]
        self.assertTrue(install_skills_mcps._install_agentmemory(non_interactive=True))

        mock_configure_hermes.assert_called_once_with()



if __name__ == "__main__":
    unittest.main()
