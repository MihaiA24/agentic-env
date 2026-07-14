---
name: agentmemory
description: Use for long-term narrative memory: decisions, rationale, project history, user preferences, and cross-session recall.
---

# agentmemory

Use `agentmemory` for narrative memory.

Good memories:

- decisions and rationale discovered during a session
- project-specific preferences
- debugging history likely to matter later
- context that should survive agent restarts

Important accepted decisions must also be promoted to plain text in `docs/adr/*.md`. `agentmemory` improves recall; it is not the canonical audit record.
