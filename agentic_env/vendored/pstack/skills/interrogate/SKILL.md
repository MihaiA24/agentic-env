---
name: interrogate
description: "Manual only: run when the user explicitly asks for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Several models independently attack one frozen snapshot of a change; the deliverable is a report, never an edit."
disable-model-invocation: true
---

# Interrogate

A high-stakes second opinion. Several models review the *same* frozen snapshot of a change from independent angles, then you judge their findings as lead reviewer. The adversarial signal comes from model diversity, not from assigned personas.

This skill is manual-only and report-only. Run it only when the user asked for it by name or in those words; if it loads without such a request (a runtime that does not honour `disable-model-invocation`), say so and stop rather than spending reviewers. It does not edit files, fix findings, commit, push, open PRs or write to a tracker. Everything it produces is a verdict the user acts on.

It is expensive. Reach for it when a change is genuinely high-stakes or when reviewers already disagree, not as a default review path.

## Step 1. Freeze the snapshot

Every reviewer must read the identical, immutable input. Build it with the shared snapshot helper that `code-review` owns:

```
python3 <code-review skill dir>/scripts/review_snapshot.py \
  --base REF --mode wip|refs [--head REF] \
  [--path REPO_RELATIVE_PATH ...] --output NEW_ABSOLUTE_DIR
```

Locate the helper through the runtime's own skill lookup (`skill://code-review/scripts/review_snapshot.py` in OMP, `skill_view` in Hermes). Do not hard-code a checkout path.

- `--mode refs` reviews an explicit range (`--base main --head HEAD`, a tag, a merge base). Use it when the user names committed work.
- `--mode wip` reviews work in progress: committed, staged, unstaged and intended untracked content, overlaid on HEAD. `--path` is required here and repeatable; it keeps unrelated working-tree edits out. Derive intended paths from the task and changes; ask only when ownership is ambiguous. Never "commit first" to make a range reviewable.

The output directory contains `tree/` (the review source context), `diff.patch`, `commits.txt` and `manifest.json` (`mode`, `base`, `head`, `scope`, the Git `tree` SHA, and a `files` map of relative path to sha256). Run `python3 <helper> --verify OUTPUT` before dispatch and after review; any mismatch invalidates the run. The snapshot uses a temporary index and object database, so it never stages or commits the user's work. Keep prompts and reviewer output **outside** this directory so they do not change its verified file set.

An empty `diff.patch` means there is no delta in the selected scope. Verify that scope matches the request; report no reviewable change or resolve the mismatch, rather than presenting an empty review as a clean verdict.

Quote the resolved `base`, `head`, `mode` and `scope` in the final report. If reviewers are to be told a snapshot is stable, it has to actually be stable: nothing reads the live working tree after this step.

## Step 2. State the intent

Write one paragraph of author intent, drawn from the user's message, `commits.txt`, a PR description if one exists, and the code itself. Reviewers challenge the execution, not the goal, so a wrong intent wastes the whole run. If you are unsure, ask before dispatching.

## Step 3. Choose models that actually exist here

Model diversity is the entire product. Invented aliases, vendor labels copied from another harness, or three entries that resolve to one model are fraud, not diversity.

1. Use the models the user named or configured for this repository, if any.
2. Otherwise discover the real catalogue: `omp models --json` (every entry has an exact `selector` such as `anthropic/claude-sonnet-5` or `openai-codex/gpt-5.6-sol`), or `omp models find <substring>` to narrow it. Pick two to four selectors from **different providers or model families**.
3. Never invent a selector, and never silently swap in a same-family sibling. A substitution is reportable output.

Presence in the catalogue is not proof of access: a selector can still fail at dispatch on credentials or provider routing. That is what Step 5's identity accounting is for.

## Step 4. Build the reviewer prompt

Reviewers have no tools, so the prompt file is the entire world they see. Fill `references/reviewer-prompt.md` with:

1. The stated intent from Step 2.
2. The code under review: the contents of `diff.patch`, plus whichever files under `tree/` a reader needs for context. Inline them; pointing at paths is useless to a tool-less reviewer.
3. The rubric from `references/rubric.md`.
4. The code-quality lens from `references/code-quality-review.md`.

