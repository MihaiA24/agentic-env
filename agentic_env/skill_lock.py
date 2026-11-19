"""The native skills CLI's global lock and canonical skill store.

The CLI owns both. agentic-env reads install records to converge a host, and
writes back only which roster skills it has offered, as keys of the lock's
`dismissed` map: the CLI keeps unknown keys there when it rewrites the lock.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Iterable
from pathlib import Path

from .common import warn, write_atomic_text

# `~/.agents/skills` is the canonical store; Claude and Hermes link into it.
CANONICAL_SKILL_ROOT = Path.home() / ".agents" / "skills"
# The CLI discards a lock below this version and starts an empty one.
_LOCK_VERSION = 3
_OFFERED_PREFIX = "agentic-env:offered:"
# The CLI leaves these out of a skill's copy and of its folder hash.
_EXCLUDED_FILES = frozenset({"metadata.json"})
_EXCLUDED_DIRS = frozenset({".git", "__pycache__", "__pypackages__"})


def lock_path() -> Path:
    """Where the CLI keeps the global lock: under `XDG_STATE_HOME` when that is set."""
    state = os.environ.get("XDG_STATE_HOME")
    if state:
        return Path(state) / "skills" / ".skill-lock.json"
    return Path.home() / ".agents" / ".skill-lock.json"


def _read() -> dict | None:
    """The lock as the CLI would accept it; None when absent, unreadable or discarded."""
    try:
        payload = json.loads(lock_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("skills"), dict):
        return None
    version = payload.get("version")
    if isinstance(version, bool) or not isinstance(version, int | float) or version < _LOCK_VERSION:
        return None
    return payload


def load_lock() -> dict[str, dict]:
    """Skill name -> install record."""
    payload = _read()
    if payload is None:
        return {}
    return {name: entry for name, entry in payload["skills"].items() if isinstance(entry, dict)}


def offered() -> set[str]:
    """Roster skills already offered on this host."""
    dismissed = (_read() or {}).get("dismissed")
    if not isinstance(dismissed, dict):
        return set()
    return {
        key.removeprefix(_OFFERED_PREFIX)
        for key, value in dismissed.items()
        if key.startswith(_OFFERED_PREFIX) and value is True
    }


def record_offered(names: Iterable[str]) -> bool:
    """Mark skills as offered. Call only while no skills CLI process runs: the CLI
    rewrites the whole lock and would drop a record written meanwhile."""
    payload = _read()
    path = lock_path()
    if payload is None:
        if path.exists():
            warn(f"{path}: unreadable skills lock; offered skills not recorded")
            return False
        payload = {"version": _LOCK_VERSION, "skills": {}}
    dismissed = payload.get("dismissed")
    if not isinstance(dismissed, dict):
        dismissed = payload["dismissed"] = {}
    for name in names:
        dismissed[f"{_OFFERED_PREFIX}{name}"] = True
    # Same layout as the CLI's own writes; no backup of a file the CLI rewrites anyway.
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    return write_atomic_text(path, content, dry_run=False, backup=False)


def matches_record(folder: Path, entry: dict) -> bool:
    """Whether `folder` still holds what the CLI installed. Local sources record a
    SHA-256 over the folder's files; GitHub sources record the Git tree id."""
    expected = entry.get("skillFolderHash")
    if not isinstance(expected, str) or folder.is_symlink() or not folder.is_dir():
        return False
    if len(expected) == 64:
        return _folder_hash(folder) == expected
    if len(expected) == 40:
        return _tree_id(folder) == expected
    return False


def _folder_hash(folder: Path) -> str:
    """The CLI's `computeSkillFolderHash`: every file under `folder` sorted by path,
    each hashed as path, length and content (CRLF read as LF unless binary)."""
    root = folder.resolve()
    files: list[tuple[bytes, bytes]] = []

    def collect(directory: Path, prefix: str, ancestors: frozenset[Path]) -> None:
        real = directory.resolve()
        if real in ancestors:
            return
        ancestors = ancestors | {real}
        for entry in os.scandir(directory):
            is_dir = entry.is_dir(follow_symlinks=False)
            if entry.name in _EXCLUDED_FILES or (is_dir and entry.name in _EXCLUDED_DIRS):
                continue
            path = Path(entry.path)
            if entry.is_symlink():
                try:
                    target = path.resolve(strict=True)
                except (OSError, RuntimeError):
                    continue
                if not target.is_relative_to(root):
                    continue
                is_dir = target.is_dir()
                if is_dir and entry.name in _EXCLUDED_DIRS:
                    continue
            elif not is_dir and not entry.is_file(follow_symlinks=False):
                continue
            if is_dir:
                collect(path, f"{prefix}{entry.name}/", ancestors)
            else:
                files.append(((prefix + entry.name).encode(), path.read_bytes()))

    collect(folder, "", frozenset())
    digest = hashlib.sha256()
    for name, content in sorted(files):
        if b"\0" not in content:
            content = content.replace(b"\r\n", b"\n")
        digest.update(b"%s\0%d\0%s" % (name, len(content), content))
    return digest.hexdigest()


def _git_object(kind: bytes, data: bytes) -> bytes:
    return hashlib.sha1(b"%s %d\0%s" % (kind, len(data), data)).digest()


def _tree_id(folder: Path) -> str | None:
    """Git's tree id for `folder`; None when it holds no files, as Git stores none."""
    entries: list[tuple[bytes, bytes, bytes]] = []
    for entry in os.scandir(folder):
        name = os.fsencode(entry.name)
        if entry.is_symlink():
            entries.append((name, b"120000", _git_object(b"blob", os.fsencode(os.readlink(entry.path)))))
        elif entry.is_dir():
            tree = _tree_id(Path(entry.path))
            if tree is not None:
                # Git orders a tree as if its name ended with "/".
                entries.append((name + b"/", b"40000", bytes.fromhex(tree)))
        elif entry.is_file():
            mode = b"100755" if entry.stat().st_mode & stat.S_IXUSR else b"100644"
            entries.append((name, mode, _git_object(b"blob", Path(entry.path).read_bytes())))
    if not entries:
        return None
    body = b"".join(
        b"%s %s\0%s" % (mode, name.removesuffix(b"/"), oid) for name, mode, oid in sorted(entries)
    )
    return _git_object(b"tree", body).hex()
