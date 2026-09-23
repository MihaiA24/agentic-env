# Skill workflow evidence — 2026-09-21

For [issue #42](https://github.com/MihaiA24/.dotfiles/issues/42). The approved roster and routing live in [Decisions §6](../DECISIONS_AI_TOOLING.md#6-skills); provenance lives with the vendored [Matt](../agentic_env/vendored/mattpocock/UPSTREAM.md) and [pstack](../agentic_env/vendored/pstack/UPSTREAM.md) packages.

## Verification at `0a827c8`

| Check | Result |
|---|---|
| Regression suite | `uv run --frozen --with pytest python -m pytest`: **69 passed**, including WIP/index preservation and rejection of failed/aliased reviewers as model diversity. Snapshot check also passed on Python 3.10. |
| Installation | Isolated Matt/pstack install and live default install succeeded. All **38 skills**, 38 Claude links and 38 Hermes links verified; **94 package files** matched source. Extra `research/DESCRIPTION.md` preserved. |
| Wheel | Built successfully; all **98 vendored files**, including licences/provenance, and the manifest matched source bytes. |
| OMP | All 38 named loads and supporting assets resolved. With read capability, the filtered automatic list included `writing-for-agents`, not manual `wizard`. A disposable project verifier resolved. |
| Hermes | All 38 catalog entries/named views and sampled supporting assets loaded. A project verifier was absent before trust, present after trust, then trust was revoked in isolated `HERMES_HOME`. Real trust settings were untouched. |
| Real reviewers | `anthropic/claude-haiku-4-5` and `openai-codex/gpt-5.6-luna` both returned the requested identities and found the planted `eligible(18)` boundary bug from identical frozen input. No substitutions; post-review integrity passed. |
| Doctor | `uv run --frozen python -m agentic_env.stack_doctor`: **stack OK, zero secondary warnings**. |

These checks establish installation, discovery and the review path. They do not establish every skill's end-to-end behavior, performance improvements or closure of all issue scenarios. Native Hermes provider review was not established; the verified route uses OMP. Hermes still advertises manual-only skills and warns about canonical-store symlink targets, though loading succeeds.

## Historical research

The [complete reassessment, sources and pre-installation evidence](https://github.com/MihaiA24/.dotfiles/blob/0a827c85d89e3737cca03f20eb5a17c3c1b117fe/agentic-env/docs/skills-workflow-recheck-2026-09-21.md) are preserved at the implementation commit. Its earlier proposals are not the adoption contract: the full pstack TDD/teaching contracts were not approved for folding into Matt's methods. Usage counts were not performance measurements or a count of human workflows.

Earlier [source comparison](skills-development-comparison.md) and [installation assessment](skills-fit-review.md) remain historical; do not use their old rosters as current policy.
