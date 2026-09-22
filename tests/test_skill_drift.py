from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_env import skill_drift
from agentic_env.install_skills_mcps import load_skill_manifest


def _write_skill(root: Path, name: str, body: str, extra: dict[str, str] | None = None) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(body, encoding="utf-8")
    for relative, content in (extra or {}).items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return path


def _manifest(path: Path, source: str, *, upstream: dict[str, str] | None = None):
    payload = {
        "packs": [
            {
                "name": "pack",
                "source": source,
                "label": "pack",
                "skills": ["alpha", "beta"],
                **({"upstream": upstream} if upstream else {}),
            }
        ],
        "profiles": {"default": ["pack"]},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    manifest = load_skill_manifest(path)
    assert manifest is not None
    return manifest


class DigestTests(unittest.TestCase):

    def test_digest_covers_content_paths_and_additions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = _write_skill(root, "alpha", "body\n")
            baseline = skill_drift.digest_tree(skill)

            (skill / "SKILL.md").write_text("body edited\n", encoding="utf-8")
            edited = skill_drift.digest_tree(skill)

            (skill / "SKILL.md").write_text("body\n", encoding="utf-8")
            (skill / "reference.md").write_text("extra\n", encoding="utf-8")
            with_extra = skill_drift.digest_tree(skill)

            self.assertNotEqual(baseline, edited)
            self.assertNotEqual(baseline, with_extra)
            self.assertIsNone(skill_drift.digest_tree(root / "absent"))

    def test_digest_is_path_sensitive(self) -> None:
        """Same bytes under a different name is a different package."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = _write_skill(root, "one", "body\n", {"a.md": "shared\n"})
            second = _write_skill(root, "two", "body\n", {"b.md": "shared\n"})

            self.assertNotEqual(skill_drift.digest_tree(first), skill_drift.digest_tree(second))


class LocateSkillTests(unittest.TestCase):

    def test_prefers_shallowest_non_hidden_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_skill(root / "skills", "alpha", "flat\n")
            _write_skill(root / "plugins" / "vendor" / "skills", "alpha", "nested\n")
            _write_skill(root / ".openclaw" / "skills", "alpha", "hidden\n")

            found = skill_drift.locate_skill(root, "alpha")

            self.assertIsNotNone(found)
            self.assertEqual((found / "SKILL.md").read_text(encoding="utf-8"), "flat\n")

    def test_finds_categorised_upstream_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_skill(root / "engineering", "tdd", "upstream\n")

            found = skill_drift.locate_skill(root, "tdd")

            self.assertEqual(found, root / "engineering" / "tdd")
            self.assertIsNone(skill_drift.locate_skill(root, "absent"))


class UpstreamResolutionTests(unittest.TestCase):

    def test_remote_source_supplies_repo_and_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = _manifest(Path(temp_dir) / "packs.json", "Owner/repo#v1.2.3")

            upstream = skill_drift.pack_upstream(manifest, "pack")

            self.assertEqual(upstream, skill_drift.Upstream(repo="Owner/repo", ref="v1.2.3"))
            self.assertFalse(upstream.pins_commit)

    def test_vendored_source_needs_an_explicit_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "packs.json"
            unpinned = _manifest(config, "./vendored/pack/skills")
            self.assertIsNone(skill_drift.pack_upstream(unpinned, "pack"))

            pinned = _manifest(
                config,
                "./vendored/pack/skills",
                upstream={"repo": "owner/monorepo", "ref": "a" * 40, "path": "pstack"},
            )
            upstream = skill_drift.pack_upstream(pinned, "pack")

            self.assertEqual(upstream.path, "pstack")
            self.assertTrue(upstream.pins_commit)


class InspectPackTests(unittest.TestCase):

    def _fixture(self, temp_dir: str):
        root = Path(temp_dir)
        vendored = root / "vendored" / "pack" / "skills"
        _write_skill(vendored, "alpha", "alpha source\n")
        _write_skill(vendored, "beta", "beta source\n")
        manifest = _manifest(root / "packs.json", f"./{vendored.relative_to(root)}")
        # `source` is resolved against the manifest's own directory.
        return root, manifest

    def _inspect(self, manifest, installed: Path, lock: dict[str, dict] | None = None, baseline=None):
        with patch.object(skill_drift, "CANONICAL_SKILL_ROOT", installed):
            return skill_drift.inspect_pack(
                manifest,
                "pack",
                baseline=baseline or {},
                lock=lock or {},
                offline=True,
                check_upstream=False,
            )

    def test_classifies_source_install_and_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, manifest = self._fixture(temp_dir)
            installed = root / "store"
            _write_skill(installed, "alpha", "alpha source\n")
            _write_skill(installed, "beta", "beta edited\n")

            rows = {row.skill: row for row in self._inspect(manifest, installed)}

            self.assertEqual(rows["alpha"].install, "ok")
            self.assertEqual(rows["beta"].install, "modified")
            # No baseline recorded yet: new, not drift.
            self.assertEqual(rows["alpha"].source, "new")
            self.assertFalse(rows["alpha"].drifted())
            self.assertTrue(rows["beta"].drifted())

    def test_missing_install_and_changed_source_are_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, manifest = self._fixture(temp_dir)
            installed = root / "store"
            _write_skill(installed, "alpha", "alpha source\n")

            rows = {
                row.skill: row
                for row in self._inspect(
                    manifest,
                    installed,
                    baseline={"pack": {"alpha": "stale-digest"}},
                )
            }

            self.assertEqual(rows["alpha"].source, "changed")
            self.assertEqual(rows["beta"].install, "missing")
            self.assertTrue(rows["alpha"].drifted())
            self.assertTrue(rows["beta"].drifted())

    def test_install_from_another_pack_is_foreign(self) -> None:
        """Matching bytes are not enough: the lockfile must name this pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root, manifest = self._fixture(temp_dir)
            installed = root / "store"
            _write_skill(installed, "alpha", "alpha source\n")
            lock = {"alpha": {"source": "someone/else"}}

            rows = {row.skill: row for row in self._inspect(manifest, installed, lock=lock)}

            self.assertEqual(rows["alpha"].install, "foreign:someone/else")
            self.assertTrue(rows["alpha"].drifted())

    def test_remote_pack_origin_matches_repo_without_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root / "packs.json", "Owner/repo#v1.2.3")
            installed = root / "store"
            _write_skill(installed, "alpha", "whatever\n")
            lock = {"alpha": {"source": "owner/repo"}}

            rows = {
                row.skill: row
                for row in self._inspect(manifest, installed, lock=lock)
            }

            # Source tree unreachable offline, so bytes cannot be compared,
            # but a matching origin must not be reported as foreign.
            self.assertEqual(rows["alpha"].install, skill_drift.UNKNOWN)
            self.assertEqual(rows["alpha"].source, skill_drift.UNKNOWN)
            self.assertFalse(rows["alpha"].drifted())


