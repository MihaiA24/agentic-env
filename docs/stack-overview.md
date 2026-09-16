# The stack `agentic-env` defines

One command sets up a machine to code with AI agents the way we have decided works. Every piece is pinned, every rejection was measured, and a doctor checks the result.

This page is the plain-language summary. Evidence, thresholds, and the exact config lines live in [`DECISIONS_AI_TOOLING.md`](../DECISIONS_AI_TOOLING.md), which is the operative document; vocabulary in [`CONTEXT.md`](CONTEXT.md). When the two disagree, DECISIONS wins.

## The seven layers

| Layer | Choice | Reason |
|---|---|---|
| Harness | OMP (Oh My Pi) | Best model access, LSP, anchored edits |
| Context I/O | OMP native tools only | Nothing on the read→edit path; compressors break edits |
| Compaction | Handoff at 150K tokens | −43–50% tokens with quality held |
| Memory | Mnemopi + retention canary | Keyless, zero infra, recall good |
| Code graph | codebase-memory-mcp, off by default | 10× tokens on ordinary tasks |
| Skills | 25 skills, four packs, fit-curated | Adopted on workflow fit, pruned by audit |
| Hooks | verification-recorder, retention-canary | Pass-rate read-outs; silent-memory-loss tripwire |

### Harness — OMP, primary

OMP won on tooling, not on model: LSP-backed navigation and hashline-anchored edits. Hermes, Claude Code, opencode, and Codex all lost on the same axis. Revisited only if OMP fails.

Three agent tiers follow from that:

- **Primary harness — OMP.** Installer-enforced, smoke-verified. Any drift in its wiring is a doctor failure.
- **Supported agent — Hermes.** CLI, skills, MCP config, and health checks are managed; the doctor only warns. Keeps its own memory (agentmemory) and code-graph MCPs.
- **Installed agents — Claude Code, Codex.** Pinned CLI plus the curated skills, nothing else. No MCP config is written or diagnosed; the doctor warns only when the binary is missing.

### Context I/O — native only

OMP's own `read`/`grep`/`glob`/`edit`, the LSP, and scout subagents. Nothing sits between reading a file and editing it. Two measured rules drive this: cache reads are roughly 69% of the bill, and a compressor cannot touch a cached re-read; lossy compression corrupted edit anchors (patch success fell from 27/40 to 15/40).

Rejected: lean-ctx (removed stack-wide, ADR-0009), Headroom (+48% cost), rtk (a wash), LLMLingua (degrades on code), Repomix and repo maps (not pursued). Any read-interception prose in a config OMP loads is a doctor failure.

### Compaction — handoff at 150K

Handoff summary at 150K tokens, idle compaction on, handoff saved to disk. Method order handoff → remote → soft. A 120K threshold gave the same quality with less headroom. Revert if end-green quality drops under 88%.

### Memory — Mnemopi, one owner per agent

Mnemopi stays the OMP memory backend: recall is good, it needs no API key and no infrastructure. Its one known defect is silent retention loss (a month of zero retains despite correct wiring), which the retention-canary hook now detects. Polyphonic recall is off.

agentmemory is rejected on OMP (0 calls in 934 sessions; ADR-0006 single memory owner) but stays wired on Hermes as that agent's memory provider. Hindsight is the sole challenger, and only if cross-project memory sharing becomes a real need.

### Code graph — codebase-memory-mcp, gated off

Installed and registered on both OMP roots but disabled by default: it costs answer quality and about 10× tokens on ordinary tasks. Enable per session when the task needs more than ten native calls, crosses repository boundaries, or aggregates the whole graph. That litmus has fired zero times since August 2026; if it stays at zero by 2026-10-01 the server comes off the OMP roots (still installed for per-project mounting).

### Skills — 32, fit-curated by job

