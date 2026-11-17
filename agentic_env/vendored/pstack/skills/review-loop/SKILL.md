---
name: review-loop
description: "Manual only: review a change in rounds with one or more other models until a gate passes. Run when the user asks for /review-loop, a \"review loop\", review \"until N/10\" or \"max N rounds\", a \"council\" or \"panel\" of models, a second-model review, or a re-review after fixes. Fixes land in the working tree only."
disable-model-invocation: true
---

# Review loop

Other models review a frozen snapshot of the change. You check their findings, make the smallest fix, and send the result back until the gate passes or the budget ends. Reviewers are tool-less OMP processes: each reads one prompt file and reports.

Manual only. If this skill loaded without the user asking for it, say so and stop before spending reviewers. A user-invoked recipe that names `review-loop` is a real invocation.

Hold scope. Repeated review pulls a change wider: make the smallest fix that answers a finding, and decline the rest with a reason.

Requires the `omp` CLI on `PATH`, whichever harness drives, and the `code-review` skill for its snapshot helper.

## 1. Gate

Read the gate from the request. The user's numbers win.

| The request says | Mode | Gate |
| --- | --- | --- |
| No model, or one | Single reviewer | `VERDICT: APPROVE` with no blocker or should open; 3 rounds |
| "council", "panel", several models | Panel, one model per provider | The same, from every reviewer |
| "until 9/10", "at least 8.5" | Either | Every reviewer's score at or above the number |
| "max 5 rounds" | Either | That round cap |
| "add X once Y reaches 8.5" | Staged panel | X joins the round after Y's score meets the number, and its first round is a full review |

A round is one full pass by that round's reviewers. A fresh review after fixes is the next round.

## 2. Brief

Run `git status --short`. The change under review is the paths this task touched; unrelated edits sharing the working tree stay out. Ask when ownership of a path is unclear.

Base: with a PR or MR, `gh pr view --json baseRefName` or `glab mr view`, then `git merge-base HEAD origin/<base>`. Without one, the merge-base with the default branch, or the ref the user names.

Run the covering checks and fix what they show broken before sending anything. Then write the brief and show it to the user:

- **Intent**: what the change is for, in one or two sentences.
- **Out of scope**: what reviewers leave alone (platforms, paths, follow-ups).
- **Checks**: what ran and the results; missing or already-failing checks named as such.

When intent or scope is your guess, ask before round 1. Every round grades against the brief, so a wrong one wastes them all.

## 3. Reviewers

1. Models the user named, resolved to exact selectors with `omp models find <substring>`.
2. Otherwise, from `omp models --json`: for a single reviewer, the newest flagship of a provider other than the one driving this session; for a panel, the newest flagship from each of up to three providers.

A `:level` suffix sets reasoning effort (`<provider>/<model>:high`). Report a named model that is missing, or a panel that reaches one provider only, and wait for the user's choice of replacement.

## 4. Round

Freeze the change with the snapshot helper `code-review` owns (`skill://code-review/scripts/review_snapshot.py` in OMP, `skill_view` in Hermes):

```
python3 <helper> --base <base> --mode wip --path <path> [--path <path> ...] \
  --output <run>/round-N/snapshot
python3 <helper> --verify <run>/round-N/snapshot
```

`--mode wip` takes committed, staged, unstaged and untracked content under those paths without staging or committing; `--mode refs --head <ref>` reviews committed work only. `<run>` is a new directory outside the repository. An empty `diff.patch` means the scope is wrong: stop and resolve it.

Write `<run>/round-N/prompt.md`. It is all a reviewer sees, so inline everything:

```
Review only. Report findings; you have no tools.
Intent: <intent>
Out of scope: <scope>
Checks: <results>

Find bugs, broken callers and mismatch with the intent. Skip style unless it
hides a bug. Hold to the smallest change: flag code, tests or guards the
intent does not need. Other paths, rare cases, small perf, extra compat: nit.
blocker = the intended case is wrong. should = a real bug callers will hit,
inside the intent. nit = the rest.
If a file you need was not supplied, name it instead of guessing.

Reply:
VERDICT: APPROVE or CHANGES
SCORE: <n>/10    (include this line only when the gate is a score)
S1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion>
(one line per finding, stable ids)

## Diff
<contents of diff.patch>

## Context
<each file under tree/ a reader needs, headed by its path>
```

From round 2, add above the diff: the ledger, the change since the previous round (`git diff --no-index <previous>/tree <current>/tree`), and "Review open ids and changed code only. Mark each old id `resolved` or `still open: <reason>`." A reviewer joining late gets the round 1 prompt.

When the material is too large for one prompt, split it into named scopes and run every reviewer over each scope. All reviewers in a round get the same bytes.

Dispatch as one background job:

```
python3 <this skill's directory>/scripts/run_reviewers.py \
  --prompt <run>/round-N/prompt.md --output <run>/round-N/reviews \
  --model <selector> [--model <selector> ...] [--attach <screenshot.png> ...]
```

It writes one `reviewer-N.review.md` per reviewer, and `reviewers.json` with each requested selector, the provider and model that answered, and any substitution. `--attach` sends images to every reviewer, for UI work; the runner copies them into the output directory before dispatch and records each copy's hash, so every reviewer sees the same bytes. Exit 2 means too few models answered (one for a single reviewer, two distinct for a panel); exit 3 means no `omp` CLI. Both block the round: report the failure. A timeout, an error or an empty reply is never an approval.

## 5. Answer findings

Check each finding against the code yourself and set its severity yourself. A caller that cannot pass the bad input, another path, a rare case or a preference is a nit, whatever label it arrived with.

- **Agree**: the smallest fix. Prefer deleting or narrowing over a new helper, option, lock or cache. Add one test that fails without the fix when the intent needs it.
- **Disagree**: say why with evidence (`file:line`, a test, output).
- **Out of scope or nit**: decline in one line and list it as a follow-up.

Keep a ledger across rounds: id, reviewer, severity, outcome (`fixed`, `disagree`, `declined`) and evidence. Re-run the checks and `git diff --shortstat <base>`. If review grew the diff, cut before the next round. Agree because the finding is right, never to end the loop.

## 6. Next round or stop

Start another round while budget remains and the gate is unmet: a blocker or should is open, behaviour changed since the last verdict, or a score is under the number. Declined nits and comment-, doc- or format-only fixes need no new round.

Stop on the first of:

- **Gate met** on the current diff, and you hold no concern of your own.
- **Stuck**: an item is still disputed after two replies. Show both sides in two or three lines each; the user decides.
- **Budget ended**: report what is open. A spent budget is not an approval.

## Effects

Fixes go to the working tree. Commit per round, push, or edit a PR description only when the request names that step.

## Report

One row per reviewer, named by the model that answered, then the ledger, the diff size before and after, and what stays open:

```
| Reviewer | Round 1 | Round 2 |
| --- | --- | --- |
| <provider>/<model> | CHANGES 7/10 | APPROVE 9/10 |
```

Write `no score` where a reviewer gave none. Call the review multi-model only when `reviewers.json` lists two or more distinct models.

Adapted from Tstack's `sol-loop` and `council` (MIT, see `LICENSE`).
