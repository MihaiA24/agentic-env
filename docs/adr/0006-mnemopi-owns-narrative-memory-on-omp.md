# ADR 0006: Mnemopi owns narrative memory on the primary harness

## Status
Accepted

## Context
`AI_CONTEXT_TOOLING_COMPARISON.md` (advisory, uncommitted, snapshot 2026-07-24) ranks Hindsight first for the memory layer on evidence grade A — ~91.4% LongMemEval answer accuracy. That grade does not survive checking: the comparison calls the result "independently reproduced", but both cited sources are first-party (the vendor's repository and `arXiv:2512.12818`, authored by Vectorize). The number is a vendor benchmark on a public corpus, not an independent reproduction. OMP 17.1.5 accepts `off | local | hindsight | mnemopi`, so the recommendation is implementable, not aspirational. Meanwhile the host runs `memory.backend: mnemopi` and simultaneously mounts the `agentmemory` MCP in OMP: two narrative memory owners capturing the same turns.

## Decision
On the primary harness (OMP), Mnemopi owns narrative memory, and `agentmemory` is unmounted from OMP so there is exactly one owner. Hindsight is not adopted now; it is the named upgrade path.

## Considered options

1. **Hindsight** — deferred, not rejected on merit. Its measured strength is structured extraction, which is precisely Mnemopi's measured weakness. But it costs a service on `localhost:8888` plus a database to run, upgrade and back up on a laptop, and the structured knowledge it would produce duplicates what `CONTEXT.md` and `docs/adr/*.md` already own canonically under ADR 0002.
2. **`local`** (OMP's own summary pipeline) — no vector store, no service; never exercised here, so choosing it would trade a known quantity for an unknown one.
3. **Keep both Mnemopi and agentmemory** — rejected. Roughly 1,900 injected tokens per session for a store nothing queries, and with two owners a recall failure cannot be attributed to either.

## Evidence
Measured on the `dotfiles` Mnemopi bank (15 sessions, 2026-06-20 to 2026-07-14) rather than on published claims, because no published benchmark for Mnemopi exists:

- The consolidation defect in `can1357/oh-my-pi#2320` — `episodic_memory`, `gists`, `graph_edges` permanently empty because `sleepAllSessions()` ran only from `/memory enqueue` — was fixed in `#2327`. Verified populated here: 4 episodes, 4 gists, 37 edges, 15 triples.
- The structured layer is nonetheless noise: pronouns as knowledge-graph subjects (`What related_to …`, `This related_to documented`), a single universal `related_to` predicate, verbatim duplicated triples, facts with truncated subjects (`mage_size… metric 354MB`), and fabricated `location`/`emotion` fields on gists.
- Verbatim transcript recall works and is accurate. Useful recall arrives through the vector/FTS path tagged `[coding-agent-transcript]`, not through the graph.

Mnemopi is therefore treated as a per-project transcript index. Its structured-memory surface is not relied on.

## Consequences

- `mnemopi.polyphonicRecall` stays `false`. Enabling it promotes the graph and fact voices into recall, which injects the noise documented above into the prompt.
- Durable decisions are still promoted to `CONTEXT.md` and ADRs. ADR 0002's plain-text-is-canonical rule is unchanged and is what makes this choice affordable.
- Supersedes ADR 0002 only for the primary harness. Hermes, Claude Code and Codex keep their current wiring until the secondary-agent question is decided.
- Flip trigger: when "what did we decide about X" returns transcript sludge instead of the decision, the upgrade has paid for itself.
- **At flip time, re-evaluate Hindsight against mem0 rather than assuming Hindsight.** mem0 published 94.4% on LongMemEval in April 2026 against Hindsight's 91.4% from December 2025, which contradicts Hindsight's "most accurate agent memory system ever tested". The numbers are not reconcilable — different answerers and judges, and neither vendor ran the other — but the ordering is no longer obvious, and mem0's headline is managed-platform only, which is a materially different deployment from a self-hosted service.
