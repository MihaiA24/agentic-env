---
name: research
description: Research topics and verify docs or API facts against high-trust primary sources. Use for outside facts or delegated reading; return a cited answer or save a reusable note as needed.
---

Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it and cite it.

## Execution

- Handle a focused docs or API lookup inline.
- Delegate substantial, independent reading slices only when you can continue other useful work while they run. Use your runtime's delegation tool (OMP: `task`; Hermes: `delegate_task`); otherwise research inline.
- Cover the requested scope in either mode. Delegation changes who reads, not what must be investigated.

## Findings

- Default to a cited answer in the reply.
- Save a single Markdown note only when the user requests a file or later work needs a reusable research record for a spec, decision or handoff. A chat-only or read-only request stays in the reply.
- When saving, update an existing relevant note or use the repo's established location and format. If there is no convention, choose a sensible location. Keep the citations and say where the note is saved.
