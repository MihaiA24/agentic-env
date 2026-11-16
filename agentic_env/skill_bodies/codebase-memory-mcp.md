---
name: codebase-memory-mcp
description: Structural code-graph queries — symbols, callers, architecture, impact. Use only when the litmus passes.
---

# codebase-memory-mcp

Query the graph only when the litmus passes:

- the question would need more than ~10 native read/grep calls, or
- it crosses repository boundaries, or
- it aggregates over the whole graph (architecture overview, dead code, impact analysis).

Run a `fast` reindex before the first query — the graph is not maintained between uses.

The graph is rebuildable from code. Do not store rationale or accepted decisions here; promote durable decisions to ADRs.
