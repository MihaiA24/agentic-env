# Agentic Environment Context

## Core terms

- **Agent stack**
  - The canonical local tooling set managed in this folder: `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `lean-ctx`, `agentmemory`.

- **Project memory stack**
  - The three-tool project context layer used by agents: `lean-ctx` for efficient local context access, `codebase-memory-mcp` for structural code graph queries, and `agentmemory` for narrative and decision memory.
  - _Avoid_: Memory MCP stack, AI context stack

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
  - Global agent config that registers MCP servers for Hermes and OMP before an agent session starts.
  - _Avoid_: Project memory, skill install

- **Agent global skill**
  - A reusable `SKILL.md` installed in an agent's user-level skills directory so the agent knows when and how to use a tool.
  - _Avoid_: MCP server, project-local skill

- **Fresh install**
  - A complete, non-interactive installation from a clean container using:
    - `install-agents.py --all --yes`
    - `install-skills-mcps.py --all-mcps --yes`
    - `configure-agent-mcps.py --yes`

- **Unattended update**
  - A maintenance run that refreshes installed agent stack components without opening prompts or re-running interactive bootstrap installers.
  - _Avoid_: Fresh install, smoke test

- **Setup runner**
  - The shared `run_cmd` wrapper in `agentic-env/setup_helpers.sh` that keeps setup scripts quiet by default, prints command progress, and dumps captured output only on failure.
  - _Avoid_: Per-script command wrapper copies

- **Smoke test**
  - The `docker-smoke-test.sh` contract that must pass before an image is accepted.

- **Smoke contract**
  - Process succeeds when: tools are installed, binaries are callable, Hermes/OMP MCP configs contain the project memory stack servers, and matching global skills exist.

- **Compatibility floor**
  - Base OS/runtime assumptions required by installer scripts, including:
    - GNU libc-compatible runtime for Hermes/OMP/Installer scripts
    - `curl`, `git`, and `ca-certificates` for network bootstrap + TLS

- **Documentation scope**
  - `agentic-env/README.md`: runbook and operating instructions.
  - `agentic-env/docs/CONTEXT.md`: canonical vocabulary and invariants.
  - `agentic-env/docs/adr/*.md`: irreversible design decisions.
