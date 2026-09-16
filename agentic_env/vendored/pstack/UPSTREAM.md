# pstack (vendored)

Copied from `cursor/plugins`, directory `pstack/`, at commit
`c1c0a32802223f4be824112dd83d33ad29a8b26c` (2026-09-14T21:56:29-04:00).
Licence: `LICENSE` (MIT, Lauren Tan).

Why a copy: `cursor/plugins` publishes no tags and the `skills` CLI clones by
branch name only, so no upstream ref can pin this pack. The copy is the pin.

Contents: the nine skills in `skills/`, each directory complete and unmodified.
Everything else under `pstack/` (agents, automations, the other skills) is
deliberately not copied; the roster and its reasons are in
`DECISIONS_AI_TOOLING.md` §6.

Local modifications: none.

Bump: re-copy the same directories at a reviewed commit, update the commit and
date above, note it in `DECISIONS_AI_TOOLING.md` Upstream watch.
