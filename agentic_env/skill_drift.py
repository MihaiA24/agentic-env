"""Compare the curated skill roster against its sources. Read-only.

Three questions per skill in the manifest:

* `upstream` — did the pack's upstream change since the pinned revision?
* `source`   — does the pack source still hash to the reviewed fingerprint?
* `install`  — does the installed copy match that source, and, for a remote
  pack, did the skills CLI install it from that repo?

Vendored packs carry documented local adaptations, so the upstream answer never
diffs the vendored tree against upstream: it compares upstream at the pinned
revision with upstream today. Adaptations therefore never register as drift, and
a real upstream edit does.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.table import Table

from . import common
from .common import fetch_url, info, ok, skip, warn
from .install_skills_mcps import (
    SKILL_PACK_CONFIG_PATH,
    SkillManifest,
    SkillUpstream,
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

UNKNOWN = "unknown"
FIX = "agentic-install-skills-mcps --skill-profile default --yes"


@dataclass
class SkillStatus:
    """One row: `skill` as the manifest wants it versus as the world has it."""

    pack: str
    skill: str
    source: str
    install: str
    upstream: str
    digest: str | None = None

    def drifted(self) -> bool:
        return any(
            value not in ("ok", UNKNOWN, "new")
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


def _api(route: str) -> object | None:
    try:
        return json.loads(fetch_url(f"{GITHUB_API}{route}", _TIMEOUT_SEC))
    except Exception as exc:  # network, rate limit, malformed payload
        warn(f"github api {route}: {exc}")
        return None


def latest_ref(upstream: SkillUpstream) -> str | None:
    """The revision upstream is at now: newest commit for a commit pin (scoped to
    `path`), newest release tag otherwise."""
    if _COMMIT_PATTERN.fullmatch(upstream.ref):
        scope = f"&path={upstream.path}" if upstream.path else ""
        commits = _api(f"/repos/{upstream.repo}/commits?per_page=1{scope}")
        if isinstance(commits, list) and commits and isinstance(commits[0], dict):
            sha = commits[0].get("sha")
            return sha if isinstance(sha, str) else None
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


def _scoped(tree: Path | None, upstream: SkillUpstream) -> Path | None:
    if tree is None or not upstream.path:
        return tree
    scoped = tree / upstream.path
    return scoped if scoped.is_dir() else None


def source_root(
    manifest: SkillManifest, pack: str, upstream: SkillUpstream | None, *, offline: bool
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


def _baseline_packs(path: Path) -> dict[str, object] | None:
    """Raw `packs` of the baseline file: `{}` when absent, None when unreadable."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        return None
    packs = payload.get("packs") if isinstance(payload, dict) else None
    return packs if isinstance(packs, dict) else None


def _skill_digests(entry: object) -> dict[str, str] | None:
    digests = entry.get("skills") if isinstance(entry, dict) else None
    if not isinstance(digests, dict):
        return None
    return {name: value for name, value in digests.items() if isinstance(value, str)}


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, dict[str, str]]:
    """Reviewed fingerprints: pack -> skill -> digest."""
    return {
        pack: digests
        for pack, entry in (_baseline_packs(path) or {}).items()
        if (digests := _skill_digests(entry)) is not None
    }


def _origin_status(
    manifest: SkillManifest, pack: str, skill: str, lock: dict[str, dict]
) -> str | None:
    """`foreign:<source>` when the skills CLI recorded another repo as the origin
    of a remote pack's skill. Vendored installs are judged by content alone: the
    skills CLI keeps a stale remote source in the lock after a local install."""
    source = manifest.packs[pack].source
    if source.startswith("./"):
        return None
    recorded = str(lock.get(skill, {}).get("source", "")).strip()
    if not recorded:
        return None
    expected = source.partition("#")[0]
    return None if recorded.lower() == expected.lower() else f"foreign:{recorded}"


