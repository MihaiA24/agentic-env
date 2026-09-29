"""Compare the curated skill roster against its sources. Read-only.

Three questions per skill in the manifest:

* `upstream` — did the pack's upstream change since the pinned revision?
* `source`   — does the pack source still hash to the reviewed fingerprint?
* `install`  — does the installed copy match that source, and did the skills CLI
  install it from this pack?

Vendored packs carry documented local adaptations. Upstream drift compares the
pinned upstream revision with upstream today; local/upstream differences are
reported separately and do not count as drift. Optional diffs expose both.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from . import common
from .common import fetch_url, info, ok, skip, warn
from .install_skills_mcps import (
    SKILL_PACK_CONFIG_PATH,
    SkillManifest,
    load_skill_manifest,
)

# `~/.agents/skills` is the canonical store; Claude and Hermes link into it.
CANONICAL_SKILL_ROOT = Path.home() / ".agents" / "skills"
SKILL_LOCK_PATH = Path.home() / ".agents" / ".skill-lock.json"
BASELINE_PATH = Path(__file__).with_name("skill-fingerprints.json")
CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    / "agentic-env"
    / "skill-sources"
)

GITHUB_API = "https://api.github.com"
CODELOAD = "https://codeload.github.com"
_TIMEOUT_SEC = 60
_BASELINE_VERSION = 1
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_REMOTE_SOURCE_PATTERN = re.compile(r"^(?P<repo>[\w.-]+/[\w.-]+)(?:#(?P<ref>[^#]+))?$")

UNKNOWN = "unknown"
FIX = "agentic-install-skills-mcps --skill-profile default --yes"


@dataclass(frozen=True)
class Upstream:
    repo: str
    ref: str
    path: str | None = None

    @property
    def pins_commit(self) -> bool:
        return bool(_COMMIT_PATTERN.match(self.ref))


@dataclass
class SkillStatus:
    """One row: `skill` as the manifest wants it versus as the world has it."""

    pack: str
    skill: str
    source: str
    install: str
    upstream: str
    digest: str | None = None
    local_upstream: str = "skipped"
    pinned_ref: str | None = None
    latest_ref: str | None = None
    upstream_diff: str | None = None
    local_diff: str | None = None

    def drifted(self) -> bool:
        return any(
            value not in ("ok", UNKNOWN, "new", "skipped")
            for value in (self.source, self.install, self.upstream)
        )


def digest_tree(root: Path | None) -> str | None:
    """SHA256 over a skill directory: every file's relative path and bytes."""
    if root is None or not root.is_dir():
        return None
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def diff_skill(before: Path | None, after: Path | None, before_label: str, after_label: str) -> str:
    """Unified diff of whole packages, including added/deleted and binary files."""
    old_files = {p.relative_to(before).as_posix(): p for p in before.rglob("*") if p.is_file()} if before else {}
    new_files = {p.relative_to(after).as_posix(): p for p in after.rglob("*") if p.is_file()} if after else {}
    output: list[str] = []
    for name in sorted(old_files.keys() | new_files.keys()):
        old = old_files[name].read_bytes() if name in old_files else None
        new = new_files[name].read_bytes() if name in new_files else None
        if old == new:
            continue
        old_label = f"{before_label}/{name}" if old is not None else "/dev/null"
        new_label = f"{after_label}/{name}" if new is not None else "/dev/null"
        try:
            old_text = (old or b"").decode("utf-8")
            new_text = (new or b"").decode("utf-8")
        except UnicodeDecodeError:
            output.append(f"Binary files {old_label} and {new_label} differ\n")
            continue
        if "\0" in old_text or "\0" in new_text:
            output.append(f"Binary files {old_label} and {new_label} differ\n")
            continue
        lines = list(difflib.unified_diff(
            old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
            fromfile=old_label, tofile=new_label,
        ))
        if not lines:  # An empty file was added or deleted.
            output.append(f"--- {old_label}\n+++ {new_label}\n")
        for line in lines:
            output.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    return "".join(output)


