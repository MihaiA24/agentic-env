# Matt skills provenance

Source: [mattpocock/skills at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7), 2026-09-18. Licence: [MIT, Matt Pocock](LICENSE).

The [manifest](../../skill-packs.json) selects eighteen complete packages from `skills/engineering/` and `skills/productivity/`, flattened into `skills/`. Supporting files and per-skill descriptors are retained; category indexes and unselected skills are omitted. `teach` was removed with its format files and descriptor; the public `teach` is pstack's. Vendoring exists to preserve local adaptations, not to work around CLI pinning, since the skills CLI supports tags and commit SHAs.

## Local adaptations

- Native loading (`skill://`, `skill_view`) and delegation (`task`, `delegate_task`); independent work may fan out, small work stays inline. Authoring mechanics distinguish manual discovery from named dependency loading.
- `code-review` uses the local `scripts/review_snapshot.py`: explicit refs/scoped WIP, unchanged user staging, shared frozen context and before/after integrity checks. Intent can come from the user, not only commits. Hashes are not write restrictions; reviewers need restricted grants or tool-less input.
- `code-review` ships a local `STANDARDS.md`: six shared review lenses condensed from Lauren Tan's pstack `principle-*` skills (`cursor/plugins` @ `c1c0a32`, [MIT, Lauren Tan](../pstack/LICENSE)), not Matt's work. The Standards axis applies it in every repo, below the repo's own standards and above the smell baseline.
- Tracker consumers use `docs/agents/issue-tracker.md` rather than the excluded setup skill; ask when configuration is missing.
- `wizard` is manual-only with metadata and body guards. Approve stages/destinations, never inspect secret files, and leave execution to the human. Hermes does not enforce the metadata flag.
- `prototype`, `wayfinder`, `to-spec`, `to-tickets` and `wizard` gate publication separately. Merge resolution retains its finishing commit, stages only resolved paths and announces it.
- `improve-codebase-architecture` surveys without refactoring or requiring a lone worker.

Other supporting content retains upstream bytes. See [the operative policy](../../../DECISIONS_AI_TOOLING.md#6-skills).

## Updating

Re-copy only selected complete packages at a reviewed revision. Reapply these adaptations, preserve the local snapshot helper, bundled `STANDARDS.md` and licence, update this source record and verify installation before changing the manifest. Compare against the old upstream revision to recover exact local edits.
