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

# Reviewed stack release. Install and update must converge to these identities.
HERMES_VERSION: Final[str] = "0.18.2"
HERMES_COMMIT: Final[str] = "36f2a966c7f9f69987494b867c3dcf96b69a5766"
OMP_VERSION: Final[str] = "17.0.5"
OMP_REF: Final[str] = f"v{OMP_VERSION}"
OPENAI_CODEX_VERSION: Final[str] = "0.144.1"
OPENAI_CODEX_PACKAGE: Final[str] = f"@openai/codex@{OPENAI_CODEX_VERSION}"
CLAUDE_VERSION: Final[str] = "2.1.210"
CODEBASE_MEMORY_VERSION: Final[str] = "0.9.0"
LEAN_CTX_VERSION: Final[str] = "3.9.11"
SKILLS_CLI_VERSION: Final[str] = "1.5.16"
SKILLS_CLI_PACKAGE: Final[str] = f"skills@{SKILLS_CLI_VERSION}"
AGENTMEMORY_VERSION: Final[str] = "0.9.27"
AGENTMEMORY_NPM_PACKAGE: Final[str] = f"@agentmemory/agentmemory@{AGENTMEMORY_VERSION}"

HERMES_INSTALL_URL: Final[str] = "https://hermes-agent.nousresearch.com/install.sh"
HERMES_INSTALL_SHA256: Final[str] = (
    "c2e4326c1660bd45f64321996eb15bda35e7a4649e32a310495a61972a2804c8"
)
OMP_INSTALL_URL: Final[str] = "https://omp.sh/install"
OMP_INSTALL_SHA256: Final[str] = (
    "1e089e5d3c94224a7ceaa7c2130b6ea8018ec88aafa55b9fa18728fe076a1e80"
)
CLAUDE_INSTALL_URL: Final[str] = "https://claude.ai/install.sh"
CLAUDE_INSTALL_SHA256: Final[str] = (
    "b3f79015b54c751440a6488f07b1b64f9088742b9052bc1bd356d13108320d2a"
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
LEAN_CTX_RELEASE_BASE: Final[str] = (
    f"https://github.com/yvgude/lean-ctx/releases/download/v{LEAN_CTX_VERSION}"
)
LEAN_CTX_ARCHIVES: Final[dict[tuple[str, str], tuple[str, str]]] = {
    ("darwin", "amd64"): (
        "lean-ctx-x86_64-apple-darwin.tar.gz",
        "1bfa42f5ec4c45398ba6687ec3e860678fd704d837110f926b48bbaa9bb773e0",
    ),
    ("darwin", "arm64"): (
        "lean-ctx-aarch64-apple-darwin.tar.gz",
        "8f7735e2df93b99056d89d0d4d406f5d1d795968f49372018ac46b511e4c228c",
    ),
    ("linux", "amd64"): (
        "lean-ctx-x86_64-unknown-linux-gnu.tar.gz",
        "69f48a29d9dbeddbb9bf087a304153b00588f2a67efa0bee282ae0381cb70f69",
    ),
    ("linux", "arm64"): (
        "lean-ctx-aarch64-unknown-linux-gnu.tar.gz",
        "f8cb2a769ae00a22756bb60451d209fd52c6b7ba4859afb979d9afaad285d127",
    ),
}

STACK_VERSION_FRAGMENTS: Final[dict[str, tuple[str, ...]]] = {
    "hermes": (f"Hermes Agent v{HERMES_VERSION}", f"upstream {HERMES_COMMIT[:8]}"),
    "omp": (f"omp/{OMP_VERSION}",),
    "codex": (f"codex-cli {OPENAI_CODEX_VERSION}",),
    "claude": (CLAUDE_VERSION,),
    "codebase-memory-mcp": (f"codebase-memory-mcp {CODEBASE_MEMORY_VERSION}",),
    "lean-ctx": (f"lean-ctx {LEAN_CTX_VERSION}",),
    "agentmemory": (AGENTMEMORY_VERSION,),
    "skills": (SKILLS_CLI_VERSION,),
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
        "reason": "Floating script endpoint is hash-pinned for reproducibility.",
    },
    "omp": {
        "label": "OMP / Oh My Pi installer script",
        "reference": OMP_INSTALL_URL,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": True,
        "sha256": OMP_INSTALL_SHA256,
        "reason": "Floating script endpoint is hash-pinned for reproducibility.",
    },
    "codex": {
        "label": "OpenAI Codex npm package",
        "reference": OPENAI_CODEX_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
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
        "pinned": True,
        "reason": "",
    },
    "agentmemory_npm": {
        "label": "agentmemory npm package",
        "reference": AGENTMEMORY_NPM_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
    },
}

UPDATE_REMOTE_CONTRACT: Final[dict[str, dict[str, object]]] = {
    **AGENTS_INSTALL_REMOTE_CONTRACT,
    **SKILLS_INSTALL_REMOTE_CONTRACT,
}

# Update execution deliberately reuses the canonical install paths; native latest-only
# updater commands cannot satisfy the curated stack contract.

# Agents supported by configure-agent-mcps.
CONFIGURE_AGENT_CHOICES: Final[tuple[str, ...]] = ("hermes", "omp")
