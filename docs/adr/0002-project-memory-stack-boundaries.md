# ADR 0002: Project memory stack boundaries

## Status
Accepted

## Context
Projects need durable context for AI agents, but generated indexes, retrieval memory, and canonical project records must stay separate. The first rollout targets one repository at a time, with Hermes Agent and Oh My Pi / OMP as the configured agent clients.

## Decision
Use a three-tool project memory stack with strict boundaries: `lean-ctx` for context access and compression, `codebase-memory-mcp` for structural memory (rebuildable code graph queries), and `agentmemory` for narrative memory (searchable session history and decision recall). `CONTEXT.md` holds canonical project language and `docs/adr/*.md` holds accepted decisions. Promote important decisions found through `agentmemory` into ADRs; they must not live only in retrieval memory.

## Alternatives considered

1. **Put all project knowledge in `agentmemory`**
   - Rejected: retrieval memory helps recall, but it is not a plain-text canonical record that future maintainers can audit in the repo.

2. **Use only `CONTEXT.md` and ADRs**
   - Rejected: plain text is canonical, but it cannot replace fast structural queries, cached context access, or cross-session narrative recall.

3. **Treat all three tools as interchangeable memory**
   - Rejected: mixing structural code facts with decision history sends agents to the wrong store and produces stale truth that cannot be rebuilt.

## Consequences

- `CONTEXT.md` stays a glossary, not an implementation spec or memory dump.
- ADRs are append-only by default; a new decision supersedes an old one instead of rewriting it.
- `codebase-memory-mcp` indexes can be deleted and rebuilt without losing project truth.
- `agentmemory` improves recall, but a decision that becomes durable still needs promotion to plain text.
- During project work, missing tools degrade with warnings; fresh agent-stack CI can still fail on broken installation contracts.
