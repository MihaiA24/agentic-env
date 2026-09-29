"""Canonical metadata for agentic-env stack installers, packages, and update flows.

This module intentionally centralizes shared remote-install references and command
mappings so install/update/configure scripts cannot drift independently.
"""

from __future__ import annotations

from typing import Final

from .remote_install_contract import (
    REMOTE_KIND_NPM,
    REMOTE_KIND_SCRIPT,
)

# Reviewed stack release. These are version floors, not pins: install and update
# fetch the latest release and verify it is at or above the floor. At each
# review, take the latest stable version and record it here.
# Reviewed 2026-09-09: OMP v18.1.14 and Codex 0.153.4.
# Other floors last reviewed 2026-09-02:
# Hermes v2026.8.31, Claude 2.1.258, and agentmemory 0.9.29.
HERMES_COMMIT: Final[str] = "29112bef099274229cadff79cdff7bf7b99c4b77"
OMP_VERSION: Final[str] = "18.1.14"
OPENAI_CODEX_PACKAGE: Final[str] = "@openai/codex@latest"
CODEBASE_MEMORY_VERSION: Final[str] = "0.9.0"
# lean-ctx is Rejected (ADR-0009). Reinstall pointer if semantic search need ever
# fires: https://github.com/yvgude/lean-ctx v3.10.0 or newer — never 3.9.x (lossy
# read-path default).
SKILLS_CLI_PACKAGE: Final[str] = "skills@latest"
AGENTMEMORY_VERSION: Final[str] = "0.9.29"
AGENTMEMORY_NPM_PACKAGE: Final[str] = "@agentmemory/agentmemory@latest"

# Installer fetched from the reviewed commit, not the floating endpoint: the
# endpoint changed on 2026-09-13 (issue #39) and every acceptance job went red.
# Bump = pick a new commit, re-verify the SHA256, record it in DECISIONS.
HERMES_INSTALL_COMMIT: Final[str] = "95d42656021a22f20201c618a67da07a618d16f3"
HERMES_INSTALL_URL: Final[str] = (
    "https://raw.githubusercontent.com/NousResearch/hermes-agent/"
    f"{HERMES_INSTALL_COMMIT}/scripts/install.sh"
)
HERMES_INSTALL_SHA256: Final[str] = (
    "5854b15670b51a8daae8f59ddfa917062de9f74be261eb73b4b8d719710f8968"
)
# OMP installs from GitHub release assets checked against the release's
# SHA256SUMS.txt, not via omp.sh/install: that script resolves every release
# (even with --ref) on the unauthenticated api.github.com REST API, which shared
# CI runner IPs exhaust (HTTP 403).
OMP_RELEASES_URL: Final[str] = "https://github.com/can1357/oh-my-pi/releases"
CLAUDE_INSTALL_URL: Final[str] = "https://claude.ai/install.sh"
CLAUDE_INSTALL_SHA256: Final[str] = (
    "3a68d3406cf674e17bed1733a4dcf37805e2e47d87417700007d7e1aa766a944"
)


CODEBASE_MEMORY_RELEASE_BASE: Final[str] = (
    f"https://github.com/DeusData/codebase-memory-mcp/releases/download/v{CODEBASE_MEMORY_VERSION}"
)
CODEBASE_MEMORY_ARCHIVES: Final[dict[tuple[str, str, bool], tuple[str, str]]] = {
    ("darwin", "amd64", False): (
        "codebase-memory-mcp-darwin-amd64.tar.gz",
        "6af3d02a27f589901fa763d3971089337bc8c9838bbed5d0cf543ca9f1a9e543",
    ),
    ("darwin", "arm64", False): (
        "codebase-memory-mcp-darwin-arm64.tar.gz",
        "faa02f0404230c451a9812230394481948f80183801fa5bf67044b41c2f25ed4",
    ),
    ("linux", "amd64", False): (
        "codebase-memory-mcp-linux-amd64-portable.tar.gz",
        "8459d5c9d1457f2c82de3de307ffc7641ecbba2dde893427be1e62eca8ef9b25",
    ),
    ("linux", "arm64", False): (
        "codebase-memory-mcp-linux-arm64-portable.tar.gz",
        "b0a43fdaf534073c16707d72726b73b149d4c1212034b281ee8b7b2dac755107",
    ),
    ("darwin", "amd64", True): (
        "codebase-memory-mcp-ui-darwin-amd64.tar.gz",
        "1fddbebbc4442b423e967fa730856e8f49c023fcdf8622cebe5b3c99f12219fc",
    ),
    ("darwin", "arm64", True): (
        "codebase-memory-mcp-ui-darwin-arm64.tar.gz",
        "592f84e44d5e8eab9ae7134e99b1540ce3c28e84b684204f8f39cde51620d0ee",
    ),
    ("linux", "amd64", True): (
        "codebase-memory-mcp-ui-linux-amd64-portable.tar.gz",
        "bb836df7cc84536bd501d1ff98d49f566cfbbaba421ea54780149e0b83c121fd",
    ),
    ("linux", "arm64", True): (
        "codebase-memory-mcp-ui-linux-arm64-portable.tar.gz",
        "67ef134e3fb490093b64156a88437c7ed1424c16e45440670d972346ea25271b",
    ),
}

