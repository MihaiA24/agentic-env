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
  - An agent for which `agentic-env` installs the CLI (latest release, verified against its reviewed version floor) and the curated skills, and nothing more: no MCP configuration is written or diagnosed, and the doctor only warns when the binary is missing. The installed agents are Claude Code and Codex (measured need for managed wiring: zero; `DECISIONS_AI_TOOLING.md` Harness → "Agent tiers").
  - _Avoid_: Supported agent, secondary agent (unqualified)

- **Clean host**
  - A supported host being provisioned from scratch, with no prior agent-stack installation or agent-specific configuration. It is the target of a fresh install, independent of any existing workstation’s installed tools or configuration.
  - _Avoid_: Fresh machine (unqualified), blank VM

- **Native host acceptance**
  - Verification of clean provisioning on the target host's own operating system and kernel, with acceptance state isolated from any existing agent stack. This is distinct from distro-container evidence, which exercises a container's userland on its host's kernel.
  - _Avoid_: Container acceptance, existing-stack health check

- **Machine provisioning**
  - The managed-stack operation: install, configure, update, and diagnose the user-level agent stack; distinct from standalone skill copying. Repository initialization, indexing, project-memory maintenance, uninstall, and rollback remain outside provisioning, and agent hook files are diagnosed rather than written.
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
  - A user-level MCP entry whose expected definition is tracked by `agentic-env`: missing entries are added, while mismatches in existing entries are reported for manual correction without overwriting them. Explicit primary-harness exclusion and gating policies still apply; malformed configuration is rejected without modification.
  - _Avoid_: Automatically repaired entry, any MCP entry

- **Read-interception policy**
  - A hook or instruction block that gates or redirects an agent's file reads and searches toward a query-first tool. Scoped per supported agent, counted across every configuration file that agent loads rather than the files in its own directory. At most one may be active for a given agent.
  - _Avoid_: Query-before-read hook, discovery gate, read redirect

- **Skill package**
  - A skill directory containing its `SKILL.md` and any supporting scripts or references; the unit copied by either installation route.
  - _Avoid_: Descriptor only, MCP server

- **Standalone skill copy**
  - A complete package copied into an explicitly chosen skills folder, outside managed-agent installation and its provenance, health checks and update lifecycle. Discovery and workflow compatibility belong to the destination harness.
  - _Avoid_: Managed installation, harness provisioning

- **Python-only skill copy**
  - The offline standalone-copy route for packages vendored in the checkout; remote-only packages are outside its scope. Windows copy acceptance applies to this operation, not to the agent stack.
  - _Avoid_: Full-stack Windows support, remote pack installation

- **Agent global skill**
  - A reusable `SKILL.md` installed in an agent's user-level skills directory so the agent knows when and how to use a tool.
  - _Avoid_: MCP server, project-local skill

- **Curated skill default**
  - The reviewed roster selected per pack in the skill-pack manifest, shared by managed installations and native-CLI standalone copying. The Python-only route is limited to its vendored subset; custom skill-pack configuration extends the native installer's selection without a separate prompt-exposure allowlist.
  - _Avoid_: Comprehensive skill catalog, skill marketplace

- **Checkout module command**
  - An installation, development or verification command run directly from the provisioner's checkout, without installing its command set into the user's environment.
  - _Avoid_: Root script wrapper, uv tool command, installed CLI

- **uv tool command**
  - A named CLI entry point installed by `uv tool install` and run from the user's PATH.
  - _Avoid_: Checkout module command

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
  - A non-interactive maintenance run that reinstalls every installed agent-stack component: floating components land on the current latest release, fixed-identity components stay at the reviewed artifact. The run fails if any result is below its reviewed version floor.
  - _Avoid_: Convergence to exact versions, mixed pinned/latest update, fresh install, deployment (unqualified)

- **Reviewed version floor**
  - The minimum acceptable installed version of a stack binary, declared in `stack_metadata.STACK_VERSION_FLOORS` and set to the latest stable release at review time. At or above the floor is compliant; below it fails install and the doctor. Distinct from _Compatibility floor_, which is about host prerequisites, not stack components.
  - _Avoid_: Version pin, exact-version match, tolerated drift

