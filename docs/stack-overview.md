# The stack `agentic-env` defines — landscape map

What the stack is made of, what was surveyed for each part, and where to read the survey. Nothing here is a setting: the operative contract (what was selected, why, with what evidence and revisit trigger) is [`DECISIONS_AI_TOOLING.md`](../DECISIONS_AI_TOOLING.md). Vocabulary is [`CONTEXT.md`](CONTEXT.md). Operations are the [README](../README.md).

## Layers and what was surveyed

| Layer | Field surveyed | Survey | Selected (see DECISIONS) |
|---|---|---|---|
| Harness | OMP, Hermes, Claude Code, opencode, Codex | DECISIONS §1; paired OMP/Hermes benchmark parked | OMP, with three agent tiers |
| Context I/O | lean-ctx, Headroom, rtk, LLMLingua, Repomix, repo maps | [ADR-0007](adr/0007-omp-core-owns-context-io.md); [ADR-0008](adr/0008-lean-ctx-gated-to-semantic-search-on-omp.md) → [ADR-0009](adr/0009-lean-ctx-removed-from-stack.md) (lean-ctx lifecycle); DECISIONS §2 | Native OMP tools only |
| Compaction | Handoff/remote/soft method orders, 120K vs 150K thresholds | DECISIONS §3 | Handoff at 150K |
| Memory | Mnemopi, agentmemory, Hindsight, mem0 | [Memory backend research](memory-backend-research.md); [ADR-0006](adr/0006-mnemopi-owns-narrative-memory-on-omp.md); DECISIONS §4 | Mnemopi on OMP, agentmemory on Hermes |
| Code graph | codebase-memory-mcp, GitNexus, GraphRAG, cognee, Graphiti, Semantica, Serena | DECISIONS §5 | codebase-memory-mcp, gated off behind a litmus |
| Skills | Matt, pstack, ponytail and caveman | [Research and verification](skills-workflow-recheck-2026-09-21.md) | [38 skills, routed by job](../DECISIONS_AI_TOOLING.md#6-skills) |
| Hooks | verification-recorder, retention-canary, cadence-governor | DECISIONS §7 | The first two; cadence-governor rejected on measured non-adherence |
| Project memory | Per-repo use of the above | [Project memory stack](project-memory-stack.md) | Template, not a machine setting |

Where a survey and DECISIONS disagree, DECISIONS is operative — the surveys are dated inputs, the contract is the decision.

## Reading order

1. [`DECISIONS_AI_TOOLING.md`](../DECISIONS_AI_TOOLING.md) — the contract: one section per layer (Decided → Why → Rejected → Revisit → Wiring), the live wiring for this machine, and the pre-registered upstream triggers.
2. [`README.md`](../README.md) — the commands, the version policy, the runbooks, and the clean-platform acceptance matrix.
3. [`docs/CONTEXT.md`](CONTEXT.md) — the domain vocabulary; [`docs/adr/`](adr/) — the decisions that needed their own record.
4. The surveys above — only when reopening a layer, which requires its revisit trigger to fire.

## Installation runbooks

- [Choose a route](../README.md#choose-an-installation-path): full-stack provisioning, managed skill refresh, native-CLI directory copies, or Python-only copies.
- [Windows/offline copying](../README.md#python-only-copy-on-windows): vendored packages without installing the stack.
- [Standalone-copy maintenance](../README.md#verify-and-refresh-standalone-copies): verify discovery, preserve local edits and refresh into a new directory.
- [Acceptance evidence](../README.md#ci-and-recorded-evidence): full-stack platform checks and the separately scoped Windows copy check.
