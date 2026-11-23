"""Copy repository-vendored skills with Python alone; never download packages."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Collection
from pathlib import Path


def copy_skill_packages(
    packages: list[Path], destination: Path, replace: Collection[str] = ()
) -> None:
    """Preflight every package before copying; overwrite only skills named in `replace`."""
    destination = destination.resolve()
    if not packages:
        raise ValueError("No vendored skill packages selected")
    if destination.exists() and not destination.is_dir():
        raise NotADirectoryError(f"{destination}: not a directory")
    if len({package.name for package in packages}) != len(packages):
        raise ValueError("Two selected packages share a skill name")
    for package in packages:
        if not (package / "SKILL.md").is_file():
            raise FileNotFoundError(f"{package}: missing SKILL.md")
        if destination.is_relative_to(package.resolve()):
            raise ValueError(f"{destination}: destination is inside source package {package}")
        target = destination / package.name
        if not target.is_symlink() and target.resolve() == package.resolve():
            raise ValueError(f"{target}: is the source package")
        if target.exists() and not target.is_dir():
            raise FileExistsError(f"{target}: exists and is not a skill directory")
        if (target.exists() or target.is_symlink()) and package.name not in replace:
            raise FileExistsError(
                f"{target}: already exists; choose a destination without this skill"
            )
    destination.mkdir(parents=True, exist_ok=True)
    for package in packages:
        target = destination / package.name
        # copytree refuses a target that appeared after preflight: only `replace` overwrites.
        if package.name not in replace or not (target.exists() or target.is_symlink()):
            shutil.copytree(package, target)
            continue
        # Stage the copy and move the old package aside, so no failure loses it.
        staging = Path(tempfile.mkdtemp(prefix=f".{package.name}.", dir=destination))
        old = staging / "old"
        try:
            shutil.copytree(package, staging / "new")
            target.rename(old)
            (staging / "new").rename(target)
        except BaseException:
            shutil.rmtree(staging / "new", ignore_errors=True)
            if old.exists() or old.is_symlink():
                old.rename(target)  # raises, keeping `old`, if target is occupied again
            shutil.rmtree(staging, ignore_errors=True)
            raise
        shutil.rmtree(staging)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-dir", required=True, type=Path, help="Exact destination skills folder"
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        metavar="NAME",
        help="Copy only these vendored skills (repeat or comma-separate); default: all vendored skills",
    )
    args = parser.parse_args(argv)
    requested = {name.strip() for value in args.skill for name in value.split(",") if name.strip()}
    if args.skill and not requested:
        parser.error("--skill must contain a skill name")

    try:
        manifest_path = Path(__file__).with_name("skill-packs.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        local: dict[str, Path] = {}
        remote: list[str] = []
        for pack in manifest["packs"]:
            for entry in pack["skills"]:
                name = entry["name"] if isinstance(entry, dict) else entry
                if not name or name in {".", ".."} or "/" in name or "\\" in name:
                    raise ValueError(f"Invalid skill name: {name!r}")
                if pack["source"].startswith("./"):
                    local[name] = manifest_path.parent / pack["source"][2:] / name
                else:
                    remote.append(name)
        unavailable = requested - local.keys()
        if unavailable:
            raise ValueError(f"Not vendored in this checkout: {', '.join(sorted(unavailable))}")
        packages = [source for name, source in local.items() if not requested or name in requested]
        destination = args.skills_dir.expanduser().resolve()
        if remote and not requested:
            print(f"Not copied (remote-only, {len(remote)}): {', '.join(remote)}")
        copy_skill_packages(packages, destination)
        print(f"Copied {len(packages)} vendored skills to {destination}")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"Skill copy failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
