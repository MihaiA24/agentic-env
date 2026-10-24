# Pstack provenance

Source: `cursor/plugins`, `pstack/`.

- Original nine packages: [`c1c0a32802223f4be824112dd83d33ad29a8b26c`](https://github.com/cursor/plugins/tree/c1c0a32802223f4be824112dd83d33ad29a8b26c/pstack), 2026-09-14.
- Added `technical-writing` and `maintain-verification-skill`, later `teach` (a single `SKILL.md`): [`640ea3abfbdef74aad432b58d8586e4bf645f42d`](https://github.com/cursor/plugins/tree/640ea3abfbdef74aad432b58d8586e4bf645f42d/pstack). The pstack subtree is unchanged between these revisions.
- Merged the twelve to pstack 0.15.21 and added `benchmark-checklist` and `correct`: [`1dcc2bacde73ddd284803b7af28164d0436198fc`](https://github.com/cursor/plugins/tree/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack), 2026-10-12. Upstream prompt distillation is taken; its Cursor model defaults are not.
- Selectively backported from pstack 0.15.29, reviewed at [`29fa9382c9c250d134f6a2f1aa86c01c5f63119d`](https://github.com/cursor/plugins/tree/29fa9382c9c250d134f6a2f1aa86c01c5f63119d/pstack), 2026-10-21: `correct`'s behavior-preserving test criterion ([`e5136d82`](https://github.com/cursor/plugins/commit/e5136d82418d2db3165ea1050d17577cd618cc05)) and `interrogate`'s lead-judgment cleanup ([`99743e9c`](https://github.com/cursor/plugins/commit/99743e9c151c8537cbbf1f98bb38f34ef3368453)). The base pin remains `1dcc2ba`; new packages and Cursor-specific model/effort routing changes are not imported.
- Licence: [MIT, Lauren Tan](LICENSE). [The manifest](../../skill-packs.json) selects fourteen complete skill packages; other skills, agents and automations are omitted.

Vendoring preserves local adaptations. Upstream has no tags, but the skills CLI supports full commit pins.

## Local adaptations

All fourteen remain manual-only through metadata plus description/body guards, which still allow named composition under an explicitly invoked recipe. Hermes ignores the metadata gate. OMP/Hermes equivalents replace Cursor-specific loading, delegation, model slugs and transcript paths. Read-only means an actual restricted tool grant; otherwise investigate in the parent or supply frozen input to tool-less reviewers.

| Methods | Changes to preserve |
|---|---|
| `how`, `why` | Small questions inline; independent evidence may fan out. Discover authorized sources through tool/server metadata, not credential files; retain evidence categories and skipped-source accounting. An explicit user or recipe scope (such as `teach`'s) is a third skip reason: requested sources must be covered, including before `why`'s trivial inline answer, and omitted categories are reported coverage limits, not nulls. |
| `blast-radius`, `interrogate` | Report-only, separately authorized effects; use shared scoped snapshots and actual returned model identities. The local `interrogate/scripts/run_reviewers.py` requires two successful distinct models; unavailable diversity is reported, never fabricated. |
| Verification creation/maintenance | Project `.agents/skills/verify-<app>`; existing runners first. Creation proves one feature, maintenance serially exercises every mapped feature and edits only the verifier. Hermes project trust is explicit; product gaps are reported. |
| `technical-writing`, `unslop` | Named cleanup only; preserve domain terms, literals, quotations, confidence language and file conventions. Agent documents route to `writing-for-agents`; unslop rule IDs stay stable. |
| `show-me-your-work` | Resolve its installed script; reserve a unique directory and sole-writer log for each run, including children. Audit owned files against scoped transcripts, never ownership inferred from shared-log timestamp stretches. Keep six-column TSV and sanitization unchanged. Commit permission is separate; cross-model claims require verified identity. |
| `reflect`, `recall` | Explicit session/workspace scope, native timestamps and record types—not newest-file or slug guesses. Inline synthesis unless volume warrants delegation; no automatic Backlog writes. Transcript reconstruction remains distinct from durable-memory retrieval. |
| `teach` | Invocation authorizes its named `how`/`why`/`unslop` runs, loaded natively; small questions stay inline, joint fan-out is one batch. Output is the reply only: no edits, lesson files or learning records. Scoped `why` coverage is disclosed and its confidence language kept. Mermaid where rendered, else ASCII; image generation only when the session exposes a tool, else ASCII sketches. `unslop` is one pass per reply. |
| `benchmark-checklist` | Seven questions intact. Invocation covers local benchmark and profiling runs, not stopping processes the user owns: interleave and say so. Unvendored playbook references become self-contained baseline/harness rules; PR bodies keep one primary number through the native `pr` skill. |
| `correct` | Levels in order, docs last; each check proven on a real past mistake; rule table kept. History mining is read-only. Invocation covers working-tree guard edits; each commit, CI workflow push and exception approval is separately authorized, so it prepares one commit-sized change per class and names what would land. |

Supporting prompts retain their method contracts with those adaptations. Native Hermes model review requires capability/identity verification; the working route uses installed OMP. See [the operative policy](../../../DECISIONS_AI_TOOLING.md#6-skills).

## Updating

Re-copy selected complete packages at a reviewed revision, reapply these adaptations and retain the local reviewer script and licence. Compare against the old upstream revision, update this record and verify installation. New tags alone do not justify discarding the adaptations.