One skill store on disk, symlinked into every agent, loaded by OMP once through the Claude root. Each installed skill is **Core** (named in a recipe's default step) or an **Escalation** (runs only on its trigger); the roster table with triggers and work products, the six recipes A–F, and every **Excluded** skill with its reopen condition live in [`DECISIONS_AI_TOOLING.md` §6](../DECISIONS_AI_TOOLING.md).

- **mattpocock (15):** wayfinder, grill-with-docs, grilling, domain-modeling, codebase-design, tdd, diagnosing-bugs, code-review (core); research, prototype, to-spec, to-tickets, resolving-merge-conflicts, handoff, teach (escalations).
- **ponytail (6):** anti-over-engineering mode plus audit, debt, gain, help, review. Force-injected; measured −10.3% cost.
- **caveman (2):** terse output on demand; measured −8.5%. Pinned to the benchmarked v2.3.1 text.
- **pstack (9, vendored):** how (core for "how does X work"); why, blast-radius, interrogate, unslop, create-verification-skill, show-me-your-work, reflect, recall (escalations). All `/`-only by upstream design.

Skills are adopted on fit for a named job as judged by the user; usage history is a diagnostic footnote. Review standards for `code-review`'s Standards axis: [`CODING_STANDARDS.md`](../CODING_STANDARDS.md). Notable exclusions: `implement` (its pre-commit review silently omits WIP), `architect`/`arena` (reopen for a genuinely new module shape), `swarm` (OMP fan-out covers it), pstack `tdd`/`teach` (name collisions with the Pocock skills that hold the job), the `principle-*` skills (condensed into the standards file).

Selection evidence: [Matt Pocock + pstack for efficient development](skills-development-comparison.md) (per-job comparison of all 84 skills; where its recommendations differ from §6, §6 is operative) and the earlier [source and installation review](skills-fit-review.md) (historical).

### Hooks — two

`verification-recorder` writes every verification event to a dedicated table (527 events at 87.3% pass on OMP, which beat string-scanning session logs). `retention-canary` trips when Mnemopi stops retaining. Both live in the dotfiles `omp/hooks/` directory; the stack checks they are registered exactly once and present, but never writes them.

Rejected: cadence-governor. Its verification nudges were followed 16.4% of the time within ten calls, at or below chance — prose does not route behaviour, wiring does.

## What is pinned

| Component | Version |
|---|---|
| OMP | 18.1.14 |
| Hermes Agent | 0.21.0 (`29112bef`) |
| Claude Code | 2.1.258 |
| OpenAI Codex | 0.153.4 |
| codebase-memory-mcp | 0.9.0 |
| agentmemory | 0.9.29 |
| skills CLI | 1.5.16 |
| mattpocock/skills | v1.2.3 |
| JuliusBrussee/caveman | v2.3.1 |
| DietrichGebert/ponytail | v4.9.0 |
| cursor/plugins (pstack) | vendored copy at `c1c0a32` (2026-09-14), `agentic_env/vendored/pstack/UPSTREAM.md`; upstream publishes no tags (ADR-0010) |

Remote install scripts are checksum-pinned; npm packages are version-pinned. Every remote reference must be pinned or carry a written reason for floating.

## Where things land on a machine

| Path | Content |
|---|---|
| `~/.omp/agent/config.yml` | OMP settings contract: memory backend, compaction, skill roots, hooks |
| `~/.omp/agent/mcp.json`, `~/.pi/agent/mcp.json` | codebase-memory-mcp registered; `disabledServers` = codebase-memory-mcp, node_repl, agentmemory, lean-ctx |
| `~/.agents/skills` | The skill store (canonical copy of every installed skill) |
| `~/.claude/skills`, `~/.hermes/skills` | Symlinks into the store; OMP loads via the Claude root |
| `~/.omp/agent/skills`, `~/.pi/agent/skills` | Built-in descriptors for codebase-memory-mcp, agentmemory, ponytail |
| `~/.hermes/config.yaml` | Hermes MCP entries (codebase-memory-mcp, agentmemory) and memory provider |
| `~/.claude.json` | Must not contain excluded servers or read-interception prose |
| `~/.dotfiles/omp/hooks/` | Hook sources, owned by the dotfiles repo |

## Lifecycle

- **`agentic-bootstrap`** — install agents → install skills and MCPs → configure → doctor. Four fixed phases, each skippable, dry-run available.
- **`agentic-update-stack`** — reconverge everything already installed to the pins (never "latest"), then doctor.
- **`agentic-stack-doctor`** — read-only. Exit code reflects the OMP contract only; Hermes, Claude, and Codex findings are tagged `TODO secondary`.

Configuration ownership: existing user files are never rewritten. Missing MCP entries are added; mismatched ones are reported for manual correction. An existing OMP `config.yml` is read-only; a missing one is seeded from the contract, and only when the hook files are present.

## Guarantees

- A clean host with a `~/.dotfiles` checkout, after `uv tool install --force . && agentic-bootstrap`, yields exactly this stack.
- Versions may run ahead of the pins (the doctor warns); skill, MCP, and hook drift may not.
- Acceptance runs in CI on a Debian bookworm container, native macOS 15 on Apple Silicon, and an Arch Linux container. Intel macOS is out of scope; direct CachyOS verification is deferred.

## What would change it

Each layer carries a pre-registered trigger; nothing moves without one firing:

- OMP major release → re-verify the config contract against the new settings schema, re-pin, re-run the smoke.
- oh-my-pi #8940 (retain-attempt telemetry) ships → retire the retention canary.
- Code-graph litmus still zero on 2026-10-01 → remove codebase-memory-mcp from the OMP roots.
- Semantic search visibly missing on a real task → reinstall lean-ctx ≥ 3.10.0 behind an OMP-native gate.
- Cross-project memory becomes a live need → Hindsight vs mem0 bake-off.
- mattpocock ships `retro` → fit audit against pstack `reflect`, keep one.
- End-green quality under 88% → revert compaction tuning.