Write the filled template outside the snapshot (for example `<review-run>/prompt.md`, beside `<review-run>/snapshot/`). Every reviewer receives the same bytes, captured once by the runner and recorded by SHA256. If the material is too large, ask to split the review into explicit scopes, then run every model over each scope. Never silently drop requested files or hand different reviewers different subsets.

## Step 5. Dispatch reviewers and account for who answered

```
python3 <interrogate skill dir>/scripts/run_reviewers.py \
  --prompt <review-run>/prompt.md --output <review-run>/reviews \
  --model SELECTOR --model SELECTOR [--model SELECTOR ...]
```

The script runs each reviewer concurrently as its own OMP CLI process with `-p --mode json --no-tools --no-skills --no-rules --no-extensions --no-session` and a report-only system prompt. Reviewers have no tools for reading the live repository or editing anything. For each it writes a numbered raw JSON transcript, `reviewer-N.review.md`, and `reviewers.json` recording the requested selector, observed provider/model, status and shared prompt hash. Failed, partial and identity-less responses do not count; fewer than two distinct completed models blocks the verdict.

Runtime notes:

- **OMP:** run the script through a supervised process or a single bash call; do not try to pass a model through the `task` tool, whose schema is not guaranteed to accept one.
- **Hermes:** use the same script when OMP is installed. Without it, use Hermes's native one-shot CLI only after confirming its provider/model, tool-disabling and identity-reporting options with `hermes --help`. Record the actual returned provider/model and completion state, not the requested label. If this cannot produce two verified, tool-less responses, report blocked; do not guess flags or add credentials.
- Neither runtime is allowed a silent fallback. A reviewer that did not run is an unavailable reviewer.

Accounting rules:

- Report requested selector, returned provider/model and status for every reviewer.
- Report every substitution explicitly, next to the finding it produced.
- If fewer than two distinct models answered, report **blocked** with the failures and what would unblock it. Never present a verdict, and never present an empty verdict, on a single model's output.

## Step 6. Synthesize

1. Parse all findings.
2. Findings raised independently by two or more models are the highest signal.
3. Lone-model findings still matter; weight them accordingly.
4. Deduplicate: different models describe the same issue differently. Merge them and record who raised it.
5. Note explicit disagreements. One model asserting the opposite of another is useful context.

## Step 7. Lead judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator. Read `references/lead-judgment.md` for the framework.

Every finding gets a bucket, the model(s) that raised it, and a one-line rationale:

- **Act on.** Real correctness, security or maintainability problems given the actual goals. These would block a real PR.
- **Consider.** Legitimate, but the cost of addressing it now is arguable. Worth the user's attention.
- **Noted.** Valid but not actionable: context-dependent, premature, or low-impact at this stage.
- **Dismissed.** Wrong, nitpicky, or missing context. Say briefly why.

A finding is evidence-based or it is dismissed. A reviewer that could not read the code path it speculates about does not get promoted to "act on" on assertion alone.

## Output format

### Snapshot
> mode, base, head, scope, and the snapshot directory.

### Intent
> [The paragraph from Step 2]

### Reviewers
- Reviewer [label]: requested `<selector>`, answered `<provider>/<model>`, [N findings] — one bullet per reviewer, including failures and substitutions.

### Act On
[Findings to address: description, which models raised it, why it matters.]

### Consider
[Findings worth thinking about: description, which models raised it, the tradeoff.]

### Noted
[Valid but low-priority. Brief list.]

### Dismissed
[Rejected findings with brief rationale.]

### Agreement Map
[Where models agreed, where they diverged, and what that pattern says about confidence.]

Stop there. Fixes, commits and PRs are separate work under their own authorization.

## Reference files

- `references/reviewer-prompt.md`. Reviewer prompt template and finding format.
- `references/rubric.md`. Review lenses.
- `references/code-quality-review.md`. Code-quality lens applied by every reviewer.
- `references/lead-judgment.md`. Lead-reviewer triage framework.
- `scripts/run_reviewers.py`. Concurrent tool-less reviewer dispatch with model-identity accounting.

Load references through the runtime's own skill lookup (`skill://interrogate/references/<file>` in OMP, `skill_view` in Hermes). Do not hard-code a checkout path.
