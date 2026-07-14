"""Canonical metadata for agentic-env stack installers, packages, and update flows.

This module intentionally centralizes shared remote-install references and command
mappings so install/update/configure scripts cannot drift independently.
"""

from __future__ import annotations

from typing import Final

from .remote_install_contract import REMOTE_KIND_NPM, REMOTE_KIND_RAW_URL, REMOTE_KIND_SCRIPT

# Tool versions and installer sources (pinned where applicable)
OPENAI_CODEX_PACKAGE: Final[str] = "@openai/codex@0.144.1"
SKILLS_CLI_PACKAGE: Final[str] = "skills@1.5.16"
AGENTMEMORY_NPM_PACKAGE: Final[str] = "@agentmemory/agentmemory@0.9.27"

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

AGENTMEMORY_PI_INDEX_TS: Final[str] = (
    "https://raw.githubusercontent.com/rohitg00/agentmemory/93ae9bc04f3ab5042f982aaadf11f1e3f5137531/integrations/pi/index.ts"
)
AGENTMEMORY_PI_INDEX_SHA256: Final[str] = (
    "1e978990097ece72036b30eb0d24b3a26022a0d8276ea645fb47380c691d5f31"
)
CODEBASE_MEMORY_INSTALL: Final[str] = (
    "https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/2469ecc3a7a2f80debe296e1f17a1efcfdb9450c/"
    "install.sh"
)
CODEBASE_MEMORY_INSTALL_SHA256: Final[str] = (
    "90ef82a3da3336ddc2c3851ad56822067b161856f24cd88cbd405fe423af6a66"
)
LEAN_CTX_INSTALL_SCRIPT: Final[str] = "https://leanctx.com/install.sh"
LEAN_CTX_INSTALL_SHA256: Final[str] = (
    "f689c9667cd7d96b5a2bedd701cdb93b7d1ec8cd993fa5fcd591cd8ca76b96bb"
)
# Shared agent/skill identities used by install_skills and configuration flows.
SKILL_AGENTS: Final[tuple[tuple[str, str, str], ...]] = (
    ("hermes", "hermes-agent", "Hermes Agent"),
    ("ohmipy", "pi", "Pi"),
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
    "agentmemory_pi_index": {
        "label": "agentmemory PI index.ts",
        "reference": AGENTMEMORY_PI_INDEX_TS,
        "kind": REMOTE_KIND_RAW_URL,
        "pinned": True,
        "sha256": AGENTMEMORY_PI_INDEX_SHA256,
        "reason": "",
    },
    "codebase_memory_script": {
        "label": "codebase-memory-mcp install script",
        "reference": CODEBASE_MEMORY_INSTALL,
        "kind": REMOTE_KIND_RAW_URL,
        "pinned": True,
        "sha256": CODEBASE_MEMORY_INSTALL_SHA256,
        "reason": "",
    },
    "lean_ctx_script": {
        "label": "lean-ctx installer",
        "reference": LEAN_CTX_INSTALL_SCRIPT,
        "kind": REMOTE_KIND_SCRIPT,
        "pinned": True,
        "sha256": LEAN_CTX_INSTALL_SHA256,
        "reason": "Floating script endpoint is hash-pinned for reproducibility.",
    },
}

UPDATE_REMOTE_CONTRACT: Final[dict[str, dict[str, object]]] = {
    "agentmemory_npm": {
        "label": "agentmemory npm package",
        "reference": AGENTMEMORY_NPM_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
    },
    "openai_cdx": {
        "label": "OpenAI Codex npm package",
        "reference": OPENAI_CODEX_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
    },
    "skills_cli": {
        "label": "skills CLI",
        "reference": SKILLS_CLI_PACKAGE,
        "kind": REMOTE_KIND_NPM,
        "pinned": True,
        "reason": "",
    },
}

# Canonical update command targets.
UPDATE_STEPS: Final[
    tuple[tuple[str, str, list[str], str], ...]
] = (
    (
        "Hermes Agent",
        "hermes",
        ["hermes", "update", "--yes"],
        "Hermes Agent: not installed",
    ),
    ("OMP / Oh My Pi", "omp", ["omp", "update"], "OMP / Oh My Pi: not installed"),
    ("Claude Code", "claude", ["claude", "update"], "Claude Code: not installed"),
    (
        "codebase-memory-mcp",
        "codebase-memory-mcp",
        ["codebase-memory-mcp", "update"],
        "codebase-memory-mcp: not installed",
    ),
    ("lean-ctx", "lean-ctx", ["lean-ctx", "update"], "lean-ctx: not installed"),
)

# Agents supported by configure-agent-mcps.
CONFIGURE_AGENT_CHOICES: Final[tuple[str, ...]] = ("hermes", "omp")
