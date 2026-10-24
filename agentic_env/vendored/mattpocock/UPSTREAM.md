# Matt skills provenance

Source: [mattpocock/skills at `49dd158d1076134a641b33efb035946536778336`](https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336), 2026-10-09. Licence: [MIT, Matt Pocock](LICENSE).

Rechecked 2026-10-19 through [`5beb35b040e3de97e54fa9e386d7e42d15c295c2`](https://github.com/mattpocock/skills/compare/49dd158d1076134a641b33efb035946536778336...5beb35b040e3de97e54fa9e386d7e42d15c295c2): only the excluded `chief-of-staff` package and its changeset changed. All nineteen selected packages are unchanged upstream; the source pin stays at `49dd158`.

The [manifest](../../skill-packs.json) selects nineteen complete packages from `skills/engineering/` and `skills/productivity/`, flattened into `skills/`. Supporting files and per-skill descriptors are retained; category indexes and unselected skills are omitted. `teach` was removed with its format files and descriptor; the public `teach` is pstack's. `resolving-merge-conflicts` was removed upstream in `daa01d8` and is dropped here. Vendoring exists to preserve local adaptations, not to work around CLI pinning, since the skills CLI supports tags and commit SHAs.

## Local adaptations

- Native loading (`skill://`, `skill_view`) and delegation (`task`, `delegate_task`); independent work may fan out, small work stays inline. Authoring mechanics distinguish manual discovery from named dependency loading.
- `code-review` uses the local `scripts/review_snapshot.py`: explicit refs/scoped WIP, unchanged user staging, shared frozen context and before/after integrity checks. Intent can come from the user, not only commits. Hashes are not write restrictions; reviewers need restricted grants or tool-less input.
- `code-review` ships a local `STANDARDS.md`: six shared review lenses condensed from Lauren Tan's pstack `principle-*` skills (`cursor/plugins` @ `c1c0a32`, [MIT, Lauren Tan](../pstack/LICENSE)), not Matt's work. The Standards axis applies it in every repo, below the repo's own standards and above the smell baseline.
- Tracker consumers use `docs/agents/issue-tracker.md` rather than the excluded setup skill; ask when configuration is missing.
- `wizard` is manual-only with metadata and body guards. Approve stages/destinations, never inspect secret files, and leave execution to the human. Hermes does not enforce the metadata flag.
- `wizard/template.sh` writes literal single-line dotenv values, not shell quote concatenation. Enter-to-keep reads hand-edited lines as dotenv readers do (surrounding whitespace, inline ` # comments`, a comment after a closing quote); upstream keeps those raw and empties `"a\nb"`. Forms readers disagree on (`a#b`, backticks, text after a closing quote, unclosed quotes) or that this quoting subset cannot represent losslessly fail before file mutation; use a consumer-specific serializer for them.
- `prototype`, `wayfinder`, `to-spec`, `to-tickets` and `wizard` gate publication separately. `wayfinder` research branches are created or pushed only on request, never PR'd; `to-tickets` names sub-issue attachment in the breakdown the user approves.
- `improve-codebase-architecture` surveys without refactoring or requiring a lone worker.
- The `CONTEXT.md` convention stays: upstream `d80fa0f` renamed `CONTEXT.md`, `CONTEXT-MAP.md` and `CONTEXT-FORMAT.md` to `GLOSSARY*`, but the user's repos use the old names. `domain-modeling` (with `CONTEXT-FORMAT.md`), `codebase-design`, `diagnosing-bugs`, `improve-codebase-architecture`, `tdd`, `wait-what` and `pr` keep them; "glossary" stays an ordinary noun.
- `retro` is manual-only with metadata and body guards, and report-only: implementing a candidate, commits, CI or hook changes need separate authorization. It reads the current session unless the user names another, through native transcripts, never a newest-file guess. Its reviewer agent and `CODING_STANDARDS.md` map to `code-review` and the repo's own standards file.
- `pr` only drafts the body; pushing, opening or editing a PR is a separate authorized effect. Evidence is what the session observed, never fabricated.

Other supporting content retains upstream bytes, apart from the `CONTEXT.md` names and the documented wizard dotenv fix. See [the operative policy](../../../DECISIONS_AI_TOOLING.md#6-skills).

## Updating

Re-copy only selected complete packages at a reviewed revision. Reapply these adaptations, preserve the local snapshot helper, bundled `STANDARDS.md` and licence, update this source record and verify installation before changing the manifest. Compare against the old upstream revision to recover exact local edits.
