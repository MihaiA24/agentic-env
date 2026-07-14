---
name: lean-ctx
description: Use when reading files, searching code, listing directories, or running shell commands so context is compressed and cached.
---

# lean-ctx

Use `lean-ctx` as the default local context layer.

- Prefer lean-ctx reads/search/tree/shell wrappers over raw file and shell output.
- Read the smallest useful fidelity first: map/signatures/range before full files.
- Use cached re-reads and diff mode after edits.
- Run `lean-ctx doctor` when wiring looks broken.
- Do not treat lean-ctx cache or session state as the canonical project decision record.
