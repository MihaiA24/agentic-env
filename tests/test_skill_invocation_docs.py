from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "agentic_env" / "vendored"


def manual_flags(skills_dir: Path) -> dict[str, bool]:
    """Skill name -> True when its frontmatter sets disable-model-invocation: true."""
    return {
        skill.parent.name: re.search(
            r"^disable-model-invocation:\s*true\s*$",
            skill.read_text(encoding="utf-8").split("---", 2)[1],
            re.MULTILINE,
        ) is not None
        for skill in skills_dir.glob("*/SKILL.md")
    }


MATT = manual_flags(VENDORED / "mattpocock" / "skills")
PSTACK = manual_flags(VENDORED / "pstack" / "skills")
LOCAL = manual_flags(ROOT / "agentic_env" / "skills")
ROSTER = {
    skill["name"]
    for pack in json.loads((ROOT / "agentic_env" / "skill-packs.json").read_text(encoding="utf-8"))["packs"]
    for skill in pack.get("skills", [])
}


class SkillInvocationDocsTests(unittest.TestCase):
    def test_routing_guide_lists_every_curated_skill_with_its_invocation(self) -> None:
        flags = {**MATT, **PSTACK, **LOCAL}
        starts: dict[str, str] = {}
        for row in (ROOT / "guides" / "skill-routing.md").read_text(encoding="utf-8").splitlines():
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) < 3 or not cells[2].startswith(("Agent", "You", "Always on")):
                continue
            for name in re.findall(r"`([\w-]+)`", cells[0]):
                starts[name] = cells[2]
        # Every manifest skill is listed and nothing else is.
        self.assertEqual(sorted(starts.keys() ^ ROSTER), [])
        # Starts says "You" exactly when the skill is manual-only. Remote packs ship no local
        # frontmatter to compare, so only vendored and first-party skills are checked.
        self.assertEqual(
            sorted(name for name, value in starts.items() if name in flags and value.startswith("You") != flags[name]),
            [],
        )

    def test_pstack_skills_are_manual_only_except_technical_writing(self) -> None:
        # `technical-writing` loads on a document deliverable (Decisions §6, 2026-11-16).
        self.assertEqual(
            sorted(name for name, manual in PSTACK.items() if not manual), ["technical-writing"]
        )
