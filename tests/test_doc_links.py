from __future__ import annotations

import functools
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Vendored docs keep their upstream's links; dot-directories hold tool state.
SKIPPED_DIRS = {"node_modules", "vendored"}


def markdown_files() -> list[Path]:
    return [
        path for path in sorted(ROOT.rglob("*.md"))
        if not any(part.startswith(".") or part in SKIPPED_DIRS for part in path.relative_to(ROOT).parts)
    ]


@functools.cache
def github_anchors(path: Path) -> frozenset[str]:
    """Heading anchors as GitHub renders them; repeated headings get -1, -2, ..."""
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(r"#{1,6} ", line):
            slug = re.sub(r"[^\w\- ]", "", line.lstrip("#").strip().lower()).replace(" ", "-")
            count = seen.get(slug, 0)
            anchors.add(f"{slug}-{count}" if count else slug)
            seen[slug] = count + 1
    return frozenset(anchors)


class DocLinkTests(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self) -> None:
        broken: list[str] = []
        for source in markdown_files():
            text = re.sub(r"```.*?```", "", source.read_text(encoding="utf-8"), flags=re.DOTALL)
            text = re.sub(r"`[^`\n]*`", "", text)
            targets: list[str] = re.findall(r"\]\(([^)\s]+)\)", text)
            for target in targets:
                if re.match(r"[a-z][a-z0-9+.-]*:", target):  # https:, mailto:, ...
                    continue
                path, _, anchor = target.partition("#")
                dest = (source.parent / path).resolve() if path else source
                if not dest.exists():
                    broken.append(f"{source.relative_to(ROOT)}: {target} (no such file)")
                elif anchor and dest.suffix == ".md" and anchor not in github_anchors(dest):
                    broken.append(f"{source.relative_to(ROOT)}: {target} (no such heading)")
        self.assertEqual(broken, [])
