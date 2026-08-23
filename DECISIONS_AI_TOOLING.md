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
| Skills | Fit-curated roster (see Skills section): Pocock spine + Ponytail forced + Caveman/Graphify on demand + 4 pstack picks | Fit-judged by user; audits prune | Full Pocock 25 + pstack 44 stores | Fit audit flags stale |
| Hooks | verification-recorder, retention-canary | Pass-rate read-outs; silent-memory-loss tripwire | cadence-governor (rejected 08-19), external monitoring | Recorder DB unread by next read-out; canary false-warns |

## Live wiring (this machine)

- OMP: compaction `handoff` @ 150K, idle on, handoff-to-disk (bak `~/.omp/agent/config.yml.bak-tuning`)
- Hooks: `omp/hooks/verification-recorder.ts` + `retention-canary.ts` (memory staleness tripwire)
- MCP: `mcpServers: {}` · `disabledServers: [agentmemory, node_repl, codebase-memory-mcp, lean-ctx]` (bak `mcp.json.bak-leanctx-drop`)
- Memory: `backend: mnemopi`, `polyphonicRecall: false` — single memory owner (ADR-0006)
- MCP + skill roster bind at instance start: after any `mcp.json` edit → `/mcp reload` or restart live omp instances
- Skills: curated at install time via `skill-packs.json`; `skills.enableAgentsUser: false` (`~/.agents/skills` = recovery store only). Local one-off skills (graphify) live in the agent skill roots directly, outside packs.

## Rules (measured; violations cost real money)

1. Judge by success-adjusted billed cost, never token reduction (correlation r=0.15).
2. Cache reads ≈ 68.6% of bill — a tool that can't touch cached re-reads can't move it.
3. No lossy compressor on the read→edit path (anchor corruption: patch success 27/40 → 15/40).
4. One semantic-memory owner per agent. OMP LSP owns live symbol truth.
5. Wiring routes tools; prose doesn't (3×-repeated prompt mandate → 15.6% adherence; cadence-governor nudges 16.4% ≈ chance).
6. Vendor claims measure at 1/8–1/3 of advertised, or negative — adopt only on locally measured, pre-registered endpoints.
7. Decisions live in committed docs; memory is convenience.
8. Skills are adopted on workflow fit (user judgment); usage audits are diagnostic — they flag stale or duplicate skills for re-review, never gate adoption. Rule 6 governs tools only. Usage units are canonical in `docs/CONTEXT.md`: user-invoked ≠ model-invoked ≠ string-scan.

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

## Skills (settled 2026-08-22)

Criterion: workflow fit, judged by the user. The 2026-08-20 fit audits (`docs/pocock-skills-fit-report.html`, `docs/pstack-skills-audit.html`) are diagnostic input, committed with adjudication addenda.

**Audit adjudication (08-22, raw DBs):** both reports honest, units systematically mixed. 567 OMP "sessions" = 226 main + 341 subagent. grill-with-docs: 74 OMP session files / 215 Hermes sessions user-invoked (413 = registry loads). tdd/code-review: 0 user-invoked vs 108/320 model-invoked — the model reaches for them, the user never does; don't force slash commands. Only verification DBs reproduced exactly (OMP 527 @ 87.3% pass, Hermes 248): dedicated event tables beat string scans. Glossary of counting units: `docs/CONTEXT.md`.

**Adopted 08-22 (vanilla first; adapt only after real friction):**
- `resolving-merge-conflicts`, `diagnosing-bugs` (Pocock) — sat on measured pains (merge churn: 64+ merges with conflict fallout; repeat-diagnosis loops) while structurally unavailable in OMP (recovery store only, `enableAgentsUser: false`). Their low use was availability, not misfit.
- `create-verification-skill` (pstack) — the only genuine capability gap either audit found: verification is test/lint-centric; no user-journey checks on Paw app/portal/course sites.
- `show-me-your-work` (pstack) — decision trails (Run Records, sealed proofs) are hand-rolled per repo today.
- `reflect` (pstack) — the manual retrospective→skill-patch loop (137 patches on code-review), automated.
- `recall` (pstack) — installed manual-only (ships `disable-model-invocation: true`). Forensic tool for canary-fires events; never wired (Rule 4, single memory owner).

**Pruned from pack:** `to-spec`, `to-tickets` — 1 use each in 5 months; grill-with-docs + wayfinder already emit specs and tickets.

**Rejected (and why):**
- pstack duplication cluster (poteto-mode, laziness-protocol, subtract-before-you-add, minimize-reader-load, no-comments) — duplicates benchmarked ponytail (−10.3%) / caveman (−8.5%); double style injection = paid prompt weight; no-comments contradicts load-bearing `ponytail:` ceiling markers. Novel fragments fold into ponytail text, never a second skill.
- pstack blast-radius, swarm — OMP-native subagent fan-out already covers both; a skill adds prompt weight over a proven native flow.
- grill-me — grill-with-docs is a proven superset, including non-code decisions (this decision session ran on it).
- handoff-as-deliberate-habit — compaction wiring (150K handoff) covers fragmentation mechanically; "remember to invoke at seams" is prose, and prose doesn't route (Rule 5). Skill stays installed for on-demand use.
- writing-for-agents — doc-drift pain is real but the skill is prose discipline, no mechanism; revisit if drift persists.
- pstack recall-as-wired-hedge — Rule 4 violation; retention-canary covers detection; upstream #8940 telemetry would retire even the canary.
- wait-what, to-questionnaire, ask-matt, wizard — no observed need in 5 months / 1,000+ sessions.

**Revisit:** next fit audit, or when a pruned skill's pain resurfaces. pstack Tier 1 leftovers (why, automate-me, interrogate, arena, technical-writing) reopen only if an adopted pstack pick earns its keep.

## Parked

- **Secondary-agent stack** (Hermes / Claude Code / Codex: lean-ctx + agentmemory + codebase-memory-mcp) — untouched, unmeasured on those harnesses. Revisit when a secondary harness becomes primary for any project, or agentmemory shows nonzero use.
- Paired OMP/Hermes benchmark — only if OMP-primary ever needs to be definitive.
- Context I/O re-shop — only when grep+LSP+scouts visibly fail on a real task.
