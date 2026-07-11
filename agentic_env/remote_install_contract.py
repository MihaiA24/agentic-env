"""Remote-install reproducibility contract helpers for agentic-env scripts.

The contract is intentionally explicit: each remote reference is declared once with either
`pinned=True` (must include a concrete version/ref) or `pinned=False` with a rationale
for allowed floating behavior.
"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Mapping

from .common import warn

REMOTE_KIND_NPM = "npm"
REMOTE_KIND_RAW_URL = "raw-url"
REMOTE_KIND_SCRIPT = "script"


def _is_pinned_npm_package(package: str) -> bool:
    """Return True when an npm package spec is pinned to an explicit version."""
    _, sep, version = package.rpartition("@")
    return bool(sep and version and version.lower() != "latest")


def _is_pinned_raw_url(raw_url: str) -> bool:
    """Return True when a raw GitHub URL is pinned to a non-mutable ref."""
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = [part for part in parsed.path.split("/") if part]
    if len(path) < 3:
        return False
    # raw.githubusercontent.com/<owner>/<repo>/<ref>/<path...>
    ref = path[2]
    if not ref:
        return False
    return ref.lower() not in {"main", "master", "develop", "trunk", "latest", "head"}


def validate_remote_contract_reference(*, label: str, reference: str, kind: str, pinned: bool, reason: str | None = None, scope: str) -> bool:
    """Validate one contract entry and emit actionable diagnostics."""
    if not label or not reference:
        warn(f"[{scope}] invalid remote contract entry for {label!r} in {scope}")
        return False

    if pinned:
        if kind == REMOTE_KIND_NPM and not _is_pinned_npm_package(reference):
            warn(
                f"[{scope}] {label}: pinned npm package must include an explicit version, "
                f"found '{reference}'."
            )
            return False

        if kind == REMOTE_KIND_RAW_URL and not _is_pinned_raw_url(reference):
            warn(
                f"[{scope}] {label}: raw URL must avoid mutable git refs (main/master), "
                f"found '{reference}'."
            )
            return False

        if kind not in {REMOTE_KIND_NPM, REMOTE_KIND_RAW_URL}:
            warn(f"[{scope}] {label}: unsupported remote kind '{kind}'")
            return False

        return True

    if not reason:
        warn(f"[{scope}] {label}: floating remote references require an allowlist reason")
        return False
    return True


def validate_remote_contract(
    entries: Mapping[str, Mapping[str, str | bool]], *, scope: str
) -> bool:
    """Validate all configured remote contract entries for a script."""
    ok_all = True
    for entry in entries.values():
        label = str(entry.get("label", "unknown"))
        reference = str(entry.get("reference", ""))
        kind = str(entry.get("kind", ""))
        pinned = bool(entry.get("pinned", False))
        reason = str(entry.get("reason", "")) or None

        ok_all = (
            validate_remote_contract_reference(
                label=label,
                reference=reference,
                kind=kind,
                pinned=pinned,
                reason=reason,
                scope=scope,
            )
            and ok_all
        )
    return ok_all