def locate_skill(root: Path | None, name: str) -> Path | None:
    """A skill package inside a source tree. Upstream nests skills under category
    directories, vendored packs flatten them, so fall back to the shallowest
    non-hidden `<name>/SKILL.md`."""
    if root is None or not root.is_dir():
        return None
    if (root / name / "SKILL.md").is_file():
        return root / name
    matches = sorted(
        (
            match.parent
            for match in root.rglob(f"{name}/SKILL.md")
            if not any(part.startswith(".") for part in match.relative_to(root).parts)
        ),
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    return matches[0] if matches else None


def pack_upstream(manifest: SkillManifest, pack: str) -> Upstream | None:
    """Repo and revision to compare against, from `upstream` or the remote source."""
    entry = manifest.packs[pack]
    repo, ref = entry.upstream_repo, entry.upstream_ref
    if repo is None or ref is None:
        match = _REMOTE_SOURCE_PATTERN.match(entry.source)
        if match is None or match.group("ref") is None:
            return None
        repo = repo or match.group("repo")
        ref = ref or match.group("ref")
    return Upstream(repo=repo, ref=ref, path=entry.upstream_path)


def _api(route: str) -> object | None:
    try:
        return json.loads(fetch_url(f"{GITHUB_API}{route}", _TIMEOUT_SEC))
    except Exception as exc:  # network, rate limit, malformed payload
        warn(f"github api {route}: {exc}")
        return None


def latest_ref(upstream: Upstream) -> str | None:
    """Default-branch HEAD for commit pins; newest release tag otherwise."""
    if upstream.pins_commit:
        # Git refs avoid GitHub's anonymous REST rate limit. The package comparison
        # below still ignores unrelated commits elsewhere in a monorepo.
        try:
            result = subprocess.run(
                ["git", "ls-remote", f"https://github.com/{upstream.repo}.git", "HEAD"],
                capture_output=True, text=True, check=True, timeout=_TIMEOUT_SEC,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            fields = result.stdout.split()
            if len(fields) == 2 and _COMMIT_PATTERN.fullmatch(fields[0]) and fields[1] == "HEAD":
                return fields[0]
            warn(f"{upstream.repo}: could not resolve remote HEAD")
        except (OSError, subprocess.SubprocessError) as exc:
            warn(f"{upstream.repo}: remote HEAD lookup failed ({exc})")
        return None

    release = _api(f"/repos/{upstream.repo}/releases/latest")
    if isinstance(release, dict) and isinstance(release.get("tag_name"), str):
        return release["tag_name"]
    tags = _api(f"/repos/{upstream.repo}/tags?per_page=1")
    if isinstance(tags, list) and tags and isinstance(tags[0], dict):
        name = tags[0].get("name")
        return name if isinstance(name, str) else None
    return None


def fetch_tree(repo: str, ref: str, *, offline: bool) -> Path | None:
    """Extracted source tree for `repo` at `ref`, cached under `CACHE_ROOT`."""
    target = CACHE_ROOT / f"{repo.replace('/', '+')}@{ref}"
    if (target / ".agentic-complete").is_file():
        return target
    if offline:
        return None

    url = f"{CODELOAD}/{repo}/tar.gz/{ref}"
    try:
        payload = fetch_url(url, _TIMEOUT_SEC)
    except Exception as exc:
        warn(f"{repo}@{ref}: download failed ({exc})")
        return None

    staging = Path(tempfile.mkdtemp(prefix="agentic-skill-src-"))
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            archive.extractall(staging, filter="data")
        roots = [path for path in staging.iterdir() if path.is_dir()]
        extracted = roots[0] if len(roots) == 1 else staging
        (extracted / ".agentic-complete").write_text(f"{repo}@{ref}\n", encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(extracted), str(target))
    except Exception as exc:
        warn(f"{repo}@{ref}: extraction failed ({exc})")
        return None
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return target


def _scoped(tree: Path | None, upstream: Upstream) -> Path | None:
    if tree is None or not upstream.path:
        return tree
    scoped = tree / upstream.path
    return scoped if scoped.is_dir() else None


def source_root(
    manifest: SkillManifest, pack: str, upstream: Upstream | None, *, offline: bool
) -> Path | None:
    """What the installer reads: the vendored directory, or the pinned tarball."""
    if manifest.packs[pack].source.startswith("./"):
        root = Path(manifest.source(pack))
        return root if root.is_dir() else None
    if upstream is None:
        return None
    return _scoped(fetch_tree(upstream.repo, upstream.ref, offline=offline), upstream)


def load_lock(path: Path = SKILL_LOCK_PATH) -> dict[str, dict]:
    """The skills CLI lockfile: skill name -> install record."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    skills = payload.get("skills")
    return {
        name: entry
        for name, entry in skills.items()
        if isinstance(entry, dict)
    } if isinstance(skills, dict) else {}


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, dict[str, str]]:
    """Reviewed fingerprints: pack -> skill -> digest."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    packs = payload.get("packs")
    if not isinstance(packs, dict):
        return {}
    baseline: dict[str, dict[str, str]] = {}
    for pack, entry in packs.items():
        digests = entry.get("skills") if isinstance(entry, dict) else None
        if isinstance(digests, dict):
            baseline[pack] = {
                name: value for name, value in digests.items() if isinstance(value, str)
            }
    return baseline


def _origin_status(
    manifest: SkillManifest, pack: str, skill: str, lock: dict[str, dict]
) -> str | None:
    """`foreign:<source>` when the skills CLI recorded another pack as the origin."""
    entry = lock.get(skill)
    if entry is None:
        return None
    recorded = str(entry.get("source", "")).strip()
    if not recorded:
        return None

    source = manifest.packs[pack].source
    if source.startswith("./"):
        vendored = Path(manifest.source(pack))
        recorded_path = Path(recorded)
        if recorded_path == vendored or vendored in recorded_path.parents:
            return None
        return f"foreign:{recorded}"

    match = _REMOTE_SOURCE_PATTERN.match(source)
    expected = match.group("repo") if match else source
    return None if recorded.lower() == expected.lower() else f"foreign:{recorded}"


def inspect_pack(
    manifest: SkillManifest,
    pack: str,
    *,
    baseline: dict[str, dict[str, str]],
    lock: dict[str, dict],
    offline: bool,
    check_upstream: bool,
    check_installed: bool = True,
    show_diff: bool = False,
) -> list[SkillStatus]:
    upstream = pack_upstream(manifest, pack)
    pinned_source = source_root(manifest, pack, upstream, offline=offline)

    upstream_pinned: Path | None = None
    upstream_latest: Path | None = None
    newest: str | None = None
    if check_upstream and upstream is not None:
        newest = latest_ref(upstream) if not offline else None
        if newest is not None:
            upstream_pinned = _scoped(
                fetch_tree(upstream.repo, upstream.ref, offline=offline), upstream
            )
            upstream_latest = _scoped(
                fetch_tree(upstream.repo, newest, offline=offline), upstream
            )

    rows: list[SkillStatus] = []
    for skill in manifest.packs[pack].skills:
        source_dir = locate_skill(pinned_source, skill)
        source_digest = digest_tree(source_dir)

        if source_digest is None:
            source_status = "absent" if pinned_source is not None else UNKNOWN
        else:
            recorded = baseline.get(pack, {}).get(skill)
            source_status = (
                "new" if recorded is None else "ok" if recorded == source_digest else "changed"
            )

        install_status = "skipped"
        if check_installed:
            installed_digest = digest_tree(CANONICAL_SKILL_ROOT / skill)
            if installed_digest is None:
                install_status = "missing"
            elif source_digest is None:
                install_status = UNKNOWN
            elif installed_digest != source_digest:
                install_status = "modified"
            else:
                install_status = "ok"
            if install_status in ("ok", "modified"):
                install_status = _origin_status(manifest, pack, skill, lock) or install_status

        pinned_dir = locate_skill(upstream_pinned, skill)
        latest_dir = locate_skill(upstream_latest, skill)
        pinned_digest = digest_tree(pinned_dir)
        latest_digest = digest_tree(latest_dir)
        upstream_diff = local_diff = None
        local_status = "skipped" if not check_upstream else UNKNOWN
        if not check_upstream:
            upstream_status = "skipped"
        elif upstream_pinned is None or upstream_latest is None:
            upstream_status = UNKNOWN
        else:
            if pinned_digest is None or latest_digest is None:
                upstream_status = "absent"
            else:
                upstream_status = "ok" if pinned_digest == latest_digest else "changed"
            if show_diff:
                upstream_diff = diff_skill(
                    pinned_dir, latest_dir,
                    f"{pack}@{upstream.ref}/{skill}", f"{pack}@{newest}/{skill}",
                )

        if check_upstream and upstream_latest is not None and pinned_source is not None:
            if source_digest is None or latest_digest is None:
                local_status = "absent"
            else:
                local_status = "ok" if source_digest == latest_digest else "different"
            if show_diff:
                local_diff = diff_skill(
                    latest_dir, source_dir,
                    f"{pack}@{newest}/{skill}", f"local/{pack}/{skill}",
                )

        rows.append(
            SkillStatus(
                pack=pack,
                skill=skill,
                source=source_status,
                install=install_status,
                upstream=upstream_status,
                digest=source_digest,
                local_upstream=local_status,
                pinned_ref=upstream.ref if upstream else None,
                latest_ref=newest,
                upstream_diff=upstream_diff,
                local_diff=local_diff,
            )
        )

    if check_upstream and upstream is not None and newest is not None and newest != upstream.ref:
        info(f"{pack}: pinned {upstream.ref}, upstream at {newest}")
    return rows


def unmanaged_skills(manifest: SkillManifest) -> list[str]:
    """Installed skills no pack in the manifest claims, whatever `--pack` selected."""
    roster = {skill for pack in manifest.packs.values() for skill in pack.skills}
    if not CANONICAL_SKILL_ROOT.is_dir():
        return []
    return sorted(
        path.name
        for path in CANONICAL_SKILL_ROOT.iterdir()
        if (path / "SKILL.md").is_file() and path.name not in roster
    )


def write_baseline(
    manifest: SkillManifest, rows: list[SkillStatus], path: Path = BASELINE_PATH
) -> bool:
    """Record current source digests as reviewed. Packs with an unresolved source
    keep their previous fingerprints rather than losing them."""
    payload: dict[str, object] = {"version": _BASELINE_VERSION, "packs": {}}
    previous = load_baseline(path)
    packs: dict[str, object] = {}

    for pack in dict.fromkeys(row.pack for row in rows):
        digests = {row.skill: row.digest for row in rows if row.pack == pack and row.digest}
        unresolved = [row.skill for row in rows if row.pack == pack and row.digest is None]
        if unresolved:
            warn(f"{pack}: keeping recorded fingerprints, unresolved: {', '.join(unresolved)}")
            digests = {**previous.get(pack, {}), **digests}
        upstream = pack_upstream(manifest, pack)
        packs[pack] = {
            "source": manifest.packs[pack].source,
            "upstream": f"{upstream.repo}@{upstream.ref}" if upstream else None,
            "skills": dict(sorted(digests.items())),
        }

    payload["packs"] = packs
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    except OSError as exc:
        warn(f"{path}: could not write baseline ({exc})")
        return False
    ok(f"{path}: fingerprints recorded for {len(packs)} packs")
    return True


_STYLES = {
    "ok": "green",
    "new": "cyan",
    UNKNOWN: "yellow",
    "skipped": "dim",
    "different": "cyan",
    "changed": "red",
    "modified": "red",
    "missing": "red",
    "absent": "red",
}


def _cell(value: str) -> str:
    style = _STYLES.get(value.split(":", 1)[0], "red")
    return f"[{style}]{value}[/]"


def report(rows: list[SkillStatus], extra: list[str]) -> None:
    table = Table(title="agentic-skill-drift", show_lines=False)
    for column in ("Pack", "Skill", "Source", "Installed", "Upstream", "Local/upstream"):
        table.add_column(column, overflow="fold")
    for row in rows:
        table.add_row(
            row.pack, row.skill, _cell(row.source), _cell(row.install), _cell(row.upstream),
            _cell(row.local_upstream),
        )
    common.console.print(table)

    drifted = [row for row in rows if row.drifted()]
    if drifted:
        warn(f"{len(drifted)} of {len(rows)} curated skills drifted")
        for row in drifted:
            if row.install in ("missing", "modified") or row.install.startswith("foreign:"):
                warn(f"{row.skill}: install {row.install} — fix with `{FIX}`")
    elif not any(UNKNOWN in (row.source, row.install, row.upstream) for row in rows):
        ok(f"{len(rows)} curated skills: no drift (local adaptations excluded)")

    if any(UNKNOWN in (row.source, row.install, row.upstream) for row in rows):
        warn("Check incomplete: unknown is not a pass")
    for row in rows:
        for label, diff in (("Upstream changes (pinned -> latest)", row.upstream_diff),
                            ("Local differences (latest -> local)", row.local_diff)):
            if diff:
                common.console.print(f"\n{row.pack}/{row.skill}: {label}", markup=False)
                common.console.print(diff, markup=False, highlight=False, end="")

    if extra:
        skip(f"{len(extra)} installed skills outside the manifest: {', '.join(extra)}")


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare installed skills against their pack sources and upstreams",
    )
    parser.add_argument(
        "--pack",
        action="append",
        metavar="NAME",
        help="Restrict to this pack (repeatable). Default: every pack in the manifest.",
    )
    parser.add_argument(
        "--skill-config",
        metavar="PATH",
        default=str(SKILL_PACK_CONFIG_PATH),
        help="Path to JSON skill pack config (packs + profiles).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Never reach the network; use cached source trees only.",
    )
    parser.add_argument(
        "--no-upstream",
        action="store_true",
        help="Skip the upstream comparison (no GitHub API calls).",
    )
    parser.add_argument(
        "--no-installed",
        action="store_true",
        help="Check repository sources/upstreams only; ignore host installations.",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Include whole-package diffs: pinned upstream -> latest, latest -> local source.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Record current source fingerprints as reviewed, then exit.",
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)
    if args.diff and (args.no_upstream or args.offline or args.update_baseline):
        parser.error("--diff requires an online upstream check, without --update-baseline")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])

    if args.json:
        # Progress and warnings share the console with every other command, so
        # move them off stdout: `--json` must emit one parseable document.
        common.console = Console(stderr=True)

    manifest = load_skill_manifest(Path(args.skill_config))
    if manifest is None:
        return 1

    if args.pack:
        packs = [name.strip().lower() for name in args.pack]
        unknown = [name for name in packs if name not in manifest.packs]
        if unknown:
            warn(f"Unknown pack(s): {', '.join(unknown)}")
            return 1
    else:
        packs = list(manifest.packs)

    baseline = load_baseline()
    lock = {} if args.no_installed else load_lock()
    rows: list[SkillStatus] = []
    for pack in packs:
        rows.extend(
            inspect_pack(
                manifest,
                pack,
                baseline=baseline,
                lock=lock,
                offline=args.offline,
                check_upstream=not args.no_upstream,
                check_installed=not args.no_installed,
                show_diff=args.diff,
            )
        )

    if args.update_baseline:
        return 0 if write_baseline(manifest, rows) else 1

    extra = [] if args.no_installed else unmanaged_skills(manifest)
    if args.json:
        print(json.dumps({"skills": [asdict(row) for row in rows], "unmanaged": extra}, indent=2))
    else:
        report(rows, extra)

    if any(UNKNOWN in (row.source, row.install, row.upstream) for row in rows):
        return 2
    return 1 if any(row.drifted() for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
