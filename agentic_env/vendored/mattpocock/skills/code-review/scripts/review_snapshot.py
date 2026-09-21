#!/usr/bin/env python3
"""Freeze an explicitly scoped Git review without staging or committing user work."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile


def git(root: Path, *args: str, env: dict[str, str] | None = None, data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], input=data, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ".git" in path.parts or value.startswith(":"):
        raise ValueError(f"Expected a literal repository-relative path: {value!r}")
    return str(path)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text())
    expected = manifest["files"]
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != set(expected) | {"manifest.json"}:
        raise ValueError("Snapshot file set changed")
    for name, sha in expected.items():
        path = output / relative_path(name)
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != output.parent):
            raise ValueError(f"Snapshot contains a filesystem symlink: {name}")
        if digest(path) != sha:
            raise ValueError(f"Snapshot content changed: {name}")
    return manifest


def working_files(root: Path, head: str, paths: list[str]) -> dict[str, tuple[str, bytes] | None]:
    # Include HEAD deletions, index additions and scoped untracked files; ignored
    # untracked files are deliberately excluded. Git pathspec magic is disabled.
    tracked = git(root, "--literal-pathspecs", "ls-tree", "-r", "--name-only", "-z", head, "--", *paths)
    current = git(root, "--literal-pathspecs", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *paths)
    names = sorted({os.fsdecode(p) for p in (tracked + current).split(b"\0") if p})
    files = {}
    for name in names:
        path = root / relative_path(name)
        parent = path.parent
        while parent != root:
            if parent.is_symlink():
                raise ValueError(f"Refusing to follow symlink parent: {name}")
            parent = parent.parent
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            files[name] = None
            continue
        if stat.S_ISLNK(mode):
            files[name] = ("120000", os.fsencode(os.readlink(path)))
        elif stat.S_ISREG(mode):
            files[name] = ("100755" if mode & 0o111 else "100644", path.read_bytes())
        else:
            raise ValueError(f"Cannot freeze non-file or submodule: {name}")
    return files


def freeze(base: str, mode: str, head_ref: str, paths: list[str], output: Path) -> dict:
    root = Path(os.fsdecode(git(Path.cwd(), "rev-parse", "--show-toplevel")).strip()).resolve()
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError("Snapshot output must be outside the source checkout")
    if output.exists():
        raise ValueError("Snapshot output must not already exist")
    if mode == "wip" and not paths:
        raise ValueError("WIP requires explicit --path selections; do not include unrelated user work")
    paths = [relative_path(p) for p in paths]
    base_commit = git(root, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}").decode().strip()
    head = git(root, "rev-parse", "--verify", "--end-of-options", f"{head_ref}^{{commit}}").decode().strip()
    if mode == "wip" and head_ref != "HEAD":
        raise ValueError("WIP overlays the current HEAD; use --mode refs for another head")
    before = working_files(root, head, paths) if mode == "wip" else {}
    output.mkdir(parents=True)
    try:
        with tempfile.TemporaryDirectory(prefix="review-index-") as temporary:
            scratch = Path(temporary)
            objects = scratch / "objects"
            objects.mkdir()
            original_objects = Path(os.fsdecode(git(root, "rev-parse", "--git-path", "objects")).strip())
            if not original_objects.is_absolute():
                original_objects = root / original_objects
            # Temporary index AND object database: the real checkout is read-only.
            env = dict(os.environ, GIT_INDEX_FILE=str(scratch / "index"),
                       GIT_OBJECT_DIRECTORY=str(objects),
                       GIT_ALTERNATE_OBJECT_DIRECTORIES=str(original_objects.resolve()))
            git(root, "read-tree", head, env=env)
            for name, entry in before.items():
                git(root, "update-index", "--force-remove", "--", name, env=env)
            for name, entry in before.items():
                if entry is not None:
                    file_mode, content = entry
                    blob = git(root, "hash-object", "--no-filters", "-w", "--stdin", env=env, data=content).decode().strip()
                    git(root, "update-index", "--add", "--cacheinfo", file_mode, blob, name, env=env)
            tree = git(root, "write-tree", env=env).decode().strip()
            if mode == "wip" and (working_files(root, head, paths) != before or git(root, "rev-parse", "HEAD").decode().strip() != head):
                raise ValueError("Source changed during capture; freeze again after edits stop")
            patch = git(root, "--literal-pathspecs", "diff", "--binary", "--no-ext-diff", "--no-textconv", base_commit, tree, "--", *paths, env=env)
            (output / "diff.patch").write_bytes(patch)
            (output / "commits.txt").write_bytes(git(root, "--literal-pathspecs", "log", "--format=%H %s", f"{base_commit}..{head}", "--", *paths))
            tree_dir = output / "tree"
            tree_dir.mkdir()
            symlinks = {}
            # Export blobs directly: git archive can apply export-ignore and
            # export-subst attributes, silently changing the code being reviewed.
            entries = git(root, "ls-tree", "-r", "-z", tree, env=env).split(b"\0")
            for entry in entries:
                if not entry:
                    continue
                metadata, raw_name = entry.split(b"\t", 1)
                file_mode, kind, object_id = metadata.decode().split()
                name = os.fsdecode(raw_name)
                if kind != "blob":
                    raise ValueError(f"Submodule context needs a separate explicit review: {name}")
                destination = tree_dir / relative_path(name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                content = git(root, "cat-file", "blob", object_id, env=env)
                destination.write_bytes(content)
                if file_mode == "120000":
                    # Preserve link targets as text, never create links that
                    # could let a reviewer escape the frozen tree.
                    symlinks[name] = os.fsdecode(content)
            files = {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*")) if p.is_file()}
            manifest = {"mode": mode, "base": base_commit, "head": head, "scope": paths,
                        "tree": tree, "symlinks_as_text": symlinks, "files": files}
            (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        verify(output)
        return manifest
    except BaseException:
        shutil.rmtree(output)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    parser.add_argument("--mode", choices=("wip", "refs"), default="wip")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            manifest = verify(args.verify.resolve())
        elif args.base and args.output:
            manifest = freeze(args.base, args.mode, args.head, args.path, args.output)
        else:
            parser.error("supply --base and --output, or --verify")
        print(json.dumps(manifest, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Snapshot failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
