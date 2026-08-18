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

- **Memory: Mnemopi stays default (user, 2026-08-11); bake-off Stage 1 executed same day — Hindsight wins the registered endpoint.** Zero-LLM Hindsight (pinned 0.9.0, $0 retain) on the 20-session dotfiles corpus: decision-recall **1/4 @OMP-wired 1,024 tok vs Mnemopi 0/4**; 2/4 + 1 partial @4,096; cross-project leakage **4/4 PASS** (`any_strict` unions hold, bank boundary holds). Binding constraint is OMP's 1,024-tok recall cap ≈ one chunk — `hindsight.recallMaxTokens: 4096` doubles successes at $0 LLM cost but injects up to ~3K more tokens/recall. Eliminated earlier: mem0 OSS, agentmemory (see research doc). **Stage 2 (retain-LLM, reflect, observations) blocked on an OpenAI-compatible key** — user's ChatGPT OAuth cannot drive Hindsight (needs a Bearer key on an OpenAI-compatible endpoint; verified 08-18: no local LLM server, no keys in env). Unblock paths: free-tier Gemini/Groq key ($0, recommended), OpenAI PAYG (≈cents for 309 KB corpus + 4 probes), or local Ollama 7B via `host.docker.internal:11434/v1` = "Hindsight keyless $0" arm (fair vs keyless Mnemopi, may under-represent extraction ceiling; the backing LLM is part of the measured arm — label it). Container stopped, image + `hindsight-bakeoff` volume kept (re-ingest 14 s). Switch decision stays with user. Full data: `agentic-env/docs/memory-backend-research.md`.
- **Memory, corrected by forensics (08-12): Mnemopi's 0/4 was a SILENT RETENTION GAP, not recall** — zero retains landed 07-13→08-11 (8 dotfiles sessions, `backend: mnemopi` wired throughout; #2320/#2322 class reproduced locally). Stage 1b replay on the now-populated bank: **1 PASS + 3 PARTIAL** ≈ Hindsight@4,096, reflect works keyless. Residual defects are opposite: Mnemopi = silent retention loss (canary, not tuning); Hindsight = recall budget (config). Standing risk: retention can die silently again — **retention canary wired 08-18** (`omp/hooks/retention-canary.ts`, registered in `extensions`): warns in-session when the project bank's newest row is ≥7 days older than the latest session across ≥2 sessions; replayed against the real gap it fires 07-26 instead of 08-11. ADR-0002 (decisions live in committed docs) remains the real safety net. Switch to Hindsight only if related-project memory sharing becomes a live need — the one thing Mnemopi structurally cannot do.
- Re-shop context I/O only when grep+LSP+scouts visibly fail on a real task.
- Paired OMP/Hermes benchmark only if OMP-primary ever needs to be definitive.
- `feat/agent-stack-measured-cleanup` pushed to origin 2026-08-11 (user: publish only, no merge). Merge-to-main decision still open — PR: https://github.com/MihaiA24/.dotfiles/pull/new/feat/agent-stack-measured-cleanup
