# ADR 0002: Project memory stack boundaries

## Status
Accepted

## Context
Projects need durable context for AI agents without mixing generated indexes, retrieval memory, and canonical project records. The first rollout targets one repository at a time, with Hermes Agent and Oh My Pi / OMP as the configured agent clients.

## Decision
Use a three-tool project memory stack with strict boundaries: `lean-ctx` is the context access and compression layer, `codebase-memory-mcp` is structural memory for rebuildable code graph queries, and `agentmemory` is narrative memory for searchable session history and decision recall. Keep canonical project language in `CONTEXT.md` and accepted decisions in `docs/adr/*.md`; important decisions discovered through `agentmemory` must be promoted into ADRs instead of living only in retrieval memory.

## Alternatives considered

1. **Put all project knowledge in `agentmemory`**
   - Rejected: retrieval memory is useful for recall, but it is not the plain-text canonical record future maintainers can audit in the repo.

2. **Use only `CONTEXT.md` and ADRs**
   - Rejected: plain text is canonical but does not replace fast structural queries, cached context access, or cross-session narrative recall.

3. **Treat all three tools as interchangeable memory**
   - Rejected: mixing structural code facts with decision history makes agents ask the wrong store and creates stale or non-rebuildable truth.

## Consequences

- `CONTEXT.md` remains a glossary, not an implementation spec or memory dump.
- ADRs are append-only history by default; new decisions supersede old ones instead of rewriting them.
- `codebase-memory-mcp` indexes can be deleted and rebuilt without losing project truth.
- `agentmemory` improves recall, but accepted decisions still need plain-text promotion when they become durable.
- Missing tools degrade with warnings during project work, while fresh agent-stack CI can still fail on broken installation contracts.
