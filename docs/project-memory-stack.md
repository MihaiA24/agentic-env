# Project memory stack

This guide defines the first project template for agent-readable project context. It targets one repository at a time; multi-repo patterns come after this shape works in one repo.

## Roles

Roles differ by harness:

| Layer | Owner/tool | Job | Canonical? |
| --- | --- | --- | --- |
| OMP context access | OMP core | Native reads, search, shell, evaluation, and anchored edits | No |
| OMP narrative memory | Mnemopi | Per-project transcript recall | No; retrieval layer |
| Structural memory | `codebase-memory-mcp` | Code graph queries: symbols, callers, callees, routes, architecture, impact, dead-code candidates | No; rebuildable cache |
| Hermes narrative memory | `agentmemory` | Session history and rationale recall for Hermes | No; retrieval layer |
| Plain-text project record | `CONTEXT.md` + `docs/adr/*.md` | Canonical domain language and accepted decisions | Yes |

Rule: if losing a generated store would lose project truth, record the fact in plain text too.

On OMP, the core owns context I/O and Mnemopi owns narrative memory (ADR-0006). `lean-ctx` was dropped from OMP on 2026-08-11 (ADR-0008 pre-registered fallback) and removed from the whole stack on 2026-09-02 (ADR-0009). `codebase-memory-mcp` stays available on OMP, gated behind the codebase-memory litmus.

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

Use on Hermes for narrative recall:

- why a session changed direction
- discoveries that may matter later
- user/project preferences
- debugging history
- partial reasoning that should help future agents

Do not use it as the only source for accepted decisions; promote important decisions into ADRs. Do not mount it on OMP, where Mnemopi is the sole narrative-memory owner under ADR-0006.

### `codebase-memory-mcp`

Use for structural questions:

- find a symbol or file by concept
- show callers/callees
- trace impact before edits
- summarize architecture
- find routes, channels, or cross-service edges
- identify dead/unused candidates

Do not store rationale here. The graph derives from code and can be rebuilt.

## Install and configure

The [machine-provisioning runbook](../README.md#quick-usage) owns installation and per-agent configuration on supported macOS/Linux hosts; this document owns memory roles. The runbook's checkout installation step starts in the `agentic-env` directory, not the dotfiles root.

The [custom-directory and Windows copy routes](../README.md#choose-an-installation-path) only copy skill packages. They do not install or configure this memory stack, MCPs, hooks or agent discovery.

## Per-project startup checklist

Run this when opening a repo for agent work:

1. Ensure `CONTEXT.md` exists.
2. Ensure `docs/adr/` exists or create it on first ADR.
3. On OMP, use native context I/O and Mnemopi; on Hermes, verify its `agentmemory` wiring (`agentic-stack-doctor` warns on it).
4. If the codebase-memory litmus passes, index the repo with `codebase-memory-mcp` or enable auto-index.
5. Ask structural questions through `codebase-memory-mcp` only after that litmus passes.
6. During `grill-with-docs`, update `CONTEXT.md` immediately when a term is settled.
7. Create an ADR only when the ADR threshold is met.

## Retention

- `CONTEXT.md`: keep only current canonical language.
- ADRs: keep forever; supersede with a new ADR when direction changes.
- `agentmemory`: keep project sessions for Hermes and let its lifecycle/decay manage recall quality.
- Mnemopi: OMP's sole narrative-memory owner; treat it as transcript recall, not the canonical record.
- `codebase-memory-mcp`: disposable, rebuildable index. Commit its shared graph artifact only if the team wants faster shared bootstrap.
