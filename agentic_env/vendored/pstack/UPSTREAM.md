# Pstack provenance

Source: `cursor/plugins`, `pstack/`.

- Original nine packages: [`c1c0a32802223f4be824112dd83d33ad29a8b26c`](https://github.com/cursor/plugins/tree/c1c0a32802223f4be824112dd83d33ad29a8b26c/pstack), 2026-09-14.
- Added `technical-writing` and `maintain-verification-skill`, later `teach` (a single `SKILL.md`): [`640ea3abfbdef74aad432b58d8586e4bf645f42d`](https://github.com/cursor/plugins/tree/640ea3abfbdef74aad432b58d8586e4bf645f42d/pstack). The pstack subtree is unchanged between these revisions.
- Licence: [MIT, Lauren Tan](LICENSE). [The manifest](../../skill-packs.json) selects twelve complete skill packages; other skills, agents and automations are omitted.

Vendoring preserves local adaptations. Upstream has no tags, but the skills CLI supports full commit pins.

## Local adaptations

All twelve remain manual-only through metadata plus description/body guards, which still allow named composition under an explicitly invoked recipe. Hermes ignores the metadata gate. OMP/Hermes equivalents replace Cursor-specific loading, delegation, model slugs and transcript paths. Read-only means an actual restricted tool grant; otherwise investigate in the parent or supply frozen input to tool-less reviewers.

| Methods | Changes to preserve |
|---|---|
| `how`, `why` | Small questions inline; independent evidence may fan out. Discover authorized sources through tool/server metadata, not credential files; retain evidence categories and skipped-source accounting. An explicit user or recipe scope (such as `teach`'s) is a third skip reason: requested sources must be covered, including before `why`'s trivial inline answer, and omitted categories are reported coverage limits, not nulls. |
| `blast-radius`, `interrogate` | Report-only, separately authorized effects; use shared scoped snapshots and actual returned model identities. The local `interrogate/scripts/run_reviewers.py` requires two successful distinct models; unavailable diversity is reported, never fabricated. |
| Verification creation/maintenance | Project `.agents/skills/verify-<app>`; existing runners first. Creation proves one feature, maintenance serially exercises every mapped feature and edits only the verifier. Hermes project trust is explicit; product gaps are reported. |
| `technical-writing`, `unslop` | Named cleanup only; preserve domain terms, literals, quotations, confidence language and file conventions. Agent documents route to `writing-for-agents`; unslop rule IDs stay stable. |
| `show-me-your-work` | Resolve its installed script; audit only this run and named children. Commit permission is separate; cross-model claims require verified identity. |
| `reflect`, `recall` | Explicit session/workspace scope, native timestamps and record types—not newest-file or slug guesses. Inline synthesis unless volume warrants delegation; no automatic Backlog writes. Transcript reconstruction remains distinct from durable-memory retrieval. |
| `teach` | Invocation authorizes its named `how`/`why`/`unslop` runs, loaded natively; small questions stay inline, joint fan-out is one batch. Output is the reply only: no edits, lesson files or learning records. Scoped `why` coverage is disclosed and its confidence language kept. Mermaid where rendered, else ASCII; image generation only when the session exposes a tool, else ASCII sketches. `unslop` is one pass per reply. |

Supporting prompts retain their method contracts with those adaptations. Native Hermes model review requires capability/identity verification; the working route uses installed OMP. See [the operative policy](../../../DECISIONS_AI_TOOLING.md#6-skills).

## Updating

Re-copy selected complete packages at a reviewed revision, reapply these adaptations and retain the local reviewer script and licence. Compare against the old upstream revision, update this record and verify installation. New tags alone do not justify discarding the adaptations.
