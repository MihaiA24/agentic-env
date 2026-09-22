from __future__ import annotations

import fcntl
import json
import os
import pty
import re
import select
import struct
import sys
import tempfile
import termios
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

    @patch("agentic_env.install_skills_mcps.choose", return_value=[])
    def test_picker_rows_are_pre_checked_from_the_profile_or_from_skill(self, mock_choose) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None

        install_skills_mcps._pick_skills(manifest, [])
        rows = {row.value: row for row in mock_choose.call_args.args[1] if not isinstance(row, str)}
        self.assertTrue(rows["mattpocock/"].checked)
        self.assertFalse(rows["mattpocock/tdd"].checked)
        self.assertEqual(rows["mattpocock/tdd"].description, manifest.packs["mattpocock"].descriptions["tdd"])

        install_skills_mcps._pick_skills(manifest, ["tdd"])
        rows = {row.value: row for row in mock_choose.call_args.args[1] if not isinstance(row, str)}
        self.assertFalse(rows["mattpocock/"].checked)
        self.assertTrue(rows["mattpocock/tdd"].checked)
        self.assertFalse(rows["mattpocock/teach"].checked)

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    @patch("agentic_env.install_skills_mcps.interactive", return_value=True)
    @patch("agentic_env.install_skills_mcps.ask", return_value=True)
    @patch("agentic_env.install_skills_mcps.choose")
    def test_guided_main_installs_only_picked_skills_and_mcps(
        self,
        mock_choose,
        _mock_ask,
        _mock_interactive,
        mock_install_agentmemory,
        mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        mock_choose.side_effect = [
            ["mattpocock/tdd", "ponytail/ponytail"],
            ["claude"],
            ["agentmemory"],
        ]

        self.assertEqual(install_skills_mcps.main(["--verbose"]), 0)

        _, selection, agents = mock_install_skills.call_args.args
        self.assertEqual(selection, {"mattpocock": ["tdd"], "ponytail": ["ponytail"]})
        self.assertEqual(agents, ["claude"])
        mock_install_codebase_memory.assert_not_called()
        mock_install_agentmemory.assert_called_once()

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    @patch("agentic_env.install_skills_mcps.interactive", return_value=True)
    @patch("agentic_env.install_skills_mcps.ask", return_value=True)
    @patch("agentic_env.install_skills_mcps.choose")
    def test_guided_pack_row_installs_the_whole_roster(
        self,
        mock_choose,
        _mock_ask,
        _mock_interactive,
        _mock_install_agentmemory,
        _mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        """The `All of <pack>` row installs the pack roster, and it wins over the
        individual rows of the same pack."""
        mock_choose.side_effect = [["caveman/", "caveman/caveman"], ["claude"], []]

        self.assertEqual(install_skills_mcps.main([]), 0)

        _, selection, _ = mock_install_skills.call_args.args
        self.assertEqual(selection, {"caveman": ["caveman", "caveman-commit"]})

    @patch("agentic_env.install_skills_mcps._validate_remote_contract", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_skills", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_codebase_memory", return_value=True)
    @patch("agentic_env.install_skills_mcps._install_agentmemory", return_value=True)
    @patch("agentic_env.install_skills_mcps.interactive", return_value=True)
    @patch("agentic_env.install_skills_mcps.ask", return_value=True)
    @patch("agentic_env.install_skills_mcps.choose")
    def test_guided_skills_are_skipped_when_no_agent_is_picked(
        self,
        mock_choose,
        _mock_ask,
        _mock_interactive,
        _mock_install_agentmemory,
        _mock_install_codebase_memory,
        mock_install_skills,
        _mock_validate_remote_contract,
    ) -> None:
        mock_choose.side_effect = [["caveman/caveman"], [], []]

        self.assertEqual(install_skills_mcps.main([]), 0)
        mock_install_skills.assert_not_called()

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

    def test_replay_command_round_trips_or_reports_nothing(self) -> None:
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        replay = install_skills_mcps._replay_command

        self.assertEqual(
            replay(manifest, {"caveman": ["caveman"]}, ["claude"], False, True),
            "agentic-install-skills-mcps --skill-pack caveman --skill caveman"
            " --skill-agent claude --mcp agentmemory --yes",
        )
        self.assertEqual(
            replay(manifest, {}, ["claude"], True, True),
            "agentic-install-skills-mcps --all-mcps --yes",
        )
        # A pack that ships no roster takes everything it ships, so a `--skill`
        # filter needed by another pack would narrow it. That has no flag-only form.
        open_manifest = install_skills_mcps.SkillManifest(
            packs={
                "rostered": install_skills_mcps.SkillPack(
                    "rostered", "owner/rostered#v1", "rostered skills", ("tdd", "grilling")
                ),
                "open": install_skills_mcps.SkillPack("open", "owner/open#v1", "open skills", ()),
            },
            aliases={},
            profiles={},
        )
        self.assertIsNone(
            replay(open_manifest, {"rostered": ["tdd"], "open": []}, ["claude"], False, False)
        )
        self.assertEqual(
            replay(open_manifest, {"open": []}, ["claude"], False, False),
            "agentic-install-skills-mcps --skill-pack open --skill-agent claude --yes",
        )

    def test_guided_pty_run_with_everything_cleared_installs_nothing(self) -> None:
        """Drive the real pickers through a pseudo-terminal: clear every skill and
        MCP with `a`, confirm -> three skips, exit 0. Clearing the skills also
        drops the agent picker; installers are stubbed to fail if reached."""
        manifest = install_skills_mcps.load_skill_manifest(
            install_skills_mcps.SKILL_PACK_CONFIG_PATH
        )
        assert manifest is not None
        output, status = _run_in_pty(
            _GUIDED_CHILD,
            [
                # 4 pack rows start checked, so the first `a` selects all 36 rows
                # and the second clears them.
                (b"Select skills to install", b"aa\r"),
                (b"Select MCP tooling", b"a\r"),
            ],
        )
        text = re.sub(rb"\x1b\[[0-9;?]*[A-Za-z]", b"", output).decode("utf-8", "replace")

        self.assertEqual(status, 0, text)
        self.assertNotIn("INSTALL-CALLED", text)
        self.assertNotIn("which agents?", text)
        for line in ("skill packs: skipped", "codebase-memory-mcp: skipped", "agentmemory: skipped"):
            self.assertIn(line, text)
        for pack in manifest.packs.values():
            self.assertIn(pack.label, text)
            for skill in pack.skills:
                self.assertIn(skill, text)


# Runs `main([])` in a fresh interpreter behind the pty; any install call trips
# the sentinel so a picker regression cannot reach npm/skills.
_GUIDED_CHILD = """
from unittest.mock import patch
from agentic_env import install_skills_mcps as m
trip = {"side_effect": AssertionError("INSTALL-CALLED")}
with patch.object(m, "_validate_remote_contract", return_value=True), \\
     patch.object(m, "_install_skills", **trip), \\
     patch.object(m, "_install_codebase_memory", **trip), \\
     patch.object(m, "_install_agentmemory", **trip):
    raise SystemExit(m.main([]))
"""


def _run_in_pty(code: str, steps: list[tuple[bytes, bytes]], timeout: float = 30) -> tuple[bytes, int]:
    """Exec `python -c code` on a pseudo-terminal; for each (expect, send) wait
    until `expect` was printed, then type `send`. Returns (raw output, exit code)."""
    pid, fd = pty.fork()
    if pid == 0:
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 60, 120, 0, 0))
        os.environ["TERM"] = "xterm"
        os.execv(sys.executable, [sys.executable, "-c", code])

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
