# Agentic Environment Context

## Core terms

- **Agent stack**
  - The canonical local tooling set managed in this folder: `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `lean-ctx`, `agentmemory`.

- **Primary harness**
  - The agent the stack is chosen for and validated against: `omp`. Secondary agents still receive installs and MCP configuration, but they do not drive tool selection.
  - _Avoid_: Default agent, main CLI, preferred agent

- **Supported agent**
  - An agent whose CLI, global skills, project-memory MCP configuration, and health checks are all managed by `agentic-env`. Authentication and credentials remain user-owned. The supported agents are Hermes, OMP, Claude Code, and Codex.
  - _Avoid_: Installed agent, partially supported agent, authenticated agent

- **Machine provisioning**
  - The product boundary of `agentic-env`: install, configure, update, and diagnose the user-level agent stack. Repository initialization, indexing, project-memory maintenance, uninstall, and rollback remain outside the product boundary. Agent hook files are diagnosed but never written; the tools that install them own them.
  - _Avoid_: Project onboarding, project lifecycle management

- **Project memory stack**
  - The project context layer used by agents. On the primary harness: OMP core owns context I/O, `codebase-memory-mcp` answers structural code-graph queries, and Mnemopi holds narrative memory, with `lean-ctx` gated to the tools the host has no equivalent for. Secondary agents keep the earlier three-tool wiring — `lean-ctx`, `codebase-memory-mcp`, `agentmemory` — until that is revisited.
  - _Avoid_: Memory MCP stack, AI context stack

- **Agentmemory integration**
  - The managed agentmemory CLI and MCP registration used for narrative memory. The interactive `iii-engine` runtime is outside machine provisioning because its upgrade can mutate the current repository.
  - _Avoid_: iii-engine lifecycle management

- **Structural memory**
  - The indexed code graph used to answer questions about code shape, symbols, routes, callers, dependencies, and impact.
  - _Avoid_: Narrative memory, decision memory

- **Narrative memory**
  - The durable project history used to preserve decisions, rationale, domain discoveries, and working context across agent sessions.
  - _Avoid_: Structural memory, code graph

- **Domain glossary**
  - A plain-text `CONTEXT.md` vocabulary for canonical project terms used by `grill-with-docs` and related design sessions.
  - _Avoid_: Memory dump, implementation notes

- **Agent MCP configuration**
  - Global agent config that registers MCP servers for Hermes, OMP, Claude Code, and Codex before an agent session starts.
  - _Avoid_: Project memory, skill install

- **Managed MCP entry**
  - A user-level MCP configuration entry named `lean-ctx`, `codebase-memory-mcp`, or `agentmemory` that `agentic-env` owns and converges to its curated definition while preserving unrelated agent settings. Malformed configuration is rejected without modification.
  - _Avoid_: Any MCP entry, user-owned configuration

- **Read-interception policy**
  - A hook or instruction block that gates or redirects an agent's file reads and searches toward a query-first tool. Scoped per supported agent, counted across every configuration file that agent loads rather than the files in its own directory. At most one may be active for a given agent.
  - _Avoid_: Query-before-read hook, discovery gate, read redirect

- **Agent global skill**
  - A reusable `SKILL.md` installed in an agent's user-level skills directory so the agent knows when and how to use a tool.
  - _Avoid_: MCP server, project-local skill

- **Curated skill default**
  - The small reviewed set of skill packs installed by default for the supported agent workflow; custom skill-pack configuration is the extension point for user-specific packs.
  - _Avoid_: Comprehensive skill catalog, skill marketplace

- **uv runnable script**
  - A single-file Python script with inline `uv` metadata that is executed from the checkout with `uv run --script` or `uv run ./script.py`.
  - _Avoid_: uv tool command, installed CLI

- **uv tool command**
  - A named CLI entry point installed by `uv tool install` and run from the user's PATH.
  - _Avoid_: uv runnable script

- **Fresh install**
  - A complete, non-interactive installation in a clean supported-host environment using:
    - `uv tool install --force .`
    - `agentic-bootstrap --yes`
    - legacy split path:
      - `agentic-install-agents --all --yes`
      - `agentic-install-skills-mcps --all-mcps --yes`
      - `agentic-configure-agent-mcps --yes`

- **Curated stack update**
  - A non-interactive maintenance run that converges every installed agent-stack component to the reviewed versions declared by `agentic-env`.
  - _Avoid_: Latest-available update, mixed pinned/latest update, fresh install

- **Provisioner upgrade**
  - Replacement of the installed `agentic-env` tool through `uv`, kept separate from a curated stack update because `uv` owns the provisioner's installation source and lifecycle.
  - _Avoid_: Stack update, self-replacing updater

- **Setup runner**
  - The shared `run_cmd` wrapper in `agentic-env/setup_helpers.sh` that keeps setup scripts quiet by default, prints command progress, and dumps captured output only on failure.
  - _Avoid_: Per-script command wrapper copies

- **Smoke test**
  - The fresh-install contract exercised on Arch Linux and macOS; it must pass before a host is accepted as supported.

- **Smoke contract**
  - Process succeeds when: tools are installed, binaries are callable, every supported agent's MCP config contains the project memory stack servers, and matching global skills exist.

- **Provisioning verification**
  - Evidence that deterministic command and configuration contracts pass focused tests and the complete agent stack passes the fresh-install smoke contract.
  - _Avoid_: Line coverage, mocked installer success

- **Stack doctor**
  - A read-only host diagnostic that reports agent-stack command availability, versions, MCP registrations, global skills, duplicate hook registrations, and conflicting read-interception policies for every supported agent; it exits unsuccessfully with corrective commands when the machine does not satisfy the smoke contract.
  - _Avoid_: Smoke test, automatic repair

- **Supported host**
  - A macOS or Arch Linux-family machine, including CachyOS, on which the complete machine-provisioning and stack-doctor contracts are verified.
  - _Avoid_: Any Unix-like host, Debian-compatible host

- **Compatibility floor**
  - Host prerequisites required by the agent stack: Python 3.12+, Node.js 20+, `curl`, `git`, and trusted CA certificates. The Linux fresh-install smoke environment is Arch Linux.

- **Documentation scope**
  - `agentic-env/README.md`: runbook and operating instructions.
  - `agentic-env/docs/CONTEXT.md`: canonical vocabulary and invariants.
  - `agentic-env/docs/adr/*.md`: irreversible design decisions.
