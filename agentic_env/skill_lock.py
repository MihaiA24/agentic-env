"""The native skills CLI's global lock and canonical skill store.

agentic-env reads install records to converge a host. It removes records only
after verified cleanup and stores offer history in the native ``dismissed`` map.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .common import write_atomic_text

# `~/.agents/skills` is the canonical store; Claude and Hermes link into it.
CANONICAL_SKILL_ROOT = Path.home().resolve() / ".agents" / "skills"
# Convergence only writes the format it understands.
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


class InvalidLock(ValueError):
    """An existing lock could not be read as the supported native format."""


@dataclass
class SkillLock:
    path: Path
    _payload: dict

    @property
    def skills(self) -> dict[str, dict]:
        return self._payload["skills"]

    @property
    def offered(self) -> set[str]:
        return {
            key.removeprefix(_OFFERED_PREFIX)
            for key, value in self._payload.get("dismissed", {}).items()
            if key.startswith(_OFFERED_PREFIX) and value is True
        }

    def record_changes(self, *, removed: Iterable[str], offered: Iterable[str]) -> bool:
        """Save after native installs, which rewrite the whole lock."""
        for name in removed:
            self.skills.pop(name, None)
        for name in offered:
            self._payload.setdefault("dismissed", {})[f"{_OFFERED_PREFIX}{name}"] = True
        content = json.dumps(self._payload, indent=2)
        return write_atomic_text(self.path, content, dry_run=False, backup=False)


def load_lock() -> SkillLock:
    """Only a missing lock represents an empty installation."""
    path = lock_path()
    message = f"{path}: invalid skills lock; restore or repair it before continuing"
    try:
        mode = path.stat().st_mode
        payload = json.loads(path.read_text(encoding="utf-8")) if stat.S_ISREG(mode) else None
    except FileNotFoundError as exc:
        if path.is_symlink():
            raise InvalidLock(message) from exc
        return SkillLock(path, {"version": _LOCK_VERSION, "skills": {}})
    except (OSError, ValueError) as exc:
        raise InvalidLock(message) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("version") != _LOCK_VERSION
        or type(payload.get("version")) is not int
        or not isinstance(skills := payload.get("skills"), dict)
        or not all(isinstance(entry, dict) for entry in skills.values())
        or not isinstance(payload.get("dismissed", {}), dict)
    ):
        raise InvalidLock(message)
    return SkillLock(path, payload)


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


def _folder_hash(folder: Path) -> str | None:
    """Match the CLI's file hash, but refuse to delete entries it ignores."""
    files: list[tuple[bytes, Path]] = []

    def collect(directory: Path, prefix: str) -> bool:
        before = len(files)
        with os.scandir(directory) as entries:
            for entry in entries:
                name = prefix + entry.name
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in _EXCLUDED_DIRS or not collect(path, name + "/"):
                        return False
                elif entry.name in _EXCLUDED_FILES or not entry.is_file(follow_symlinks=False):
                    return False
                else:
                    files.append((name.replace("\\", "/").encode(), path))
        return len(files) > before

    if not collect(folder, ""):
        return None
    digest = hashlib.sha256()
    for name, path in sorted(files):
        content = path.read_bytes()
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
            if tree is None:
                return None
            # Git orders a tree as if its name ended with "/".
            entries.append((name + b"/", b"40000", bytes.fromhex(tree)))
        elif entry.is_file():
            mode = b"100755" if entry.stat().st_mode & stat.S_IXUSR else b"100644"
            entries.append((name, mode, _git_object(b"blob", Path(entry.path).read_bytes())))
        else:
            raise OSError(f"{entry.path}: unsupported file type in skill tree")
    if not entries:
        return None
    body = b"".join(
        b"%s %s\0%s" % (mode, name.removesuffix(b"/"), oid) for name, mode, oid in sorted(entries)
    )
    return _git_object(b"tree", body).hex()
