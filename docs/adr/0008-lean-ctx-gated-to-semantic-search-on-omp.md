# ADR 0008: lean-ctx gated to semantic search only on OMP

## Status
Accepted 2026-08-05. Amends ADR-0007's retained-tool list. Supersedes ADR-0002's three-tool wiring on the primary harness only; secondary agents are untouched (their fate is parked with Q-F(a)).

**Fallback executed 2026-08-11**, on the pre-registered date: semantic-search calls since 2026-07-28 = 1 (one `ctx_search(action=semantic)` call, 08-10T18:32Z; the 08-10 sweep of all 54 sessions counted 0 before it) — below the fixed threshold of 5. `lean-ctx` is dropped from OMP entirely: the native `mcpServers.lean-ctx` entry removed from `~/.omp/agent/mcp.json` and `"lean-ctx"` added to `disabledServers` so the `~/.claude.json` import cannot resurface it (backup: `~/.omp/agent/mcp.json.bak-leanctx-drop`). Exploratory search falls back to `grep` + LSP + scout subagents. Re-shop for a semantic-search tool only when that path visibly fails on a real task. Secondary agents remain untouched.

## Context
ADR-0007 retained `lean-ctx` tools by measured call share: `ctx_shell` (1,729), `ctx_read` (1,263), `ctx_search` (475), `ctx_execute` (387). Grilled 2026-08-05, that criterion does not hold: **call share is usage, not benefit.** Every retained tool except semantic search has an OMP-native equivalent that absorbs its traffic — `read` (files, URLs, PDFs, directories), `bash`, `grep`, `glob`, `eval`, LSP, `edit`. The natives are prompt-cache-stable and feed OMP's own anchor snapshot store; the intercepted versions are neither.

Compression, the other claimed benefit, was re-checked and is not a benefit on OMP:
- Payload reduction does not predict billed cost: r = 0.15 over 2,848 billed runs (arXiv:2607.12161).
- A tool-output compressor can touch at most the ~11.2% new-input slice of the bill; cache reads are 68.6%.
- Compression on the read→edit path cut patch success 27/40 → 15/40; Headroom, the same shape of tool, measured +48.4% billed cost.

So the only axis on which `lean-ctx` can earn its mount is **capability**, and it has exactly one capability without a native equivalent: semantic (by-meaning) code search — `ctx_search(action=semantic)`.

Caveat recorded honestly: ADR-0007's 475 `ctx_search` calls pool regex, symbol, and semantic actions. The semantic-only share is unknown until the 2026-08-11 session-log read-out.

## Decision
On OMP, `lean-ctx` is mounted with a per-tool filter exposing only semantic search (`ctx_search` with `action=semantic`, plus its `reindex` maintenance action). Everything else is unexposed: no shadow-mode interception, no `ctx_read`/`ctx_shell`/`ctx_patch`/`ctx_knowledge`/`ctx_session` (the last three were already dropped by ADR-0007; this extends the drop to the rest).

Enforcement is **wiring, not prose** (measured: a 3×-repeated prose mandate achieves 15.6% adherence). The MCP tool filter is the mechanism; every "prefer ctx_*" or "native tools denied" instruction block is removed from context files OMP loads.

**Pre-registered fallback, set before data exists:** at the 2026-08-11 read-out, count semantic-search calls in sessions since 2026-07-28. Fewer than 5 → drop `lean-ctx` from OMP entirely and fall back to `grep` + LSP + scout subagents for exploratory search. The threshold is fixed now so the goalpost cannot move later.

## Considered options
1. **Drop `lean-ctx` entirely** — viable, and it is the pre-registered fallback. Not taken immediately because semantic search has no native substitute and the package is already installed, pinned, and indexed; keeping one tool costs a one-line filter.
2. **Status quo (shadow mode / broad tool list per ADR-0007)** — rejected. A second router on the read path is a standing rule-3/4 risk for a grade-C tool, and 18 tool schemas ride every cached prompt to duplicate the host.
3. **Replace with rtk or Headroom** — rejected as a category error. Both are compressors — alternatives to the half of `lean-ctx` being deleted, not the half being kept. Both are independently measured not to work (rtk: wash; Headroom: +48.4%).
4. **Shop for a dedicated semantic-search tool** — rejected. The discovery funnel measured trending-list yield at 0–1/20 qualifying; swap only when semantic search measurably fails, same trigger discipline as ADR-0006.

## Consequences
Written at acceptance (08-05), before the fallback executed. The items below describing an OMP semantic-only mount (per-harness installer wiring, the 18→1 schema tax) are superseded by the executed fallback in Status: OMP gets no `lean-ctx` entry at all and its schema tax is 0; secondary agents keep full wiring.

- ADR-0007's retention of `ctx_shell`/`ctx_read`/`ctx_execute` is reversed. Its own warning applied: it corrected a no-measurement error with a usage measurement, but usage was the wrong metric — replaceability is.
- The `~/.claude/CLAUDE.md` "Replace Mode (native tools denied)" block is now load-bearing wrong for this ADR and must be scoped to harnesses where it is true, or deleted (open item Q8).
- Installer and smoke contract must configure `lean-ctx` per-harness: full wiring for secondary agents (until Q-F(a) resolves), semantic-only filter on OMP. The per-tool gating pattern already exists in `~/.codex/config.toml` (`[mcp_servers.lean-ctx.tools.<name>]`).
- Implementation (2026-08-05, this host): OMP's `mcp.json` schema has no per-tool filter, so the gate is enforced server-side. `~/.omp/agent/mcp.json` defines an OMP-native `lean-ctx` entry (OMP-native config is highest-precedence; it shadows the imported `~/.claude.json` registration and its shadow-mode `instructions` prose) launching with `LEAN_CTX_TOOL_PROFILE=minimal` + `LEAN_CTX_DISABLED_TOOLS=ctx_read,ctx_shell,ctx_glob,ctx_tree,ctx_call` — `ctx_call` is lean-ctx's any-tool gateway and would bypass the gate. Verified by stdio `tools/list`: exactly `["ctx_search"]`. Action-level gating (semantic vs regex/symbol) is not enforceable at the tool boundary; prose in the retained skill body carries the semantic-only intent.
- The 18-schema prompt tax on OMP drops to 1.
- What is given up: cached re-reads (`ctx_read` map/signature modes). Accepted — the cache-read lever (68.6% of bill) belongs to compaction and session shape, not context I/O, per ADR-0007's own closing note.
