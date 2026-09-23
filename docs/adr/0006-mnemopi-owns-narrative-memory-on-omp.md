# ADR 0006: Mnemopi owns narrative memory on the primary harness

## Status
Accepted

## Context
`AI_CONTEXT_TOOLING_COMPARISON.md` (advisory, snapshot 2026-07-24; deleted 2026-08-19, full ledger in its git history) ranks Hindsight first for the memory layer at evidence grade A, citing ~91.4% LongMemEval answer accuracy. The grade fails on checking. The comparison calls the result "independently reproduced", but both cited sources are first-party: the vendor's repository and `arXiv:2512.12818`, authored by Vectorize. It is a vendor benchmark on a public corpus. OMP 17.1.5 accepts `off | local | hindsight | mnemopi`, so the recommendation can be implemented today. Meanwhile the host runs `memory.backend: mnemopi` and also mounts the `agentmemory` MCP in OMP, so two narrative memory owners capture the same turns.

## Decision
On the primary harness (OMP), Mnemopi owns narrative memory. `agentmemory` is unmounted from OMP so there is exactly one owner. Hindsight is not adopted now; it is the named upgrade path.

## Considered options

1. **Hindsight** — deferred, not rejected on merit. Its measured strength, structured extraction, is Mnemopi's measured weakness. But it needs a service on `localhost:8888` plus a database to run, upgrade and back up on a laptop. The structured knowledge it would produce also duplicates what `CONTEXT.md` and `docs/adr/*.md` already own canonically under ADR 0002.
2. **`local`** (OMP's own summary pipeline) — no vector store and no service, but never exercised here. Choosing it would trade a known quantity for an unknown one.
3. **Keep both Mnemopi and agentmemory** — rejected. It injects roughly 1,900 tokens per session for a store nothing queries, and with two owners a recall failure cannot be attributed to either.

## Evidence
Measured on the `dotfiles` Mnemopi bank (15 sessions, 2026-06-20 to 2026-07-14), not on published claims, because Mnemopi has no published benchmark:

- `#2327` fixed the consolidation defect in `can1357/oh-my-pi#2320`: `episodic_memory`, `gists` and `graph_edges` stayed permanently empty because `sleepAllSessions()` ran only from `/memory enqueue`. Verified populated here: 4 episodes, 4 gists, 37 edges, 15 triples.
- The structured layer is still noise: pronouns as knowledge-graph subjects (`What related_to …`, `This related_to documented`), a single universal `related_to` predicate, verbatim duplicated triples, facts with truncated subjects (`mage_size… metric 354MB`), and fabricated `location`/`emotion` fields on gists.
- Verbatim transcript recall works and is accurate. Useful recall comes through the vector/FTS path tagged `[coding-agent-transcript]`, not through the graph.

This stack therefore treats Mnemopi as a per-project transcript index and does not rely on its structured memory.

## Consequences

- `mnemopi.polyphonicRecall` stays `false`. Enabling it adds the graph and fact voices to recall, which injects the noise documented above into the prompt.
- Durable decisions still go to `CONTEXT.md` and ADRs. ADR 0002's rule that plain text is canonical is unchanged, and it is what makes this choice affordable.
- Supersedes ADR 0002 only for the primary harness. Hermes, Claude Code and Codex keep their current wiring until the secondary-agent question is decided.
- Flip trigger: when "what did we decide about X" returns unrelated transcript text instead of the decision, the upgrade is worth its cost.
- **At flip time, re-evaluate Hindsight against mem0 rather than assuming Hindsight.** mem0 published 94.4% on LongMemEval in April 2026, against Hindsight's 91.4% from December 2025, which contradicts Hindsight's claim to be the "most accurate agent memory system ever tested". The numbers cannot be reconciled: different answerers and judges, and neither vendor ran the other. Still, the ordering is no longer obvious. mem0's headline number is for its managed platform only, a different deployment from a self-hosted service.
