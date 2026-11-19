from __future__ import annotations

import dataclasses
import fcntl
import json
import os
import pty
import re
import select
import shlex
import shutil
import struct
import sys
import tempfile
import termios
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import install_skills_mcps, skill_lock


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
            self.assertEqual(skill_names, ("tdd", "wayfinder"))

    def test_vendored_pack_skills_exist_at_resolved_source(self) -> None:
        """A `./` source must resolve inside the package and carry every
        roster skill; a bad re-copy would otherwise fail only at install time."""
        manifest = install_skills_mcps.load_skill_manifest(install_skills_mcps.SKILL_PACK_CONFIG_PATH)
        assert manifest is not None
        vendored = [pack for pack in manifest.packs.values() if pack.source.startswith("./")]
        self.assertTrue(vendored)
        for pack in vendored:
            source = Path(manifest.source(pack.name))
            self.assertTrue(source.is_absolute())
            self.assertTrue(source.is_relative_to(install_skills_mcps.SKILL_PACK_CONFIG_PATH.parent))
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
                        "example/pack#v1", ["example"], ("claude",)
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

    def test_upstream_is_explicit_or_derived_from_a_pinned_remote_source(self) -> None:
        def load(*packs: dict) -> install_skills_mcps.SkillManifest | None:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "skill-packs.json"
                path.write_text(json.dumps({"packs": list(packs)}), encoding="utf-8")
                return install_skills_mcps.load_skill_manifest(path)

        manifest = load(
            {"name": "vendored", "source": "./v", "upstream": {"repo": "o/mono", "ref": "abc", "path": "p"}},
            {"name": "pinned", "source": "Owner/repo#v1", "upstream": {"path": "skills"}},
            {"name": "repo-override", "source": "owner/alternate#v1", "upstream": {"repo": "owner/other"}},
            {"name": "ref-override", "source": "owner/repo", "upstream": {"ref": "abc"}},
            {"name": "unpinned", "source": "owner/unpinned"},
            {"name": "local", "source": "./local"},
        )
        assert manifest is not None
        Upstream = install_skills_mcps.SkillUpstream
        self.assertEqual(
            {name: pack.upstream for name, pack in manifest.packs.items()},
            {
                "vendored": Upstream("o/mono", "abc", "p"),
                "pinned": Upstream("Owner/repo", "v1", "skills"),
                "repo-override": Upstream("owner/other", "v1"),
                "ref-override": Upstream("owner/repo", "abc"),
                "unpinned": None,
                "local": None,
            },
        )
        self.assertEqual(manifest.source("pinned"), "Owner/repo#v1")

        for source, upstream in (
            ("./vendored", {"repo": "owner/other"}),
            ("./vendored", {"ref": "abc"}),
            ("./vendored", {"path": "skills"}),
            ("owner/unpinned", {"path": "skills"}),
        ):
            with self.subTest(source=source, upstream=upstream):
                partial = load({"name": "pack", "source": source, "upstream": upstream})
                assert partial is not None
                self.assertEqual(partial.source("pack"), str((partial.config_path.parent / source[2:]).resolve()) if source.startswith("./") else source)
                self.assertIsNone(partial.packs["pack"].upstream)

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    def test_explicit_selection_matching_no_skills_fails_without_installing(
        self,
        _mock_install_agentmemory,
        _mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        for argv in (
            ["--skill-pack", "caveman", "--skill", "tdd"],
            ["--skill", "tdd"],
            ["--skills-dir", "skills"],
        ):
            with self.subTest(argv=argv):
                self.assertEqual(install_skills_mcps.main([*argv, "--yes"]), 1)
                mock_install_skills.assert_not_called()

        self.assertEqual(
            install_skills_mcps.main(["--skill-pack", "caveman,mattpocock", "--skill", "tdd", "--yes"]),
            0,
        )
        mock_install_skills.assert_called_once()

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    def test_partially_unknown_skill_names_abort_before_any_install(
        self, mock_agentmemory, mock_codebase, mock_install_skills, _contract
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for target in (["--all-mcps"], ["--skills-dir", temp]):
                with self.subTest(target=target):
                    argv = ["--skill-pack", "caveman,mattpocock", "--skill", "tdd,tddd", *target]
                    self.assertEqual(install_skills_mcps.main([*argv, "--yes"]), 1)
                    mock_install_skills.assert_not_called()
                    mock_codebase.assert_not_called()
                    mock_agentmemory.assert_not_called()

            # A pack without a roster cannot vouch for names, so they are forwarded.
            config = Path(temp) / "skill-packs.json"
            config.write_text(
                json.dumps({"packs": [
                    {"name": "rostered", "source": "o/r#v1", "aliases": ["rostered"], "skills": ["tdd"]},
                    {"name": "open", "source": "o/open#v1", "aliases": ["open"]},
                ]}),
                encoding="utf-8",
            )
            argv = ["--skill-config", str(config), "--skill-pack", "rostered,open", "--skill", "tdd,custom"]
            self.assertEqual(install_skills_mcps.main([*argv, "--yes"]), 0)
            self.assertEqual(
                mock_install_skills.call_args.args[1], {"rostered": ["tdd"], "open": ["tdd", "custom"]}
            )

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    def test_failing_skills_cli_fails_the_run_but_mcps_still_install(
        self, mock_agentmemory, mock_codebase, _contract
    ) -> None:
        floor = install_skills_mcps.STACK_VERSION_FLOORS["skills"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skills = root / "bin" / "skills"
            skills.parent.mkdir()
            skills.write_text(
                f"#!{sys.executable}\n"
                "import sys\n"
                "if '--version' in sys.argv:\n"
                f"    print('{floor}')\n"
                "    sys.exit(0)\n"
                "sys.exit('add failed')\n",
                encoding="utf-8",
            )
            skills.chmod(0o755)
            destination = root / "skills"
            with patch.dict(os.environ, {"PATH": str(skills.parent)}):
                argv = ["--skill-pack", "caveman", "--all-mcps", "--yes"]
                self.assertEqual(install_skills_mcps.main(argv), 1)
                mock_codebase.assert_called_once()
                mock_agentmemory.assert_called_once()

                argv = ["--skill-pack", "caveman", "--skills-dir", str(destination), "--yes"]
                self.assertEqual(install_skills_mcps.main(argv), 1)
            self.assertFalse(destination.exists())

    def test_resolve_pack_skills_intersects_rosters_and_passes_whole_packs(self) -> None:
        manifest = install_skills_mcps.SkillManifest(
            packs={
                "rostered": install_skills_mcps.SkillPack(
                    "rostered", "owner/rostered#v1", "rostered skills", ("tdd", "grilling")
                ),
                "open": install_skills_mcps.SkillPack(
                    "open", "owner/open#v1", "open skills", ()
                ),
            },
            aliases={},
            profiles={},
        )
        resolve = install_skills_mcps._resolve_pack_skills

        self.assertEqual(
            resolve(manifest, ["rostered", "open"], ["tdd"]),
            {"rostered": ["tdd"], "open": ["tdd"]},
        )
        self.assertEqual(resolve(manifest, ["rostered"], ["absent"]), {})
        self.assertEqual(
            resolve(manifest, ["rostered", "open"], []),
            {"rostered": ["tdd", "grilling"], "open": []},
        )

    @patch("agentic_env.install_skills_mcps.choose", return_value=["caveman/", "caveman/caveman"])
    def test_picker_pack_row_overrides_individual_rows(self, _choose) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        self.assertEqual(
            install_skills_mcps._pick_skills(manifest, []),
            {"caveman": ["caveman", "caveman-commit"]},
        )

    def test_guided_skills_are_skipped_when_no_agent_is_picked(self) -> None:
        output, status = _run_in_pty(
            _GUIDED_CHILD,
            [
                (b"Select skills to install", b"\r"),
                (b"Install skills where?", b"\r"),
                (b"Install skills for which agents?", b"a\r"),
                (b"Select MCP tooling", b"a\r"),
                (b"recommended agent rules", b"n\r"),
            ],
            argv=["--skill", "tdd"],
        )
        self.assertEqual(status, 0, output.decode("utf-8", "replace"))
        self.assertNotIn(b"INSTALL-CALLED", output)

    def test_guided_custom_directory_installs_assets_after_rejecting_blank_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "another project's skills"
            output, status = _run_in_pty(
                _DIRECTORY_CHILD,
                [
                    (b"Select skills to install", b"\r"),
                    (b"Install skills where?", b"\x1b[B\r"),
                    (b"Skills directory (exact folder)", b"\r"),
                    (b"Enter a skills directory", str(destination).encode() + b"\r"),
                    (b"Install this selection", b"y\r"),
                ],
                argv=["--skill", "writing-for-agents"],
            )
            self.assertEqual(status, 0, output.decode("utf-8", "replace"))
            self.assertEqual({path.name for path in destination.iterdir()}, {"writing-for-agents"})
            source = (
                install_skills_mcps.SKILL_PACK_CONFIG_PATH.parent
                / "vendored/mattpocock/skills/writing-for-agents"
            )
            for name in ("SKILL.md", "SKILL-MECHANICS.md"):
                self.assertEqual(
                    (destination / "writing-for-agents" / name).read_bytes(),
                    (source / name).read_bytes(),
                )
            self.assertNotIn(b"Select MCP tooling", output)
            self.assertNotIn(b"Install skills for which agents?", output)

    def test_guided_destination_cancellation_never_installs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "not installed"
            select_skills = (b"Select skills to install", b"\r")
            select_custom = (b"Install skills where?", b"\x1b[B\r")
            for steps, expected in (
                ([select_skills, (b"Install skills where?", b"\x03")], 130),
                (
                    [select_skills, select_custom, (b"Skills directory (exact folder)", b"\x03")],
                    130,
                ),
                (
                    [
                        select_skills,
                        select_custom,
                        (b"Skills directory (exact folder)", str(destination).encode() + b"\r"),
                        (b"Install this selection", b"n\r"),
                    ],
                    0,
                ),
            ):
                with self.subTest(steps=steps):
                    output, status = _run_in_pty(_GUIDED_CHILD, steps, argv=["--skill", "tdd"])
                    self.assertEqual(status, expected, output.decode("utf-8", "replace"))
                    self.assertNotIn(b"INSTALL-CALLED", output)
                    self.assertFalse(destination.exists())

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    @patch("agentic_env.install_skills_mcps.interactive", return_value=False)
    @patch("agentic_env.install_skills_mcps.choose")
    def test_without_a_terminal_and_without_flags_nothing_is_installed(
        self,
        mock_choose,
        _mock_interactive,
        mock_install_agentmemory,
        mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        """A piped run without `--yes` used to take every pre-checked row and
        install the whole default profile."""
        self.assertEqual(install_skills_mcps.main([]), 0)

        mock_choose.assert_not_called()
        mock_install_skills.assert_not_called()
        mock_install_codebase_memory.assert_not_called()
        mock_install_agentmemory.assert_not_called()

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    def test_mcp_flag_installs_one_server(
        self,
        mock_install_agentmemory,
        mock_install_codebase_memory,
        _mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        self.assertEqual(install_skills_mcps.main(["--mcp", "agentmemory", "--yes"]), 0)
        mock_install_agentmemory.assert_called_once()
        mock_install_codebase_memory.assert_not_called()

        self.assertEqual(install_skills_mcps.main(["--mcp", "nope", "--yes"]), 1)

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    def test_agent_rules_flag_writes_the_managed_file_and_keeps_a_backup(self, _validate) -> None:
        source = install_skills_mcps.AGENT_RULES_SOURCE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / ".agents" / "AGENTS.md"
            backup = target.with_name("AGENTS.md.agentic-env.bak")
            with patch.object(install_skills_mcps, "AGENT_RULES_PATH", target):
                self.assertEqual(install_skills_mcps.main(["--agent-rules", "--yes"]), 0)
                self.assertEqual(target.read_text(encoding="utf-8"), source)

                # Current content is left alone, so it never becomes its own backup.
                self.assertEqual(install_skills_mcps.main(["--agent-rules", "--yes"]), 0)
                self.assertFalse(backup.exists())

                target.write_bytes("my own rules \u00e9\n".encode("latin-1"))
                self.assertEqual(install_skills_mcps.main(["--yes"]), 0)
                self.assertEqual(target.read_bytes(), "my own rules \u00e9\n".encode("latin-1"))

                self.assertEqual(install_skills_mcps.main(["--agent-rules", "--yes"]), 0)
                self.assertEqual(target.read_text(encoding="utf-8"), source)
                self.assertEqual(backup.read_bytes(), "my own rules \u00e9\n".encode("latin-1"))

                # Updating the managed file must not replace the user's backup.
                newer = Path(temp) / "newer.md"
                newer.write_text(source + "\nA newer rule.\n", encoding="utf-8")
                with patch.object(install_skills_mcps, "AGENT_RULES_SOURCE", newer):
                    self.assertEqual(install_skills_mcps.main(["--agent-rules", "--yes"]), 0)
                self.assertEqual(target.read_text(encoding="utf-8"), source + "\nA newer rule.\n")
                self.assertEqual(backup.read_bytes(), "my own rules \u00e9\n".encode("latin-1"))

    def test_directory_install_copies_assets_and_refuses_collisions_before_writing(self) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None

        def stage(source, skills, directory):
            for skill in skills:
                shutil.copytree(Path(source) / skill, directory / ".agents" / "skills" / skill)
            return True

        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(install_skills_mcps, "_install_skill_package", side_effect=stage),
        ):
            destination = Path(temp) / "project skills"
            destination.mkdir()
            unrelated = destination / "notes.txt"
            unrelated.write_text("keep me", encoding="utf-8")
            install = install_skills_mcps._install_skill_directory
            self.assertTrue(install(manifest, {"mattpocock": ["writing-for-agents"]}, destination))
            installed = destination / "writing-for-agents"
            source = Path(manifest.source("mattpocock")) / "writing-for-agents"
            for name in ("SKILL.md", "SKILL-MECHANICS.md"):
                self.assertEqual((installed / name).read_bytes(), (source / name).read_bytes())
            (installed / "SKILL.md").write_text("local changes", encoding="utf-8")

            selection = {"mattpocock": ["tdd", "writing-for-agents"]}
            self.assertFalse(install(manifest, selection, destination))
            self.assertFalse((destination / "tdd").exists())
            self.assertEqual((installed / "SKILL.md").read_text(), "local changes")

            shutil.rmtree(installed)
            installed.symlink_to(destination / "missing")
            self.assertFalse(install(manifest, selection, destination))
            self.assertTrue(installed.is_symlink())
            self.assertFalse((destination / "missing").exists())
            self.assertFalse((destination / "tdd").exists())
            self.assertEqual(unrelated.read_text(), "keep me")

    def test_directory_mode_rejects_global_agent_and_mcp_selections(self) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        for conflicting in (
            ["--skill-agent", "claude"], ["--mcp", "agentmemory"], ["--all-mcps"], ["--agent-rules"]
        ):
            with self.subTest(conflicting=conflicting):
                args = install_skills_mcps._parse(["--skills-dir", "skills", *conflicting])
                self.assertIsNone(
                    install_skills_mcps._build_install_plan(args, manifest)
                )

    def test_replay_command_round_trips_or_reports_nothing(self) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        replay = install_skills_mcps._replay_command

        def assert_replays(manifest, selection, destination, codebase, agentmemory):
            command = replay(manifest, selection, destination, codebase, agentmemory)
            assert command is not None
            args = install_skills_mcps._parse(shlex.split(command)[1:])
            plan = install_skills_mcps._build_install_plan(args, manifest)
            assert plan is not None
            self.assertEqual(
                install_skills_mcps._resolve_pack_skills(
                    manifest, list(plan.skill_packs), list(plan.skill_names)
                ),
                selection,
            )
            if selection:
                expected = destination.resolve() if isinstance(destination, Path) else destination
                self.assertEqual(plan.destination, expected)
                self.assertEqual(Path(args.skill_config).resolve(), manifest.config_path.resolve())
            self.assertEqual((plan.do_codebase, plan.do_agentmemory), (codebase, agentmemory))

        assert_replays(manifest, {"caveman": ["caveman"]}, ("claude",), False, True)
        assert_replays(manifest, {}, ("claude",), True, True)
        assert_replays(
            manifest,
            {"mattpocock": ["tdd"]},
            Path("/tmp/another project's skills"),
            False,
            False,
        )
        with_rules = replay(manifest, {}, ("claude",), False, True, True)
        assert with_rules is not None
        rules_plan = install_skills_mcps._build_install_plan(
            install_skills_mcps._parse(shlex.split(with_rules)[1:]), manifest
        )
        assert rules_plan is not None
        self.assertEqual((rules_plan.do_agentmemory, rules_plan.do_agent_rules), (True, True))

        # A pack that ships no roster takes everything it ships, so a `--skill`
        # filter needed by another pack would narrow it. That has no flag-only form.
        open_manifest = install_skills_mcps.SkillManifest(
            packs={
                "rostered": install_skills_mcps.SkillPack(
                    "rostered", "owner/rostered#v1", "rostered skills", ("tdd", "grilling")
                ),
                "open": install_skills_mcps.SkillPack("open", "owner/open#v1", "open skills", ()),
            },
            aliases={"rostered": "rostered", "open": "open"},
            profiles={},
            config_path=Path("my project's manifest.json"),
        )
        self.assertIsNone(
            replay(open_manifest, {"rostered": ["tdd"], "open": []}, ("claude",), False, False)
        )
        assert_replays(open_manifest, {"open": []}, ("claude",), False, False)

    def test_guided_pty_run_with_everything_cleared_installs_nothing(self) -> None:
        """Drive the real pickers through a pseudo-terminal: clear every skill and
        MCP with `a`, decline the agent rules -> four skips, exit 0. Clearing the
        skills also drops the agent picker; installers are stubbed to fail if reached."""
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        output, status = _run_in_pty(
            _GUIDED_CHILD,
            [
                # The first `a` selects all rows; the second clears them.
                (b"Select skills to install", b"aa\r"),
                (b"Select MCP tooling", b"a\r"),
                (b"recommended agent rules", b"n\r"),
            ],
        )
        text = re.sub(rb"\x1b\[[0-9;?]*[A-Za-z]", b"", output).decode("utf-8", "replace")

        self.assertEqual(status, 0, text)
        self.assertNotIn("INSTALL-CALLED", text)
        self.assertNotIn("which agents?", text)
        for line in (
            "skill packs: skipped", "codebase-memory-mcp: skipped",
            "agentmemory: skipped", "agent rules: skipped",
        ):
            self.assertIn(line, text)
        for pack in manifest.packs.values():
            self.assertIn(pack.label, text)
            for skill in pack.skills:
                self.assertIn(skill, text)


# Expected values from skills 1.9.0 `computeSkillFolderHash` and from
# `git rev-parse <tree>:skill` over the same files (without the CLI-excluded ones).
_FIXTURE_FOLDER_HASH = "c55cb91c2c55277286295d3b4f543e0fe9aa3f8cc8fdc6734ab1a1f1eb6fb479"
_FIXTURE_TREE_ID = "195fee8a05f7ddd26d1b8d2440629e1b911eb64f"


def _skill_fixture(folder: Path, *, cli_excluded: bool) -> Path:
    (folder / "refs").mkdir(parents=True)
    (folder / "empty").mkdir()
    (folder / "SKILL.md").write_bytes(b"---\r\nname: demo\r\n---\r\nBody\r\n")
    (folder / "refs" / "guide.md").write_bytes(b"guide\n")
    script = folder / "run.sh"
    script.write_bytes(b"#!/bin/sh\necho hi\n")
    script.chmod(0o755)
    if cli_excluded:
        (folder / "metadata.json").write_bytes(b'{"x":1}')
        (folder / ".git").mkdir()
        (folder / ".git" / "HEAD").write_bytes(b"ref\n")
    return folder


class ConvergeTests(unittest.TestCase):
    """`--converge` against a temporary skills lock and canonical store."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = self.root / "skills"
        for active in (
            patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}),
            patch.object(skill_lock, "CANONICAL_SKILL_ROOT", self.store),
            # No global skills binary: nothing to self-update.
            patch.object(install_skills_mcps, "cmd_exists", lambda name: name != "skills"),
        ):
            active.start()
            self.addCleanup(active.stop)
        self.manifest = install_skills_mcps.SkillManifest(
            packs={
                "local": install_skills_mcps.SkillPack(
                    "local", "./vendored/local/skills", "local skills", ("tdd", "grilling")
                ),
                "remote": install_skills_mcps.SkillPack(
                    "remote", "Owner/Remote#v1", "remote skills", ("caveman",)
                ),
            },
            aliases={"local": "local", "remote": "remote"},
            profiles={"default": ("local",)},
            config_path=self.root / "site-packages" / "agentic_env" / "skill-packs.json",
        )

    def write_lock(self, skills: dict[str, dict]) -> None:
        path = skill_lock.lock_path()
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"version": 3, "skills": skills}), encoding="utf-8")

    def converge(self, *, prompt: bool, picked: list[str] | None = None) -> tuple[int, dict]:
        """Run the converge flow with stubbed installers; returns (status, selection)."""
        plan = install_skills_mcps._build_install_plan(
            install_skills_mcps._parse(
                ["--converge", "--skill-profile", "default", "--skill-agent", "claude"]
            ),
            self.manifest,
        )
        assert plan is not None
        choose = (
            patch.object(install_skills_mcps, "choose", return_value=picked)
            if picked is not None
            else patch.object(install_skills_mcps, "choose", side_effect=AssertionError("prompted"))
        )
        with choose, patch.object(install_skills_mcps, "_install_skills", return_value=True) as install:
            status = install_skills_mcps._converge(self.manifest, plan, prompt=prompt)
        return status, install.call_args.args[1] if install.called else {}

    def test_manifest_dropped_skills_must_have_left_every_roster(self) -> None:
        base = {"packs": [{"name": "p", "source": "owner/p#v1", "skills": ["tdd"]}]}
        for dropped, expected in (
            (["old", " old "], ("old",)),
            (["tdd"], None),
            ([""], None),
            ("old", None),
        ):
            with self.subTest(dropped=dropped):
                path = self.root / "skill-packs.json"
                path.write_text(json.dumps({**base, "dropped": dropped}), encoding="utf-8")
                manifest = install_skills_mcps.load_skill_manifest(path)
                self.assertEqual(manifest and manifest.dropped, expected)

    def test_existing_host_refreshes_its_skills_and_is_offered_the_rest_once(self) -> None:
        self.write_lock({"tdd": {"source": "anything"}})

        status, selection = self.converge(prompt=True, picked=["local/grilling"])
        self.assertEqual(status, 0)
        self.assertEqual(selection, {"local": ["tdd", "grilling"]})
        self.assertEqual(skill_lock.offered(), {"grilling", "caveman"})
        self.assertIn("tdd", skill_lock.load_lock())

        # Declined (caveman) and accepted (grilling) alike are never offered again.
        status, selection = self.converge(prompt=True)
        self.assertEqual((status, selection), (0, {"local": ["tdd"]}))

    def test_new_host_takes_the_profile_and_records_no_offer_without_a_prompt(self) -> None:
        status, selection = self.converge(prompt=False)

        self.assertEqual((status, selection), (0, {"local": ["tdd", "grilling"]}))
        self.assertFalse(skill_lock.lock_path().exists())
        # Once offered, a host holding no roster skill is not new: it keeps none.
        self.assertEqual(
            install_skills_mcps._converge_selection(self.manifest, ("local",), {}, {"tdd"}),
            ({}, ["grilling", "caveman"]),
        )

    def test_interrupted_offer_installs_and_records_nothing(self) -> None:
        self.write_lock({"tdd": {"source": "anything"}})
        with (
            patch.object(install_skills_mcps, "choose", side_effect=SystemExit(130)),
            patch.object(install_skills_mcps, "_install_skills") as install,
            self.assertRaises(SystemExit),
        ):
            install_skills_mcps._converge(
                self.manifest,
                install_skills_mcps._build_install_plan(
                    install_skills_mcps._parse(["--converge"]), self.manifest
                ),
                prompt=True,
            )
        install.assert_not_called()
        self.assertEqual(skill_lock.offered(), set())

    def test_prune_removes_only_unedited_dropped_skills_from_curated_packs(self) -> None:
        vendored = str(self.root / "other-python" / "agentic_env" / "vendored" / "local" / "skills")
        records = {}
        for name, source in (
            ("old-local", vendored),
            ("old-remote", "owner/remote"),
            ("edited", vendored),
            ("foreign", "someone/else"),
            ("lookalike", "/elsewhere/vendored/local/skills"),
        ):
            _skill_fixture(self.store / name, cli_excluded=False)
            records[name] = {"source": source, "skillFolderHash": _FIXTURE_FOLDER_HASH}
        (self.store / "edited" / "SKILL.md").write_text("mine\n", encoding="utf-8")
        _skill_fixture(self.store / "untracked", cli_excluded=False)
        self.write_lock(records)
        manifest = dataclasses.replace(self.manifest, dropped=(*records, "untracked", "absent"))

        with (
            patch.object(install_skills_mcps, "_skills_cli", return_value=["skills"]),
            patch.object(install_skills_mcps, "run") as run,
        ):
            self.assertTrue(install_skills_mcps._prune_dropped(manifest))
        run.assert_called_once_with(["skills", "remove", "old-local", "old-remote", "--global", "--yes"])

    def test_lock_hashes_match_what_the_cli_and_git_record(self) -> None:
        local = _skill_fixture(self.root / "local", cli_excluded=True)
        remote = _skill_fixture(self.root / "remote", cli_excluded=False)
        local_record = {"skillFolderHash": _FIXTURE_FOLDER_HASH}

        self.assertTrue(skill_lock.matches_record(local, local_record))
        self.assertTrue(skill_lock.matches_record(remote, {"skillFolderHash": _FIXTURE_TREE_ID}))
        (local / "refs" / "guide.md").write_bytes(b"edited\n")
        self.assertFalse(skill_lock.matches_record(local, local_record))
        self.assertFalse(skill_lock.matches_record(self.root / "absent", local_record))

    def test_update_skills_cli_installs_the_latest_global_binary(self) -> None:
        with (
            patch.object(install_skills_mcps, "cmd_exists", return_value=True),
            patch.object(install_skills_mcps, "cmd_version_at_least", return_value=True),
            patch.object(install_skills_mcps, "run") as run,
        ):
            self.assertTrue(install_skills_mcps._update_skills_cli())
        run.assert_called_once_with(["npm", "install", "-g", install_skills_mcps.SKILLS_CLI_PACKAGE])


# Runs `main` in a fresh interpreter behind the pty; any install call trips
# the sentinel so a picker regression cannot reach npm/skills.
_GUIDED_CHILD = """
import sys
from unittest.mock import patch
from agentic_env import install_skills_mcps as m
trip = {"side_effect": AssertionError("INSTALL-CALLED")}
with patch.object(m, "_validate_remote_contract", return_value=True), \\
     patch.object(m, "_install_skills", **trip), \\
     patch.object(m, "_install_codebase_memory", **trip), \\
     patch.object(m, "_install_agent_rules", **trip), \\
     patch.object(m, "_install_agentmemory", **trip):
    raise SystemExit(m.main(sys.argv[1:]))
"""

_DIRECTORY_CHILD = """
import shutil, sys
from pathlib import Path
from unittest.mock import patch
from agentic_env import install_skills_mcps as m
def stage(source, skills, directory):
    for skill in skills:
        shutil.copytree(Path(source) / skill, directory / ".agents" / "skills" / skill)
    return True
trip = {"side_effect": AssertionError("MCP-INSTALL-CALLED")}
with patch.object(m, "cmd_exists", return_value=True), \\
     patch.object(m, "_install_skill_package", side_effect=stage), \\
     patch.object(m, "_install_codebase_memory", **trip), \\
     patch.object(m, "_install_agentmemory", **trip):
    raise SystemExit(m.main(sys.argv[1:]))
"""


def _run_in_pty(
    code: str,
    steps: list[tuple[bytes, bytes]],
    timeout: float = 30,
    *,
    argv: list[str] | None = None,
) -> tuple[bytes, int]:
    """Exec `python -c code` on a pseudo-terminal; for each (expect, send) wait
    until `expect` was printed, then type `send`. Returns (raw output, exit code)."""
    pid, fd = pty.fork()
    if pid == 0:
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 60, 120, 0, 0))
        os.environ["TERM"] = "xterm"
        os.execv(sys.executable, [sys.executable, "-c", code, *(argv or [])])

    output = b""

    def read_until(expect: bytes | None) -> None:
        nonlocal output
        deadline = os.times().elapsed + timeout
        while expect is None or expect not in output:
            ready, _, _ = select.select([fd], [], [], max(0.0, deadline - os.times().elapsed))
            if not ready:
                raise AssertionError(f"timed out waiting for {expect!r}\n{output.decode('utf-8', 'replace')}")
            try:
                chunk = os.read(fd, 4096)
            except OSError:  # Linux raises EIO at EOF; macOS returns b""
                chunk = b""
            if not chunk:
                if expect is None:
                    return
                raise AssertionError(f"child exited before {expect!r}\n{output.decode('utf-8', 'replace')}")
            output += chunk

    try:
        for expect, send in steps:
            read_until(expect)
            os.write(fd, send)
        read_until(None)
    finally:
        os.close(fd)
        _, status = os.waitpid(pid, 0)
    return output, os.waitstatus_to_exitcode(status)



if __name__ == "__main__":
    unittest.main()
