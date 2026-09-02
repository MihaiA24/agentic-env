# Agentic Environment Context

## Core terms

- **Agent stack**
  - The canonical local tooling set managed in this folder: `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `agentmemory`. `lean-ctx` was removed stack-wide on 2026-09-02 (ADR-0009).

- **Primary harness**
  - The agent the stack is chosen for and validated against: `omp`. Its wiring is the mandatory contract: installer-enforced, smoke-verified, and a stack-doctor failure. Every other agent is either a supported agent or an installed agent; neither drives tool selection.
  - _Avoid_: Default agent, main CLI, preferred agent

- **Supported agent**
  - An agent whose CLI, global skills, project-memory MCP configuration, and health checks are all managed by `agentic-env`. Authentication and credentials remain user-owned. The supported agents are Hermes and OMP; only OMP's wiring is mandatory (see Primary harness).
  - _Avoid_: Partially supported agent, authenticated agent

- **Installed agent**
  - An agent for which `agentic-env` installs a pinned CLI and the curated skills, and nothing more: no MCP configuration is written or diagnosed, and the doctor only warns when the binary is missing. The installed agents are Claude Code and Codex (measured need for managed wiring: zero; `DECISIONS_AI_TOOLING.md` Harness → "Agent tiers").
  - _Avoid_: Supported agent, secondary agent (unqualified)

- **Clean host**
  - A supported host with no prior agent-stack installation and a `~/.dotfiles` checkout present. The contract: `uv tool install --force . && agentic-bootstrap` yields exactly the documented stack with zero skill, MCP, or hook drift. Newer tool versions than the pins are tolerated drift; skill, MCP, and hook drift are not.
  - _Avoid_: Fresh machine (unqualified), blank VM

- **Machine provisioning**
  - The product boundary of `agentic-env`: install, configure, update, and diagnose the user-level agent stack. Repository initialization, indexing, project-memory maintenance, uninstall, and rollback remain outside the product boundary. Agent hook files are diagnosed but never written; the tools that install them own them.
  - _Avoid_: Project onboarding, project lifecycle management

- **Project memory stack**
  - The project context layer used by agents. On the primary harness: OMP core owns context I/O and search, Mnemopi holds narrative memory, and `codebase-memory-mcp` answers structural code-graph queries when its enable litmus fires. Hermes keeps `codebase-memory-mcp` and `agentmemory` wiring (unmeasured); installed agents get none.
  - _Avoid_: Memory MCP stack, AI context stack

## Stack lifecycle states

Every tracked tool or process is in exactly one state; the state names the bar for reopening its decision.

- **Adopted**
  - A component wired and on by default on the primary harness.
  - _Avoid_: Selected, installed (installation alone does not adopt)

- **Gated**
  - A component kept wired but off until a pre-registered trigger or litmus fires.
  - _Avoid_: Disabled, blocked

- **Parked**
  - A decision explicitly deferred with a named revisit condition or owner.
  - _Avoid_: Backlog, someday

- **Rejected**
  - A component evaluated and declined on graded evidence, including decline by its own pre-registered threshold; reopening requires new external evidence.
  - _Avoid_: Discarded, deprecated

- **Dormant**
  - A component known or installed but never evaluated; reopening requires only a stated reason.
  - _Avoid_: Discarded, rejected

- **Retired**
  - A process or source no longer operated because its measured yield did not justify it. Applies to workflows, not components.
  - _Avoid_: Rejected, abandoned

- **Agentmemory integration**
  - The managed agentmemory CLI and MCP registration used for narrative memory. The interactive `iii-engine` runtime is outside machine provisioning because its upgrade can mutate the current repository.
  - _Avoid_: iii-engine lifecycle management

- **Structural memory**
  - The indexed code graph used to answer questions about code shape, symbols, routes, callers, dependencies, and impact. On the primary harness it is enabled on demand for cross-repo, whole-graph, or architecture questions, not default-mounted.
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
  - A user-level MCP configuration entry named `codebase-memory-mcp` or `agentmemory` that `agentic-env` owns and converges to its curated definition while preserving unrelated agent settings. On OMP roots, `agentmemory` and `lean-ctx` are excluded entries: purged from `mcpServers` and kept in `disabledServers` so a re-import cannot mount them. Malformed configuration is rejected without modification.
  - _Avoid_: Any MCP entry, user-owned configuration

- **Read-interception policy**
  - A hook or instruction block that gates or redirects an agent's file reads and searches toward a query-first tool. Scoped per supported agent, counted across every configuration file that agent loads rather than the files in its own directory. At most one may be active for a given agent.
  - _Avoid_: Query-before-read hook, discovery gate, read redirect

- **Agent global skill**
  - A reusable `SKILL.md` installed in an agent's user-level skills directory so the agent knows when and how to use a tool.
  - _Avoid_: MCP server, project-local skill

- **Curated skill default**
  - The small reviewed set of skills installed by default for the supported agent workflow, selected per pack in the skill-pack manifest and installed once into the skill store, which every supported and installed agent reads; custom skill-pack configuration is the extension point for user-specific packs. Prompt exposure follows installation — there is no separate allowlist layer.
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
    - `agentic-bootstrap`
    - legacy split path:
      - `agentic-install-agents --all --yes`
      - `agentic-install-skills-mcps --all-mcps --yes`
      - `agentic-configure-agent-mcps --yes`
  - _Avoid_: Deployment (unqualified — means either fresh install or curated stack update)

- **Curated stack update**
  - A non-interactive maintenance run that converges every installed agent-stack component to the reviewed versions declared by `agentic-env`.
  - _Avoid_: Latest-available update, mixed pinned/latest update, fresh install, deployment (unqualified)

- **Provisioner upgrade**
  - Replacement of the installed `agentic-env` tool through `uv`, kept separate from a curated stack update because `uv` owns the provisioner's installation source and lifecycle.
  - _Avoid_: Stack update, self-replacing updater

- **Setup runner**
  - The shared `run_cmd` wrapper in `agentic-env/setup_helpers.sh` that keeps setup scripts quiet by default, prints command progress, and dumps captured output only on failure.
  - _Avoid_: Per-script command wrapper copies

- **Smoke test**
  - The fresh-install contract exercised in the Docker smoke environment (Debian bookworm) and on the supported hosts (macOS, CachyOS); it must pass before a host is accepted as supported.

- **Smoke contract**
  - Process succeeds when: tools are installed, binaries are callable, `agentic-stack-doctor` exits successfully (the OMP mandatory checks), and Hermes has its project memory stack servers and matching global skills.

- **Provisioning verification**
  - Evidence that deterministic command and configuration contracts pass focused tests and the complete agent stack passes the fresh-install smoke contract.
  - _Avoid_: Line coverage, mocked installer success

- **Stack doctor**
  - A read-only host diagnostic (`agentic-stack-doctor`) with two tiers. Mandatory checks cover the primary harness: OMP binaries and versions, both OMP `mcp.json` roots wired and gated (including the `node_repl` built-in) with excluded servers absent, `~/.claude.json` free of excluded servers and of read-interception prose (OMP imports it), the `config.yml` contract, each hook registered exactly once with its file present, the curated skill roster, and no `lean-ctx` skill directory. Secondary checks (Hermes wiring; Hermes, Claude Code, Codex, agentmemory binaries) only warn with a `TODO secondary` tag. It exits unsuccessfully with corrective commands only on a mandatory failure, never repairs, and runs as the final phase of `agentic-bootstrap` and `agentic-update-stack`.
  - _Avoid_: Smoke test, automatic repair

- **Supported host**
  - A macOS or Arch Linux-family machine, including CachyOS, on which the complete machine-provisioning and stack-doctor contracts are verified.
  - _Avoid_: Any Unix-like host, Debian-compatible host

- **Compatibility floor**
  - Host prerequisites required by the agent stack: Python 3.12+, Node.js 20+, `curl`, `git`, and trusted CA certificates. The Linux fresh-install smoke environment is Debian bookworm (`node:20-bookworm-slim`); supported hosts stay macOS and CachyOS.

- **Documentation scope**
  - `agentic-env/README.md`: runbook and operating instructions.
  - `agentic-env/DECISIONS_AI_TOOLING.md`: operative agent-stack decisions, one section per layer (harness, context I/O, compaction, memory, code graph, skills, hooks), each Decided → Why → Rejected → Revisit → Wiring.
  - `agentic-env/docs/CONTEXT.md`: canonical vocabulary and invariants.
  - `agentic-env/docs/adr/*.md`: irreversible design decisions.

## Skill lifecycle

Skill-specific states, distinct from the component lifecycle states above: a component adopts when wired on by default; a skill adopts on fit.

- **Installed (skill)**
  - Present in some skill store on this machine. Says nothing about whether it can fire or ever has.
  - _Avoid_: Available, active

- **Wired (skill)**
  - Has a mechanical trigger — forced injection, hook, or model-invocable frontmatter — that fires without the user remembering to invoke it.
  - _Avoid_: Enabled, configured

- **Adopted (skill)**
  - Kept in the curated skill default because it fits the user's workflows: a fit judgment by the user, never a usage-count threshold. Usage audits are diagnostic — they flag stale or duplicate skills for re-review.
  - _Avoid_: Proven, validated

- **Skill store**
  - `~/.agents/skills` — the canonical copy of every installed skill. `skills add` writes here and symlinks `~/.claude/skills/<name>` and `~/.hermes/skills/<name>` into it; Codex reads it directly. OMP mounts it through `~/.claude/skills` (`enableClaudeUser`), never as its own root (`enableAgentsUser: false`), so each skill is loaded once.
  - _Avoid_: Recovery store, backup, archive

## Skill usage measurement

- **User-invoked**
  - A skill activation explicitly requested by the user (slash command or named request), counted per top-level session.
  - _Avoid_: Explicit use, activation (unqualified)

- **Model-invoked**
  - A skill loaded by the model on its own judgment (registry `use_count`). Answers "does the model reach for it" — a different question than user-invoked.
  - _Avoid_: Registry use, load count

- **String-scan count**
  - Transcript matches on a skill name; overstates use by counting injected skill bodies, tool results, and discussion. Never a verdict input.
  - _Avoid_: Usage count (unqualified)