# Minimum acceptable installed version per binary. Installers fetch the latest
# release and verify it against this floor; the doctor reports anything below it.
STACK_VERSION_FLOORS: Final[dict[str, str]] = {
    "hermes": "0.21.0",
    "omp": OMP_VERSION,
    "codex": "0.153.4",
    "claude": "2.1.258",
    "codebase-memory-mcp": CODEBASE_MEMORY_VERSION,
    "agentmemory": AGENTMEMORY_VERSION,
    "skills": "1.5.16",
}
# Shared agent/skill identities used by install_skills and configuration flows.
SKILL_AGENTS: Final[tuple[tuple[str, str, str], ...]] = (
    ("hermes", "hermes-agent", "Hermes Agent"),
    ("claude", "claude-code", "Claude Code"),
    ("codex", "codex", "Codex"),
)

SKILL_AGENT_CLI_NAMES: Final[dict[str, str]] = {
    agent: cli_name for agent, cli_name, _ in SKILL_AGENTS
}

SKILL_AGENT_LOOKUP: Final[dict[str, str]] = {
    **{agent: agent for agent, _, _ in SKILL_AGENTS},
    **{cli_name: agent for agent, cli_name, _ in SKILL_AGENTS},
    **{label.lower(): agent for agent, _, label in SKILL_AGENTS},
}

# Metadata for install script remote contracts.
AGENTS_INSTALL_REMOTE_CONTRACT: Final[dict[str, dict[str, object]]] = {
    "hermes": {
        "label": "Hermes installer script",
        "reference": HERMES_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": True,
        "sha256": HERMES_INSTALL_SHA256,
        "reason": "Fetched at a fixed upstream commit and hash-pinned; "
        "the floating endpoint drifted (#39).",
    },
    "codex": {
        "label": "OpenAI Codex npm package",
        "reference": OPENAI_CODEX_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": False,
        "reason": "Installs the latest release; the version floor "
        "(STACK_VERSION_FLOORS) is verified after install.",
    },
    "claude": {
        "label": "Claude installer script",
        "reference": CLAUDE_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": True,
        "sha256": CLAUDE_INSTALL_SHA256,
        "reason": "Floating script endpoint is hash-pinned for reproducibility.",
    },
}

SKILLS_INSTALL_REMOTE_CONTRACT: Final[dict[str, dict[str, object]]] = {
    "skills_cli": {
        "label": "skills CLI",
        "reference": SKILLS_CLI_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": False,
        "reason": "Installs the latest release; the version floor "
        "(STACK_VERSION_FLOORS) is verified after install.",
    },
    "agentmemory_npm": {
        "label": "agentmemory npm package",
        "reference": AGENTMEMORY_NPM_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": False,
        "reason": "Installs the latest release; the version floor "
        "(STACK_VERSION_FLOORS) is verified after install.",
    },
}

UPDATE_REMOTE_CONTRACT: Final[dict[str, dict[str, object]]] = {
    **AGENTS_INSTALL_REMOTE_CONTRACT,
    **SKILLS_INSTALL_REMOTE_CONTRACT,
}

# Update execution deliberately reuses the canonical install paths with
# force=True, so every run pulls the latest release rather than stopping at the
# floor; native updater commands cannot satisfy the curated stack contract.

# Agents supported by configure-agent-mcps.
CONFIGURE_AGENT_CHOICES: Final[tuple[str, ...]] = ("hermes", "omp")
