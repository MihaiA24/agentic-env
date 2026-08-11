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

From this repo:

```bash
cd agentic-env
uv tool install --force .
agentic-bootstrap --yes
```

Legacy split path:

```bash
agentic-install-skills-mcps --all-mcps --yes
agentic-configure-agent-mcps
```

Current installer behavior:

- installs `lean-ctx` and runs `lean-ctx setup`
- installs `agentmemory`
- installs skill packs via the bundled `agentic_env/skill-packs.json` by default:
  - `DietrichGebert/ponytail`
  - `mattpocock/skills`
- each skill pack in JSON can include optional `skills` to install a subset by default
- if `--skill` is passed, each selected pack is filtered by intersection with requested skills
- installs to target agents in `--skill-agent` (default: `hermes,claude,codex`)
- `--skill-config` can point to an alternate JSON profile
- keeps a per-harness global-skill baseline when configured
- installs `codebase-memory-mcp` with UI by default

- prompts with checkbox-style selections for `lean-ctx`, `codebase-memory-mcp`, and `agentmemory`
- adds selected MCP servers to `~/.hermes/config.yaml` under `mcp_servers`
- writes only `codebase-memory-mcp` to OMP MCP config files under `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json`
- adds matching global skills, excluding `lean-ctx` and `agentmemory` from the OMP skill roots
- leaves existing MCP server and skill entries unchanged
### Skill pack JSON format

The bundled `agentic_env/skill-packs.json` defines:

- `packs`: list of skill pack descriptors
  - `name`: canonical pack name
  - `source`: GitHub owner/repo identifier for `skills add`
  - `label`: human-readable label in install logs
  - `aliases`: additional pack selectors for CLI prompts and `--skill-pack`
  - `skills`: optional whitelist of skill ids to install by default for that pack
- `--skill-agent`: optional list of target clients for `skills` installation
- `profiles`: named pack lists, e.g. `default`, `minimal`, `agentic-only`
Example:

```json
{
  "packs": [
    {
      "name": "mattpocock",
      "source": "mattpocock/skills",
      "label": "mattpocock skills",
      "aliases": ["mattpocock", "mattpocock/skills"],
      "skills": ["ask", "tdd"]
    }
  ],
  "profiles": {
    "default": ["mattpocock"]
  }
}
```

Behavior:

- Packs with `skills` default to that subset.
- If you pass `--skill`, installer applies requested skills to each selected pack:
  - pack with no `skills`: installs requested skills
  - pack with `skills`: installs intersection of requested and configured skills

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

OMP core owns context I/O, and Mnemopi owns narrative memory under ADR-0006. The ADR-0008 fallback executed on 2026-08-11 dropped `lean-ctx` from OMP after the semantic-search count came in at one, below the threshold of five. The MCP configuration script therefore writes neither `agentmemory` nor `lean-ctx` to OMP-family config.

`codebase-memory-mcp` remains configured as the structural-memory option:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp"
    }
  }
}
```

It writes both `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` for current OMP and legacy Pi agent paths. Existing entries are preserved. Use `codebase-memory-mcp` only after the session's codebase-memory litmus passes.

## Per-project startup checklist

Run this when opening a repo for agent work:

1. Ensure `CONTEXT.md` exists.
2. Ensure `docs/adr/` exists or create it on first ADR.
3. On OMP, use native context I/O and Mnemopi; on a secondary agent, verify its `agentmemory` and `lean-ctx` wiring.
4. If the codebase-memory litmus passes, index the repo with `codebase-memory-mcp` or enable auto-index.
5. Ask structural questions through `codebase-memory-mcp` only after that litmus passes.
6. During `grill-with-docs`, update `CONTEXT.md` immediately when a term is settled.
7. Create an ADR only when the ADR threshold is met.

## Smoke checks

Use warnings, not hard failure, for missing optional memory tools in normal project work:

```bash
command -v lean-ctx >/dev/null || echo "warning: lean-ctx missing"
command -v codebase-memory-mcp >/dev/null || echo "warning: codebase-memory-mcp missing"
command -v agentmemory >/dev/null || echo "warning: agentmemory missing"
test -f ~/.hermes/skills/ponytail/SKILL.md && echo "ponytail: global"
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
- OMP MCP config contains `codebase-memory-mcp` and excludes `agentmemory` and `lean-ctx`.
- One smoke command per installed CLI works where possible:
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
- `agentmemory`: keep project sessions for secondary agents and let its lifecycle/decay manage recall quality.
- Mnemopi: OMP's sole narrative-memory owner; treat it as transcript recall, not the canonical record.
- `codebase-memory-mcp`: disposable/rebuildable index; optionally commit its shared graph artifact only after the team wants shared bootstrap speed.
- `lean-ctx`: secondary-agent local cache/session layer; not a project record and not mounted on OMP.
