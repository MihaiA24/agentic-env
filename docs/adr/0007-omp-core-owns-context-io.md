# ADR 0007: OMP core owns context I/O; lean-ctx keeps only what it measurably carries

## Status
Accepted

## Context
`lean-ctx` was adopted as the "always on" context layer on the strength of a 60–90% token-reduction claim. Re-graded against primary sources, the claim fails:

- The headline combines unlike measurements: 59.9% CLI compression joined to ~99% *cached map-mode* reads. Its own committed benchmark measures `git status` at 32.6%, not the README's 85%. Its "cached re-reads ~13 tokens" figure compares cached map/signatures output against a full raw file, not the same read twice. Graded **C**: first-party, baseline undisclosed.
- No independent party has ever measured it.

Meanwhile two independent campaigns, billed by the provider, measured what tools of this kind do to a bill. The mechanism they found applies directly:

- Prompt-cache traffic (cache writes plus reads) is ~87% of reconstructed cost, about 80% of the actual bill. A layer that cannot touch cached re-reads cannot move the bill. (`arXiv:2607.12161`, 2,908 billed Claude Code runs, 2,848 analyzed, 103 tasks, 7 repositories, 3 models, hash-frozen holdout.)
- Local payload reduction does not predict end-to-end cost: Pearson r = 0.15. One arm removed 38% of raw tool-output tokens and cost 6.8% *more*.
- Compression corrupted verbatim edit anchors and cut successful patch application from **27/40 to 15/40**.
- Headroom, the substitute `lean-ctx` documents, measured **+48.4%** billed cost [+42.3, +55.0]. The penalty was positive in all nine model × effort cells.
- LLMLingua is the one compressor with genuine peer-reviewed third-party reproductions. It reproduces on chat QA, meetings and RAG. The two high-relevance studies that test it on a coding agent report degradation.

That last pair matters most here, because OMP's edit path is entirely anchor-based. `edit` verifies a four-hex content hash against a per-session snapshot store and recovers stale anchors. A lossy compressor on the read path is exactly the failure mode that was measured.

Tool by tool, `lean-ctx` also duplicates the host. `ctx_read(mode=anchored)` repeats `read`'s `[PATH#TAG]` output. `ctx_patch` repeats `edit`'s hashline ops with its own independent anchors. `ctx_read(map/signatures)` repeats `read`'s structural summary. `ctx_search`/`ctx_glob`/`ctx_tree`/`ctx_shell`/`ctx_expand`/`ctx_url_read` repeat `grep`/`glob`/directory reads/`bash`/`artifact://`/URL reads. `ctx_knowledge` and `ctx_session` are an extra memory owner beside Mnemopi. To do this, it puts eighteen tool schemas in every prompt.

## Decision

**Revised 2026-07-28, before implementation, on measured usage.** The original decision gated `lean-ctx` to `ctx_compose`, `ctx_explore`, `ctx_overview` and `ctx_delta`. Session telemetry shows that was backwards. Across 152 sessions and 25,182 tool calls, those four account for **115 calls**, while `ctx_shell` (1,729), `ctx_read` (1,263), `ctx_search` (475) and `ctx_execute` (387) account for 3,854. The original list would have removed every tool in use and kept every idle one. It was inferred from a single session in which no `ctx_*` tool happened to be called, then generalised without checking.

The decision now: OMP core owns context I/O, and `read`, `grep`, `glob` and `edit` stay authoritative. `lean-ctx` stays for the tools that carry real traffic. **`ctx_patch` is dropped** (175 calls). It is the one tool that keeps file anchors separate from OMP's snapshot store, on the same path where anchor corruption cut patch application from 27/40 to 15/40. `ctx_knowledge` and `ctx_session` are dropped as an extra memory owner beside Mnemopi (1 call each).

## Considered options

1. **Keep all 18 tools** — rejected only for `ctx_patch`, `ctx_knowledge` and `ctx_session`. The anchor argument applies only to `ctx_patch`. It does not extend to `ctx_shell` or `ctx_read`, which do not feed the edit path.
2. **Drop `lean-ctx` entirely** — rejected. It carries 18.7% of all tool calls across 17 of its 18 tools. The earlier finding that it was unused came from a single session.
3. **Adopt Headroom instead** — rejected outright. An independent campaign measured +48.4% billed cost.

## Consequences

- Each agent's MCP configuration needs per-tool gating. The pattern already exists on this host: `~/.codex/config.toml` has `[mcp_servers.lean-ctx.tools.<name>]` blocks.
- The `lean-ctx` "Replace Mode (native tools denied)" block in `~/.claude/CLAUDE.md` contradicts this decision and is false on OMP, which does not deny native tools. It must be scoped to the harness where it is true.
- Cached rereads stay, because `ctx_read` stays. What is given up is the independent anchor path: edits go through OMP `edit`, which verifies its four-hex content hash against the session snapshot store and recovers stale anchors.
- **The original version of this ADR was wrong in exactly the way this document warns about.** It generalised from one observation instead of measuring. It would have been implemented if the workflow had not been profiled first. The profile is in `AI_CONTEXT_TOOLING_COMPARISON.md` (deleted 2026-08-19; in its git history) under "Your workflow, measured".
- The biggest cost is elsewhere, and this ADR does not address it: **68.6% of billed cost is cache reads** on this host's measured OMP sessions. That local figure counts cache reads only; the ~87% above is the paper's figure for all cache traffic on its benchmark. No tool in the context-I/O layer can reach that share; compaction, pruning, subagent offloading and shorter sessions can. Optimising context I/O optimises at most 11.2% of the bill.
