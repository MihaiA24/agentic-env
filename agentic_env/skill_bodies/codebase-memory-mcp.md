---
name: codebase-memory-mcp
description: Structural code-graph queries — symbols, callers, architecture, impact. Disabled by default; enable per session when the litmus passes.
---

# codebase-memory-mcp

Disabled by default on the primary harness (`disabledServers` denylist). Enable it for a session only when the litmus passes:

- the question would need more than ~10 native read/grep calls, or
- it crosses repository boundaries, or
- it aggregates over the whole graph (architecture overview, dead code, impact analysis).

At enable time, run a `fast` reindex — the graph is not maintained between uses.

Promotion trigger: if the litmus fires roughly weekly in a project, make the server default-on for that project scope and re-measure answer quality there.

The graph is rebuildable from code. Do not store rationale or accepted decisions here; promote durable decisions to ADRs.
