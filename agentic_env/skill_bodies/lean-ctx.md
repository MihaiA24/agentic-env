---
name: lean-ctx
description: Semantic (by-meaning) code search via ctx_search when you know what code does but not what it is called.
---

# lean-ctx

`lean-ctx` provides one capability without a native equivalent: semantic code search.

- Use `ctx_search(action=semantic, query=...)` when keyword search fails — you know what the code does, not what it is called.
- Prefer native read/grep/glob/LSP for everything else: exact strings, symbols, structure, navigation.
- Run `ctx_search(action=reindex)` if semantic results look stale after large-scale changes.
- On OMP, `ctx_search` is the only exposed tool (ADR-0008); do not look for other `ctx_*` tools there.
- Do not treat lean-ctx cache or session state as the canonical project decision record.