- **Fixed-identity artifact**
  - A stack component fetched by an identity that cannot float — an installer commit (Hermes) or a per-architecture SHA256-pinned release archive (`codebase-memory-mcp`) — because its fetch path is untrustworthy or its assets must be verified byte-for-byte. It moves only when this repo's reviewed metadata moves. Orthogonal to the version floor, which every component has.
  - _Avoid_: Pin (unqualified — ambiguous between the fetched artifact and the version floor)

- **Provisioner upgrade**
  - Replacement of the installed `agentic-env` tool through `uv`, kept separate from a curated stack update because `uv` owns the provisioner's installation source and lifecycle.
  - _Avoid_: Stack update, self-replacing updater

- **Setup runner**
  - The shared `run_cmd` wrapper in `agentic-env/setup_helpers.sh` that keeps setup scripts quiet by default, prints command progress, and dumps captured output only on failure.
  - _Avoid_: Per-script command wrapper copies

- **Smoke test**
  - An executable check with a declared operation and OS/architecture scope; passing one scope does not establish another. Full-stack acceptance follows the smoke contract, while skill-copy acceptance checks only package copying.

- **Smoke contract**
  - Process succeeds when: tools are installed, binaries are callable, `agentic-stack-doctor` exits successfully (the OMP mandatory checks), and Hermes has its project memory stack servers and matching global skills.

- **Provisioning verification**
  - Evidence that deterministic command and configuration contracts pass focused tests and the complete agent stack passes the fresh-install smoke contract.
  - _Avoid_: Line coverage, mocked installer success

- **Stack doctor**
  - Read-only diagnosis of the primary-harness wiring contract: OMP failures are mandatory, while Hermes wiring and secondary-agent binaries only warn. It runs at the end of bootstrap/update, exits unsuccessfully only for mandatory failures, and gives corrective guidance without repairing configurations.
  - _Avoid_: Smoke test, automatic repair

- **Supported host**
  - An OS/architecture target with successful clean-host provisioning evidence, not merely a compatible release asset. The intended targets are Apple Silicon macOS and Arch Linux x86_64; direct CachyOS verification is deferred, Intel macOS is outside acceptance scope, and Windows skill-copy evidence does not establish a supported provisioning host.
  - _Avoid_: Any Unix-like host, unverified compatible host

- **Compatibility floor**
  - The prerequisites needed before machine provisioning: Python 3.12+, Node.js 20+ with npm, uv, curl, git, trusted CA certificates, and writable user-level installation paths. The Python-only copy route has a separate, smaller prerequisite set; platform-specific requirements and acceptance evidence belong in the runbook.

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

- **Core (skill)**
  - An adopted skill named in a recipe's default step for its job. Who invokes it (model or user) is a separate property: _Wired_.
  - _Avoid_: Default, primary, spine

- **Escalation (skill)**
  - An adopted skill outside every recipe's default step; runs only when its named trigger fires, producing a stated work product. Distinct from _Gated_: gated is wired but off, escalation is on but not routed.
  - _Avoid_: Optional, conditional, gated

- **Excluded (skill)**
  - A skill deliberately not installed, with the reason and the condition that reopens it.
  - _Avoid_: Rejected (that is the component state), removed, pruned

- **Skill store**
  - `~/.agents/skills` — the canonical copy of every installed skill. `skills add` writes here and symlinks `~/.claude/skills/<name>` and `~/.hermes/skills/<name>` into it; Codex reads it directly. OMP mounts it through `~/.claude/skills` (`enableClaudeUser`), never as its own root (`enableAgentsUser: false`), so each skill is loaded once.
  - _Avoid_: Recovery store, backup, archive

- **Vendored pack**
  - A skill pack whose installed source is a copy kept in this repository, carrying the upstream commit it was taken from and the upstream licence. Pinned by the copy, not by an upstream ref; a bump is a deliberate re-copy. Contrast: an upstream-pinned pack installs from the author's repository at a tag.
  - _Avoid_: Fork, mirror, local pack

- **Recipe**
  - The per-job routing of skills for one kind of development task: which core skill runs, which escalations exist and what triggers them. Routing guidance, never a mandatory command chain.
  - _Avoid_: Pipeline, workflow chain, mode

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
