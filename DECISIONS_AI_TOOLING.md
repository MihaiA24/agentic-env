# Agent Stack — Operative Context

> Distilled 2026-08-11 from `AI_CONTEXT_TOOLING_COMPARISON.md` (deprecated, frozen — full evidence, grades, and methods in its git history). Binding ADRs: `agentic-env/docs/adr/0006`–`0008`.

## Live wiring (this machine)

- OMP: compaction `handoff` @ 150K, idle on, handoff-to-disk (bak `~/.omp/agent/config.yml.bak-tuning`)
- Hooks: `omp/hooks/verification-recorder.ts` + `cadence-governor.ts` (N=25; silent after 3 unheeded nudges)
- MCP: `mcpServers: {}` · `disabledServers: [agentmemory, node_repl, codebase-memory-mcp, lean-ctx]` (bak `mcp.json.bak-leanctx-drop`)
- Memory: `backend: mnemopi`, `polyphonicRecall: false` — single memory owner (ADR-0006)
- MCP + skill roster bind at instance start: after any `mcp.json` edit → `/mcp reload` or restart live omp instances
- Skills: curated at install time via `skill-packs.json`; `skills.enableAgentsUser: false` (`~/.agents/skills` = recovery store only)

## Rules (measured; violations cost real money)

1. Judge by success-adjusted billed cost, never token reduction (correlation r=0.15).
2. Cache reads ≈ 68.6% of bill — a tool that can't touch cached re-reads can't move it.
3. No lossy compressor on the read→edit path (anchor corruption: patch success 27/40 → 15/40).
4. One semantic-memory owner per agent. OMP LSP owns live symbol truth.
5. Wiring routes tools; prose doesn't (3×-repeated prompt mandate → 15.6% adherence).
6. Vendor claims measure at 1/8–1/3 of advertised, or negative — adopt only on locally measured, pre-registered endpoints.

## Verdicts (why the wiring looks like this)

- **Kept:** OMP-native I/O (`read`/`grep`/`glob`/`edit`/LSP + scout subagents); Ponytail (−10.3% cost, must force-inject); Caveman (−8.5%, on demand); Graphify (on demand).
- **Gated:** codebase-memory-mcp — enable per session only when the task needs >10 native calls, crosses repo boundaries, or aggregates the whole graph (`/mcp enable` + `fast` reindex). Litmus fired 0× since 08-05. Promotion: fires ~weekly in a project → default-on there.
- **Dropped by own pre-registered thresholds:** lean-ctx (1 semantic call < 5, ADR-0008 fallback), agentmemory (0 calls in 934 sessions), node_repl (0 calls).
- **Rejected on 3P evidence:** Headroom (+48.4% cost), rtk (wash), LLMLingua (degrades on code agents).
- **Round 2 full-market sweep (17 tools, 08-11): 0 adoptions** — no candidate ships 3P agent-on-repo evidence.

## Open

- **Memory bake-off DUE** — Mnemopi failed 4/4 decision-recall probes (flip trigger fired 08-11). Arms: Hindsight 0.9.0 self-hosted (PG/pgvector; cap the 4,096-tok default recall) vs mem0 OSS 2.0.17 (Qdrant+SQLite; 94.4% headline is managed-only per its own README) vs Mnemopi as control. Challengers are external stacks, not OMP-native, with vendor-published chat-memory numbers — switch only if one beats Mnemopi on pre-registered local endpoints (decision-recall probes, injected tokens/query, infra cost).
- Re-shop context I/O only when grep+LSP+scouts visibly fail on a real task.
- Paired OMP/Hermes benchmark only if OMP-primary ever needs to be definitive.
- User decision open: merge/push `feat/agent-stack-measured-cleanup`.
