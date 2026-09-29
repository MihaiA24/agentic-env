from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
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

    def test_diff_includes_deleted_added_binary_and_unterminated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old = _write_skill(root / "old", "alpha", "old", {"removed.md": "gone\n"})
            new = _write_skill(root / "new", "alpha", "new\n", {"added.md": "here\n", "empty": ""})
            (old / "image").write_bytes(b"\xff\0")
            (new / "image").write_bytes(b"\xfe\0")

            diff = skill_drift.diff_skill(old, new, "old/alpha", "new/alpha")

            self.assertIn("-old\n\\ No newline at end of file\n+new\n", diff)
            self.assertIn("--- old/alpha/removed.md\n+++ /dev/null\n", diff)
            self.assertIn("--- /dev/null\n+++ new/alpha/added.md\n", diff)
            self.assertIn("--- /dev/null\n+++ new/alpha/empty\n", diff)
            self.assertIn("Binary files old/alpha/image and new/alpha/image differ\n", diff)


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

    def test_remote_tag_compares_against_latest_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = _manifest(Path(temp_dir) / "packs.json", "Owner/repo#v1.2.3")
            responses = {"/repos/Owner/repo/releases/latest": {"tag_name": "v2.0.0"}}
            with patch.object(skill_drift, "_api", side_effect=responses.get):
                self.assertEqual(
                    skill_drift.latest_ref(manifest.packs["pack"].upstream), "v2.0.0"
                )

    def test_commit_pin_resolves_remote_head_with_git_not_rest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "owner" / "monorepo.git"
            manifest = _manifest(
                root / "packs.json",
                "./vendored/pack/skills",
                upstream={"repo": "owner/monorepo", "ref": "a" * 40, "path": "pstack"},
            )
            # Git rewrites GitHub URLs to local fixtures; every network transport
            # is disabled, so wrong repositories and refs fail without a request.
            with (
                patch.dict(os.environ, {
                    "PATH": os.environ["PATH"],
                    "HOME": str(root),
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": f"url.{root.as_uri()}/.insteadOf",
                    "GIT_CONFIG_VALUE_0": "https://github.com/",
                    "GIT_ALLOW_PROTOCOL": "file",
                }, clear=True),
                patch.object(
                    skill_drift, "fetch_url", side_effect=AssertionError("unexpected HTTP request"),
                ) as fetch,
            ):
                subprocess.run(
                    ["git", "init", "--quiet", "--initial-branch=trunk", str(repo)],
                    check=True, capture_output=True, timeout=10,
                )
                subprocess.run(
                    ["git", "-C", str(repo), "-c", "user.name=Test",
                     "-c", "user.email=test@example.invalid",
                     "commit", "--quiet", "--allow-empty", "-m", "upstream fixture"],
                    check=True, capture_output=True, timeout=10,
                )
                head = subprocess.check_output(
                    ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, timeout=10,
                ).strip()
                upstream = manifest.packs["pack"].upstream
                self.assertEqual(skill_drift.latest_ref(upstream), head)

                repo.rename(root / "unavailable.git")
                self.assertIsNone(skill_drift.latest_ref(upstream))
                fetch.assert_not_called()


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

    def test_vendored_install_is_judged_by_content_not_stale_lock(self) -> None:
        """The skills CLI keeps the old remote source in the lock after a local install."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root, manifest = self._fixture(temp_dir)
            installed = root / "store"
            _write_skill(installed, "alpha", "alpha source\n")
            _write_skill(installed, "beta", "beta edited\n")
            stale = {"source": "upstream/skills"}
            lock = {"alpha": stale, "beta": stale}

            rows = {row.skill: row for row in self._inspect(manifest, installed, lock=lock)}

            self.assertEqual(rows["alpha"].install, "ok")
            self.assertFalse(rows["alpha"].drifted())
            self.assertEqual(rows["beta"].install, "modified")
            self.assertTrue(rows["beta"].drifted())

    def test_remote_install_from_another_repo_is_foreign(self) -> None:
        """Matching bytes are not enough for a remote pack: the lockfile must name its repo."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root / "packs.json", "Owner/repo#v1.2.3")
            cached = root / "cache" / "Owner+repo@v1.2.3"
            _write_skill(cached, "alpha", "alpha source\n")
            _write_skill(cached, "beta", "beta source\n")
            (cached / ".agentic-complete").write_text("Owner/repo@v1.2.3\n", encoding="utf-8")
            installed = root / "store"
            _write_skill(installed, "alpha", "alpha source\n")
            _write_skill(installed, "beta", "beta source\n")
            lock = {"alpha": {"source": "someone/else"}, "beta": {"source": "owner/repo"}}

            with patch.object(skill_drift, "CACHE_ROOT", root / "cache"):
                rows = {row.skill: row for row in self._inspect(manifest, installed, lock=lock)}

            self.assertEqual(rows["alpha"].install, "foreign:someone/else")
            self.assertTrue(rows["alpha"].drifted())
            self.assertEqual(rows["beta"].install, "ok")

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
        """Progress and warnings must not land in the machine-readable document,
        nor stay diverted for the next normal run in the same process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vendored = root / "vendored" / "pack" / "skills"
            _write_skill(vendored, "alpha", "alpha source\n")
            config = root / "packs.json"
            _manifest(config, f"./{vendored.relative_to(root)}")
            document = io.StringIO()
            normal = io.StringIO()

            with (
                patch.object(skill_drift, "CANONICAL_SKILL_ROOT", root / "store"),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with contextlib.redirect_stdout(document):
                    exit_code = skill_drift.main(
                        ["--skill-config", str(config), "--offline", "--no-upstream", "--json"]
                    )
                with contextlib.redirect_stdout(normal):
                    skill_drift.main(["--skill-config", str(config), "--offline", "--no-upstream"])

            payload = json.loads(document.getvalue())
            self.assertEqual(exit_code, 1)  # nothing installed
            self.assertEqual(
                [(row["skill"], row["install"]) for row in payload["skills"]],
                [("alpha", "missing"), ("beta", "missing")],
            )
            self.assertIn("agentic-skill-drift", normal.getvalue())


class RemoteComparisonTests(unittest.TestCase):
    """Exercise the CLI against real package trees; replace only remote lookup/download."""

    def _fixture(self, root: Path) -> Path:
        for tree in ("vendored", "pinned", "latest"):
            _write_skill(root / tree / "skills", "alpha", "upstream alpha\n")
            _write_skill(root / tree / "skills", "beta", "upstream beta\n")
        config = root / "packs.json"
        _manifest(
            config, "./vendored/skills",
            upstream={"repo": "owner/repo", "ref": "a" * 40, "path": "skills"},
        )
        return config

    def _check(self, root: Path, config: Path, *, newest="b" * 40, pinned=True, latest=True):
        trees = {
            "a" * 40: root / "pinned" if pinned else None,
            "b" * 40: root / "latest" if latest else None,
        }
        stdout = io.StringIO()
        with (
            patch.object(skill_drift, "latest_ref", return_value=newest),
            patch.object(skill_drift, "fetch_tree", side_effect=lambda repo, ref, **kw: trees[ref]),
            patch.object(skill_drift, "CANONICAL_SKILL_ROOT", root / "uninstalled"),
            contextlib.redirect_stdout(stdout),
        ):
            code = skill_drift.main([
                "--skill-config", str(config), "--no-installed", "--diff", "--json",
            ])
        return code, {row["skill"]: row for row in json.loads(stdout.getvalue())["skills"]}

    def test_separates_local_adaptations_from_new_upstream_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self._fixture(root)
            _write_skill(root / "vendored" / "skills", "alpha", "local adaptation\n")
            _write_skill(root / "vendored" / "skills", "beta", "local beta\n")
            _write_skill(root / "latest" / "skills", "alpha", "upstream alpha\n",
                         {"references/example.md": "new reference\n"})

            code, rows = self._check(root, config)

            self.assertEqual(code, 1)
            self.assertEqual(rows["alpha"]["upstream"], "changed")
            self.assertEqual(rows["beta"]["upstream"], "ok")
            self.assertEqual(rows["beta"]["local_upstream"], "different")
            self.assertEqual(rows["alpha"]["install"], "skipped")
            self.assertEqual(rows["alpha"]["latest_ref"], "b" * 40)
            self.assertEqual(rows["alpha"]["pinned_ref"], "a" * 40)
            self.assertIn("+new reference\n", rows["alpha"]["upstream_diff"])
            self.assertNotIn("local adaptation", rows["alpha"]["upstream_diff"])
            self.assertIn("+local adaptation\n", rows["alpha"]["local_diff"])
            self.assertEqual(rows["beta"]["upstream_diff"], "")

    def test_local_differences_do_not_fail_even_when_latest_equals_pin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self._fixture(root)
            _write_skill(root / "vendored" / "skills", "alpha", "local adaptation\n")
            for newest in ("a" * 40, "b" * 40):
                with self.subTest(newest=newest):
                    code, rows = self._check(root, config, newest=newest)
                    self.assertEqual(code, 0)
                    self.assertEqual(rows["alpha"]["upstream"], "ok")
                    self.assertEqual(rows["alpha"]["local_upstream"], "different")
                    self.assertIn("+local adaptation\n", rows["alpha"]["local_diff"])
                    self.assertEqual(rows["beta"]["local_upstream"], "ok")
                    self.assertEqual(rows["beta"]["local_diff"], "")

    def test_remote_failures_are_incomplete_not_absent_or_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self._fixture(root)
            for failure in ({"newest": None}, {"pinned": False}, {"latest": False}):
                with self.subTest(failure=failure):
                    code, rows = self._check(root, config, **failure)
                    self.assertEqual(code, 2)
                    self.assertEqual(rows["alpha"]["upstream"], "unknown")
                    self.assertIsNone(rows["alpha"]["upstream_diff"])

    def test_remote_skill_deletion_is_reported_with_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self._fixture(root)
            (root / "latest" / "skills" / "alpha" / "SKILL.md").unlink()

            code, rows = self._check(root, config)

            self.assertEqual(code, 1)
            self.assertEqual(rows["alpha"]["upstream"], "absent")
            self.assertIn("-upstream alpha\n", rows["alpha"]["upstream_diff"])
            self.assertIn("+++ /dev/null\n", rows["alpha"]["upstream_diff"])


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

    def test_scoped_update_keeps_other_packs_verbatim(self) -> None:
        """`--pack X --update-baseline` passes only X's rows; other packs stay reviewed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / "packs.json"
            config.write_text(
                json.dumps(
                    {
                        "packs": [
                            {"name": "pack", "source": "Owner/repo#v1.2.3", "label": "pack", "skills": ["alpha"]},
                            {"name": "other", "source": "Other/repo#v2.0.0", "label": "other", "skills": ["gamma"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            manifest = load_skill_manifest(config)
            # Reviewed at an older pin than the manifest now names: kept as recorded.
            other = {"source": "Other/repo#v1.0.0", "upstream": "Other/repo@v1.0.0", "skills": {"gamma": "reviewed"}}
            path = root / "skill-fingerprints.json"
            path.write_text(
                json.dumps({"version": 1, "packs": {
                    "pack": {"skills": {"alpha": "old"}},
                    "other": other,
                    "outside-custom-manifest": other,
                }}),
                encoding="utf-8",
            )
            rows = [skill_drift.SkillStatus("pack", "alpha", "changed", "ok", "unknown", digest="fresh")]

            self.assertTrue(skill_drift.write_baseline(manifest, rows, path))

            recorded = json.loads(path.read_text(encoding="utf-8"))["packs"]
            self.assertEqual(recorded["other"], other)
            self.assertEqual(recorded["outside-custom-manifest"], other)
            self.assertEqual(recorded["pack"]["skills"], {"alpha": "fresh"})

    def test_update_refuses_to_overwrite_unreadable_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root / "packs.json", "Owner/repo#v1.2.3")
            path = root / "skill-fingerprints.json"
            path.write_text("{not json", encoding="utf-8")
            rows = [skill_drift.SkillStatus("pack", "alpha", "new", "ok", "unknown", digest="fresh")]

            self.assertFalse(skill_drift.write_baseline(manifest, rows, path))
            self.assertEqual(path.read_text(encoding="utf-8"), "{not json")

    def test_load_baseline_tolerates_absent_or_broken_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            broken = Path(temp_dir) / "broken.json"
            broken.write_text("{not json", encoding="utf-8")

            self.assertEqual(skill_drift.load_baseline(broken), {})
            self.assertEqual(skill_drift.load_baseline(Path(temp_dir) / "absent.json"), {})


if __name__ == "__main__":
    unittest.main()
