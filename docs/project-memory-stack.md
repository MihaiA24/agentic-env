# Project memory stack

This guide defines the first project template for agent-readable project context. The target is one repository at a time. Broader multi-repo patterns come later after this shape works in one repo.

## Roles

Use three tools with hard boundaries:

| Layer | Tool | Job | Canonical? |
| --- | --- | --- | --- |
| Context access | `lean-ctx` | Compressed reads, cached re-reads, shell-output compression, local context routing | No |
| Structural memory | `codebase-memory-mcp` | Code graph queries: symbols, callers, callees, routes, architecture, impact, dead-code candidates | No; rebuildable cache |
| Narrative memory | `agentmemory` | Session history, rationale recall, preferences, discoveries, replayable work history | No; retrieval layer |
| Plain-text project record | `CONTEXT.md` + `docs/adr/*.md` | Canonical domain language and accepted decisions | Yes |

Rule: if losing the generated store would lose project truth, the fact belongs in plain text too.

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

Use for narrative recall:

- why a session changed direction
- discoveries that may matter later
- user/project preferences
- debugging history
- partial reasoning that should help future agents

Do not use it as the only source for accepted decisions. Important decisions get promoted into ADRs.

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

Use as the default local context layer:

- file reads with the smallest useful fidelity
- cached re-reads
- shell output compression
- directory maps
- session/context savings visibility

Do not treat lean-ctx memory as the project decision record.

## Install and configure

From this repo:

```bash
cd agentic-env
uv run ./install-skills-mcps.py --all-mcps --yes
uv run ./configure-agent-mcps.py
```

Current installer behavior:

- installs `codebase-memory-mcp` with UI by default
- installs `lean-ctx` and runs `lean-ctx setup`
- installs `agentmemory`
- keeps the older `agentmemory` Hermes/OMP wiring path working

Current MCP configuration script behavior:

- prompts with checkbox-style selections for `lean-ctx`, `codebase-memory-mcp`, and `agentmemory`
- adds selected MCP servers to `~/.hermes/config.yaml` under `mcp_servers`
- adds selected MCP servers to OMP MCP config files under `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json`
- adds matching global skills under `~/.hermes/skills`, `~/.omp/agent/skills`, and `~/.pi/agent/skills` when missing
- leaves existing MCP server and skill entries unchanged

Manual commands, when needed:

```bash
codebase-memory-mcp config set auto_index true
lean-ctx doctor
agentmemory doctor
```

`codebase-memory-mcp` can be run as an MCP server through the installed binary or package. Its package manifest exposes stdio transport via `npx codebase-memory-mcp` or `uvx codebase-memory-mcp`.

## Hermes target config

The installer manages the `agentmemory` block. Keep this shape for MCP entries:

```yaml
mcp_servers:
  agentmemory:
    command: npx
    args: ["-y", "@agentmemory/mcp"]

memory:
  provider: agentmemory
```

If Hermes needs explicit entries for the other tools, use the same MCP server style:

```yaml
mcp_servers:
  codebase-memory-mcp:
    command: codebase-memory-mcp
  lean-ctx:
    command: lean-ctx
```

Prefer the tools' installers and `lean-ctx setup` before hand-editing config.

## Oh My Pi / OMP target config

The MCP configuration script writes selected servers to OMP MCP config files:

```json
{
  "mcpServers": {
    "lean-ctx": {
      "command": "lean-ctx"
    },
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp"
    },
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"]
    }
  }
}
```

It writes both `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` for current OMP and legacy Pi agent paths. Existing entries are preserved.

## Per-project startup checklist

Run this when opening a repo for agent work:

1. Ensure `CONTEXT.md` exists.
2. Ensure `docs/adr/` exists or create it on first ADR.
3. Start or verify `agentmemory`.
4. Run `lean-ctx doctor`.
5. Index the repo with `codebase-memory-mcp` or enable auto-index.
6. Ask structural questions through `codebase-memory-mcp` before scanning files manually.
7. During `grill-with-docs`, update `CONTEXT.md` immediately when a term is settled.
8. Create an ADR only when the ADR threshold is met.

## Smoke checks

Use warnings, not hard failure, for missing optional memory tools in normal project work:

```bash
command -v lean-ctx >/dev/null || echo "warning: lean-ctx missing"
command -v codebase-memory-mcp >/dev/null || echo "warning: codebase-memory-mcp missing"
command -v agentmemory >/dev/null || echo "warning: agentmemory missing"
```

Fresh agent-stack CI may be stricter. In this repo, `docker-smoke-test.sh` must fail when the stack install contract breaks.

## Failure behavior

- Missing `lean-ctx`: warn; fall back to native reads/search/shell.
- Missing `codebase-memory-mcp`: warn; fall back to LSP/search for structural exploration.
- Missing `agentmemory`: warn; continue without long-term narrative recall.
- Missing all three: loud warning; project remains usable but loses the memory stack.

## CI guardrails

For a project that adopts this template, check:

- `CONTEXT.md` exists.
- `docs/adr/` exists or the project documents that no ADR has been created yet.
- `lean-ctx`, `codebase-memory-mcp`, and `agentmemory` are callable, or warnings are emitted.
- Hermes config contains required MCP entries for the adopted tools.
- OMP config contains required extensions/MCP entries for the adopted tools.
- One smoke command per tool works where possible:
  - `lean-ctx doctor`
  - `codebase-memory-mcp --version`
  - `agentmemory doctor`

## Query recipes

Use these first for codebase navigation:

- Architecture overview: ask for packages, entry points, boundaries, and hotspots.
- Symbol search: find the exact qualified symbol before reading implementation.
- Callers: ask who depends on a function before changing it.
- Callees: ask what a function reaches before debugging side effects.
- Impact: inspect affected symbols before refactors.
- Dead-code candidates: use graph results as candidates, then verify before deleting.

## Retention

- `CONTEXT.md`: keep only current canonical language.
- ADRs: keep forever; supersede with a new ADR when direction changes.
- `agentmemory`: keep project sessions and let its lifecycle/decay manage recall quality.
- `codebase-memory-mcp`: disposable/rebuildable index; optionally commit its shared graph artifact only after the team wants shared bootstrap speed.
- `lean-ctx`: local cache/session layer; not a project record.