class CommandTests(unittest.TestCase):

    def test_json_mode_keeps_stdout_parseable(self) -> None:
        """Progress and warnings must not land in the machine-readable document."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vendored = root / "vendored" / "pack" / "skills"
            _write_skill(vendored, "alpha", "alpha source\n")
            config = root / "packs.json"
            _manifest(config, f"./{vendored.relative_to(root)}")
            stdout = io.StringIO()

            with (
                patch.object(skill_drift, "CANONICAL_SKILL_ROOT", root / "store"),
                contextlib.redirect_stdout(stdout),
            ):
                exit_code = skill_drift.main(
                    ["--skill-config", str(config), "--offline", "--json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)  # nothing installed
            self.assertEqual(
                [(row["skill"], row["install"]) for row in payload["skills"]],
                [("alpha", "missing"), ("beta", "missing")],
            )


class BaselineTests(unittest.TestCase):

    def test_update_keeps_fingerprints_for_unresolved_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root / "packs.json", "Owner/repo#v1.2.3")
            path = root / "skill-fingerprints.json"
            path.write_text(
                json.dumps(
                    {"version": 1, "packs": {"pack": {"skills": {"alpha": "recorded", "beta": "kept"}}}}
                ),
                encoding="utf-8",
            )
            rows = [
                skill_drift.SkillStatus("pack", "alpha", "new", "missing", "unknown", digest="fresh"),
                skill_drift.SkillStatus("pack", "beta", "unknown", "missing", "unknown", digest=None),
            ]

            self.assertTrue(skill_drift.write_baseline(manifest, rows, path))

            recorded = skill_drift.load_baseline(path)
            self.assertEqual(recorded["pack"], {"alpha": "fresh", "beta": "kept"})

    def test_load_baseline_tolerates_absent_or_broken_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            broken = Path(temp_dir) / "broken.json"
            broken.write_text("{not json", encoding="utf-8")

            self.assertEqual(skill_drift.load_baseline(broken), {})
            self.assertEqual(skill_drift.load_baseline(Path(temp_dir) / "absent.json"), {})


if __name__ == "__main__":
    unittest.main()
