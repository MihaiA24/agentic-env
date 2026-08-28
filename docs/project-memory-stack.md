# Project memory stack

This guide defines the first project template for agent-readable project context. The target is one repository at a time. Broader multi-repo patterns come later after this shape works in one repo.

## Roles

Roles differ by harness:

| Layer | Owner/tool | Job | Canonical? |
| --- | --- | --- | --- |
| OMP context access | OMP core | Native reads, search, shell, evaluation, and anchored edits | No |
| OMP narrative memory | Mnemopi | Per-project transcript recall | No; retrieval layer |
| Structural memory | `codebase-memory-mcp` | Code graph queries: symbols, callers, callees, routes, architecture, impact, dead-code candidates | No; rebuildable cache |
| Secondary-agent context access | `lean-ctx` | Context routing for Hermes, Claude Code, and Codex | No |
| Secondary-agent narrative memory | `agentmemory` | Session history and rationale recall for Hermes, Claude Code, and Codex | No; retrieval layer |
| Plain-text project record | `CONTEXT.md` + `docs/adr/*.md` | Canonical domain language and accepted decisions | Yes |

Rule: if losing the generated store would lose project truth, the fact belongs in plain text too.

On OMP, the core owns context I/O and Mnemopi owns narrative memory (ADR-0006). The ADR-0008 pre-registered fallback was executed on 2026-08-11 after one semantic-search call since 2026-07-28, below the fixed threshold of five, so `lean-ctx` is dropped from OMP entirely. `codebase-memory-mcp` remains available there, but its use is gated behind the codebase-memory litmus.

## Repository template

Start each project with this minimum layout:

```text
.
├── CONTEXT.md
└── docs/
    └── adr/
```

`CONTEXT.md` is a glossary only. Keep it implementation-free.

```md
# Project Context

One or two sentences describing this project's domain.

## Language

**Canonical Term**:
One or two sentences defining the domain concept.
_Avoid_: vague synonym, overloaded synonym
```

`docs/adr/` stays empty until the first decision qualifies. ADR files use sequential names:

```text
docs/adr/0001-short-decision-title.md
```

ADRs are append-only history by default. Supersede with a new ADR when direction changes. Edit an old ADR only for typo or clarity fixes.

## What goes where

### `CONTEXT.md`

Put canonical project language here:

- domain terms
- names agents must use consistently
- distinctions that prevent ambiguity
- terms used by `grill-with-docs`

Do not put implementation notes, setup commands, transient plans, or decisions here.

### `docs/adr/*.md`

Put durable decisions here when all are true:

1. Reversing the decision has meaningful cost.
2. The decision is surprising without context.
3. Real alternatives existed.

Examples:

- choose events instead of synchronous HTTP between contexts
- choose manual SQL instead of an ORM
- choose where a domain boundary lives
- reject a likely alternative for non-obvious reasons

### `agentmemory`

Use on Hermes, Claude Code, and Codex for narrative recall:

- why a session changed direction
- discoveries that may matter later
- user/project preferences
- debugging history
- partial reasoning that should help future agents

Do not use it as the only source for accepted decisions. Important decisions get promoted into ADRs. Do not mount it on OMP; Mnemopi is the sole narrative-memory owner there under ADR-0006.

### `codebase-memory-mcp`

Use for structural questions:

- find a symbol or file by concept
- show callers/callees
- trace impact before edits
- summarize architecture
- find routes, channels, or cross-service edges
- identify dead/unused candidates

Do not store rationale here. The graph is derived from code and can be rebuilt.

### `lean-ctx`

Use on secondary agents for their local context layer:

- file reads with the smallest useful fidelity
- cached re-reads
- shell output compression
- directory maps
- session/context savings visibility

Do not treat lean-ctx memory as the project decision record. Do not mount or install its skill on OMP; the ADR-0008 fallback dropped it there on 2026-08-11.

## Install and configure

`agentic-env/README.md` and the installer own install behavior and per-agent config
shapes; this doc owns roles. From this repo: `uv tool install --force .` then
`agentic-bootstrap`.

## Per-project startup checklist

Run this when opening a repo for agent work:

1. Ensure `CONTEXT.md` exists.
2. Ensure `docs/adr/` exists or create it on first ADR.
3. On OMP, use native context I/O and Mnemopi; on a secondary agent, verify its `agentmemory` and `lean-ctx` wiring.
4. If the codebase-memory litmus passes, index the repo with `codebase-memory-mcp` or enable auto-index.
5. Ask structural questions through `codebase-memory-mcp` only after that litmus passes.
6. During `grill-with-docs`, update `CONTEXT.md` immediately when a term is settled.
7. Create an ADR only when the ADR threshold is met.

## Retention

- `CONTEXT.md`: keep only current canonical language.
- ADRs: keep forever; supersede with a new ADR when direction changes.
- `agentmemory`: keep project sessions for secondary agents and let its lifecycle/decay manage recall quality.
- Mnemopi: OMP's sole narrative-memory owner; treat it as transcript recall, not the canonical record.
- `codebase-memory-mcp`: disposable/rebuildable index; optionally commit its shared graph artifact only after the team wants shared bootstrap speed.
- `lean-ctx`: secondary-agent local cache/session layer; not a project record and not mounted on OMP.