def inspect_pack(
    manifest: SkillManifest,
    pack: str,
    *,
    baseline: dict[str, dict[str, str]],
    lock: dict[str, dict],
    offline: bool,
    check_upstream: bool,
) -> list[SkillStatus]:
    upstream = manifest.packs[pack].upstream
    pinned_source = source_root(manifest, pack, upstream, offline=offline)

    upstream_pinned: Path | None = None
    upstream_latest: Path | None = None
    newest: str | None = None
    if check_upstream and upstream is not None:
        newest = latest_ref(upstream) if not offline else None
        if newest is not None and newest != upstream.ref:
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

        # No upstream comparison asked for, no pinned revision to compare, or the
        # newest revision could not be resolved: all indistinguishable here.
        if not check_upstream or upstream is None or newest is None:
            upstream_status = UNKNOWN
        elif newest == upstream.ref:
            upstream_status = "ok"
        else:
            pinned_digest = digest_tree(locate_skill(upstream_pinned, skill))
            latest_digest = digest_tree(locate_skill(upstream_latest, skill))
            if pinned_digest is None or latest_digest is None:
                upstream_status = "absent" if upstream_latest is not None else UNKNOWN
            else:
                upstream_status = "ok" if pinned_digest == latest_digest else "changed"

        rows.append(
            SkillStatus(
                pack=pack,
                skill=skill,
                source=source_status,
                install=install_status,
                upstream=upstream_status,
                digest=source_digest,
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
    """Record current source digests for the packs in `rows`, preserving every
    unselected entry and unresolved skill's previous fingerprint."""
    previous = _baseline_packs(path)
    if previous is None:
        warn(f"{path}: unreadable baseline; fix or remove it before recording")
        return False

    selected = dict.fromkeys(row.pack for row in rows)
    packs: dict[str, object] = dict(previous)
    for pack in selected:
        digests = {row.skill: row.digest for row in rows if row.pack == pack and row.digest}
        unresolved = [row.skill for row in rows if row.pack == pack and row.digest is None]
        if unresolved:
            warn(f"{pack}: keeping recorded fingerprints, unresolved: {', '.join(unresolved)}")
            digests = {**(_skill_digests(previous.get(pack)) or {}), **digests}
        upstream = manifest.packs[pack].upstream
        packs[pack] = {
            "source": manifest.packs[pack].source,
            "upstream": f"{upstream.repo}@{upstream.ref}" if upstream else None,
            "skills": dict(sorted(digests.items())),
        }

    payload = {"version": _BASELINE_VERSION, "packs": packs}
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    except OSError as exc:
        warn(f"{path}: could not write baseline ({exc})")
        return False
    ok(f"{path}: fingerprints recorded for {len(selected)} packs")
    return True


_STYLES = {
    "ok": "green",
    "new": "cyan",
    UNKNOWN: "yellow",
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
    for column in ("Pack", "Skill", "Source", "Installed", "Upstream"):
        table.add_column(column, overflow="fold")
    for row in rows:
        table.add_row(
            row.pack, row.skill, _cell(row.source), _cell(row.install), _cell(row.upstream)
        )
    common.console.print(table)

    drifted = [row for row in rows if row.drifted()]
    if drifted:
        warn(f"{len(drifted)} of {len(rows)} curated skills drifted")
        for row in drifted:
            if row.install in ("missing", "modified") or row.install.startswith("foreign:"):
                warn(f"{row.skill}: install {row.install} — fix with `{FIX}`")
    else:
        ok(f"{len(rows)} curated skills match their sources")

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
        "--update-baseline",
        action="store_true",
        help="Record current source fingerprints as reviewed, then exit.",
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])

    document = sys.stdout
    # Progress and warnings print through the shared console to stdout; divert
    # them for this call only so `--json` emits one parseable document.
    diverted = contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext()
    with diverted:
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
        lock = load_lock()
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
                )
            )

        if args.update_baseline:
            return 0 if write_baseline(manifest, rows) else 1

        extra = unmanaged_skills(manifest)
        if args.json:
            findings = {"skills": [asdict(row) for row in rows], "unmanaged": extra}
            print(json.dumps(findings, indent=2), file=document)
        else:
            report(rows, extra)

        return 1 if any(row.drifted() for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
