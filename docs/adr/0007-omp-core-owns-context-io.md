# ADR 0007: OMP core owns context I/O; lean-ctx keeps only what it measurably carries

## Status
Accepted

## Context
`lean-ctx` was adopted as the "always on" context layer on the strength of a 60–90% token-reduction claim. Re-grading that claim against primary sources did not survive contact:

- The headline is a composite of unlike measurements — 59.9% CLI compression stitched to ~99% *cached map-mode* reads. Its own committed benchmark measures `git status` at 32.6%, not the README's 85%. Its "cached re-reads ~13 tokens" compares cached map/signatures output against a full raw file, not the same read twice. Graded **C**: first-party, baseline undisclosed.
- No independent party has ever measured it.

Meanwhile two independent, provider-billed campaigns measured what tools of this shape actually do to a bill, and the mechanism they identified applies directly:

- Prompt-cache traffic is ~87% of reconstructed cost. A layer that cannot touch cached re-reads cannot move the bill. (`arXiv:2607.12161`, 2,908 billed Claude Code runs, 103 tasks, 7 repositories, 3 models, hash-frozen holdout.)
- Local payload reduction does not predict end-to-end cost: Pearson r = 0.15. One arm removed 38% of raw tool-output tokens and cost 6.8% *more*.
- Compression corrupted verbatim edit anchors, cutting successful patch application from **27/40 to 15/40**.
- `lean-ctx`'s documented substitute, Headroom, measured **+48.4%** billed cost [+42.3, +55.0], with the penalty positive in all nine model × effort cells.
- LLMLingua — the one compressor with genuine peer-reviewed third-party reproductions — reproduces on chat QA, meetings and RAG. The two high-relevance studies that put it on a coding agent report degradation.

That last pair matters more here than anywhere else, because OMP's edit path is entirely anchor-based: `edit` verifies a four-hex content hash against a per-session snapshot store and performs stale-anchor recovery. A lossy compressor on the read path is precisely the failure mode that was measured.

Tool-by-tool, `lean-ctx` also duplicates the host. `ctx_read(mode=anchored)` restates `read`'s `[PATH#TAG]` output; `ctx_patch` restates `edit`'s hashline ops with its own independent anchors; `ctx_read(map/signatures)` restates `read`'s structural summary; `ctx_search`/`ctx_glob`/`ctx_tree`/`ctx_shell`/`ctx_expand`/`ctx_url_read` restate `grep`/`glob`/directory reads/`bash`/`artifact://`/URL reads; `ctx_knowledge` and `ctx_session` are a third memory owner. Eighteen tool schemas ride in every prompt to do it.

## Decision

**Revised 2026-07-28, before implementation, on measured usage.** The original decision gated `lean-ctx` to `ctx_compose`, `ctx_explore`, `ctx_overview` and `ctx_delta`. Session telemetry shows that was backwards: across 152 sessions and 25,182 tool calls, those four account for **115 calls**, while `ctx_shell` (1,729), `ctx_read` (1,263), `ctx_search` (475) and `ctx_execute` (387) account for 3,854. The original list would have removed everything in use and kept everything idle. It was inferred from a single session in which no `ctx_*` tool happened to be called, and generalised without checking.

The decision now: OMP core owns context I/O and `read`, `grep`, `glob` and `edit` remain authoritative. `lean-ctx` is retained for the tools that carry real traffic. **`ctx_patch` is dropped** — 175 calls, and it is the one tool that maintains file anchors independent of OMP's snapshot store, on precisely the path where anchor corruption was measured to cut patch application from 27/40 to 15/40. `ctx_knowledge` and `ctx_session` are dropped as a second memory owner (1 call each).

## Considered options

1. **Keep all 18 tools** — rejected only for `ctx_patch`, `ctx_knowledge` and `ctx_session`. The anchor argument is specific to `ctx_patch`; it does not extend to `ctx_shell` or `ctx_read`, which do not feed the edit path.
2. **Drop `lean-ctx` entirely** — rejected. It carries 18.7% of all tool calls across 17 of its 18 tools. The earlier reading that it was unused was a single-session artifact.
3. **Adopt Headroom instead** — rejected outright. Measured +48.4% billed cost by an independent campaign.

## Consequences

- Per-tool gating is required in each agent's MCP configuration. The pattern already exists on this host: `~/.codex/config.toml` carries `[mcp_servers.lean-ctx.tools.<name>]` blocks.
- The `lean-ctx` "Replace Mode (native tools denied)" block in `~/.claude/CLAUDE.md` directly contradicts this decision and is false on OMP, where native tools are not denied. It must be scoped to the harness where it is true.
- Cached rereads are retained, since `ctx_read` stays. What is given up is the independent anchor path: edits go through OMP `edit`, whose four-hex content hash is verified against the session snapshot store with stale-anchor recovery.
- **The original version of this ADR was wrong in exactly the way this document warns about.** It generalised from one observation instead of measuring, and it would have been implemented had the workflow not been profiled first. The profile is in `AI_CONTEXT_TOOLING_COMPARISON.md` (deleted 2026-08-19; in its git history) under "Your workflow, measured".
- The real lever is elsewhere and this ADR does not touch it: **68.6% of billed cost is cache reads.** No tool in the context-I/O layer can reach that slice; compaction, pruning, subagent offloading and shorter sessions can. Optimising context I/O is optimising at most 11.2% of the bill.
