# Agent Stack — Decisions

> Sole operative doc. 2026-08-19: absorbed `AGENT_STACK.md` + `TOOLS_RESEARCH.md` (deleted); the frozen evidence ledger `AI_CONTEXT_TOOLING_COMPARISON.md` was deleted the same day — full evidence, grades, and methods live in its git history. Binding ADRs: `agentic-env/docs/adr/0006`–`0008`.

## The stack

| Layer | Decided | Why | Alternatives | Revisit when |
|---|---|---|---|---|
| Harness | OMP | Best model + LSP + edit anchors | Hermes, Claude Code, opencode, Codex | Never unless OMP fails |
| Context I/O | OMP native only | Cache-stable, anchor-safe; compressors break edits | lean-ctx (rejected), Headroom, rtk | Native tools visibly fail |
| Compaction | handoff @ 150K, idle on, save-to-disk | −43–50% tokens, quality held | 120K threshold | End-green < 88% → revert |
| Memory | Mnemopi + retention-canary hook | Recall good, keyless, zero infra; canary covers silent-loss defect | Hindsight (sole challenger), mem0, agentmemory, Letta, Zep | Cross-project memory sharing needed → Hindsight |
| Code graph | codebase-memory-mcp gated off | Costs quality, 10× tokens | GitNexus, GraphRAG, Serena, etc. | Litmus fires weekly |
| Skills | Ponytail forced, Caveman + Graphify on demand; curated roster | Only measured savers | Full 53-skill store | Measured harm |
| Hooks | verification-recorder, retention-canary | Pass-rate read-outs; silent-memory-loss tripwire | cadence-governor (rejected 08-19), external monitoring | Recorder DB unread by next read-out; canary false-warns |

## Live wiring (this machine)

- OMP: compaction `handoff` @ 150K, idle on, handoff-to-disk (bak `~/.omp/agent/config.yml.bak-tuning`)
- Hooks: `omp/hooks/verification-recorder.ts` + `retention-canary.ts` (memory staleness tripwire)
- MCP: `mcpServers: {}` · `disabledServers: [agentmemory, node_repl, codebase-memory-mcp, lean-ctx]` (bak `mcp.json.bak-leanctx-drop`)
- Memory: `backend: mnemopi`, `polyphonicRecall: false` — single memory owner (ADR-0006)
- MCP + skill roster bind at instance start: after any `mcp.json` edit → `/mcp reload` or restart live omp instances
- Skills: curated at install time via `skill-packs.json`; `skills.enableAgentsUser: false` (`~/.agents/skills` = recovery store only)

## Rules (measured; violations cost real money)

1. Judge by success-adjusted billed cost, never token reduction (correlation r=0.15).
2. Cache reads ≈ 68.6% of bill — a tool that can't touch cached re-reads can't move it.
3. No lossy compressor on the read→edit path (anchor corruption: patch success 27/40 → 15/40).
4. One semantic-memory owner per agent. OMP LSP owns live symbol truth.
5. Wiring routes tools; prose doesn't (3×-repeated prompt mandate → 15.6% adherence; cadence-governor nudges 16.4% ≈ chance).
6. Vendor claims measure at 1/8–1/3 of advertised, or negative — adopt only on locally measured, pre-registered endpoints.
7. Decisions live in committed docs; memory is convenience.

## Verdicts

- **Kept:** OMP-native I/O (`read`/`grep`/`glob`/`edit`/LSP + scout subagents); Ponytail (−10.3% cost, must force-inject); Caveman (−8.5%, on demand); Graphify (on demand).
- **Gated:** codebase-memory-mcp — enable per session only when the task needs >10 native calls, crosses repo boundaries, or aggregates the whole graph (`/mcp enable` + `fast` reindex). Litmus fired 0× since 08-05. Promotion: fires ~weekly in a project → default-on there.
- **Rejected by own pre-registered thresholds:** lean-ctx (1 semantic call < 5, ADR-0008 fallback), agentmemory (0 calls in 934 sessions), node_repl (0 calls).
- **Rejected on measured non-adherence (2026-08-19): cadence-governor.** Across 589 session logs: verification nudge 16.4% adherence within 10 calls, declining by fire number (17.5% → 10.6% → 8.7%) — at or below the ~22% chance rate of any 10-call window containing a verification command; overwrite-steer 15% immediate switch (n=20). The 08-11 read-out's sole positive signal (first-fire 59% verify ≤25 calls) came with 60% of all fired nudges being spam beyond N=75 — the 3-strike cap treated the symptom. Prose doesn't route (Rule 5). Reopen bar: a mechanism that routes (blocks/redirects) rather than nudges.
- **Rejected on 3P evidence:** Headroom (+48.4% cost), rtk (wash), LLMLingua (degrades on code agents).
- **Rejected / not pursued (catalog):** memory — mem0, MemPalace, Letta, Zep (unproven claims, wrong lane, or paid-only) · code graph — GitNexus, GraphRAG, cognee, Graphiti, Semantica, Serena (no coding evidence, license, or paid) · compression — Context Mode, mcp-compressor, OmniRoute, pxpipe (duplicate native, unproven, or unneeded) · repo summaries — aider repomap, Repomix (not pursued).
- **Round 2 full-market sweep (17 tools, 08-11): 0 adoptions** — no candidate ships 3P agent-on-repo evidence.

## Memory (settled 2026-08-19)

- **Mnemopi stays default** (user, 2026-08-11). Stage 1 (08-11): zero-LLM Hindsight won the registered endpoint (decision-recall 1/4 @1,024 tok vs 0/4; cross-project isolation 4/4 PASS). Forensics (08-12): Mnemopi's 0/4 was a **silent retention gap**, not recall — zero retains 07-13→08-11 despite correct wiring. Stage 1b replay on the populated bank ≈ parity (1 PASS + 3 PARTIAL; reflect works keyless). Gap differential (08-17) ruled out version, cadence, config, drift, and hooks. Full data: `agentic-env/docs/memory-backend-research.md`.
- Residual defects are opposite: Mnemopi = silent retention loss → **retention canary wired 08-18**; Hindsight = recall budget (config).
- **Stage 2 bake-off: skipped (user, 2026-08-19).** Was blocked on an OpenAI-compatible key; Stage 1b parity + the canary cover the residual risk. Unblock paths stay documented in the research doc if reopened.
- **Upstream issue filed 2026-08-19:** https://github.com/can1357/oh-my-pi/issues/8940 — silent retention gap + differential; asks for retain-attempt telemetry (which, if shipped, retires the canary).
- Switch trigger: related-project memory sharing becomes a live need → Hindsight (the one thing Mnemopi structurally cannot do).

## Parked

- **Secondary-agent stack** (Hermes / Claude Code / Codex: lean-ctx + agentmemory + codebase-memory-mcp) — untouched, unmeasured on those harnesses. Revisit when a secondary harness becomes primary for any project, or agentmemory shows nonzero use.
- Paired OMP/Hermes benchmark — only if OMP-primary ever needs to be definitive.
- Context I/O re-shop — only when grep+LSP+scouts visibly fail on a real task.

## Open

- Merge `feat/agent-stack-measured-cleanup` to main — user's call. PR: https://github.com/MihaiA24/.dotfiles/pull/new/feat/agent-stack-measured-cleanup
