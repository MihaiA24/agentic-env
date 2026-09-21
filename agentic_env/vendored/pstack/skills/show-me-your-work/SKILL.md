---
name: show-me-your-work
description: "Manual only: keep a reviewable decision trail for long-running or unattended work — a TSV log with one row per decision (what, why, evidence, result). Local by default; commit it only with the user's go-ahead. Run when the user asks: /show-me-your-work, or when they ask for a trail over an autonomous or multi-phase run. Never start logging on your own."
disable-model-invocation: true
---

# Show me your work

Manual skill. Start a trail when the user asks for one, or when a recipe the user invoked routes its audit trail here. If it loads without either, say so and stop instead of logging.

Keep one canonical log.

## The format

A single TSV file, one row per decision. Cells stay single-line. Evidence is a pointer, not prose.

Copy `references/decision-log-template.tsv` (the header row) to start a clean log. Columns:

- **ts.** ISO8601 timestamp.
- **phase.** The phase or workstream.
- **decision.** What was chosen or done, one line.
- **why.** The reason in plain words. If a principle drove it, say it plainly, not as a jargon tag.
- **evidence.** A link or path that proves it: commit SHA, PR number, `file:line`, or an artifact, trace, or screenshot path. Never a paragraph.
- **result.** The outcome or predicate state: `tests green`, `reverted`, `pixel-diff 0`, `INCONCLUSIVE`, `open`.

An example, plain-spoken so a reviewer reads it at a glance. This is illustration only. Don't copy these rows into a real log.

```
ts	phase	decision	why	evidence	result
2026-05-24T09:02:00Z	frame	counted the work first, about 100 components and roughly 75 hours	wanted to know the size before starting a long run	commit 3a9f1c2	found 5 things to sort out before starting
2026-05-24T09:40:00Z	harness	took screenshots of the old version before changing anything	so we can compare old against new and catch any visual change	scripts/snapshot.sh, baseline/	saved 120 reference screenshots
2026-05-24T11:15:00Z	widget	moved the widget styles over without changing how it looks	keep the change small and the result identical	commit 7c21e0a, pixel-diff 0	looks identical, tests pass
2026-05-24T12:30:00Z	widget	threw out a helper's work because its screenshots were blank	checked the real files instead of trusting its summary	worktree reset	reverted, tightened the instructions for next time
```

## Logging a row

Write each entry the way you'd tell a teammate what you did. Plain words, concrete actions, no AI speak or abstract jargon. When you run the deliverable through the **unslop** skill, put the log text through the same pass; that skill is manual and does not apply on its own.

Use the helper `scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>`. It ships with this skill: resolve it inside the skill's own installed directory (`skill://show-me-your-work/scripts/log.sh` in OMP, the path `skill_view` reports in Hermes), never a hard-coded checkout path. It stamps `ts`, writes the header on first use, strips stray tabs/newlines, and prefixes any cell starting with `=`, `+`, `-`, or `@` with a single quote. A bare `printf` appending a row works too, but mind those same bytes if cells come from generated or user-supplied text.

Log decision points and checkpoints, not every action: a fork chosen, a unit completed with its verification result, a pivot or revert with its trigger, a blocker surfaced, a gate fixed. For loop runs, one row per iteration. Skip the trivial and self-evident.

## Where it lives

By default the log is a working artifact, not committed. Keep it at `decisions.tsv` in the work dir, or `.audit/<task-slug>.tsv` when several efforts run at once, and leave it out of git.

Commit it only when the work is ambitious enough that a reviewer needs the trail to trust the result, and only with the user's go-ahead for that commit. Committing is its own permission; running this skill is not one.

## Rules

- One row is one decision or checkpoint.
- Append-only. A wrong call gets a new row that supersedes it. Never edit or delete history.
- Prefer evidence produced by committed scripts over hand-made one-offs. A mechanism anyone can rerun outlives a claim in a row.

## Audit the log against the transcript

At the end of the run, check the log against this run's own transcript and named children. Use the runtime's current session handle or path; OMP stores sessions under `~/.omp/agent/sessions/<workspace-directory>/`, Hermes under its active home's `sessions/`. Never select a transcript by recency alone, guess a workspace slug, or inspect unrelated chats. If no unambiguous current transcript is exposed, state that limitation and audit against the current conversation and its evidence. Walk the log against what actually happened:

- Every row maps to a real action. Cut invented or aspirational entries.
- Each row's evidence resolves and shows what the row claims.
- A fork, pivot, or abandoned approach that shaped the work but isn't logged is a gap. Add it.
- Drop padding.

Fix the log, not the story. If the work diverged from what a row claims, the row is wrong.

## Cross-model review of the trail

Before handing back, have a genuinely different model review the trail. Self-review is not a substitute, and a second call to the model that did the work is self-review with extra steps.

Resolve a real model id first: `omp models --json` lists what this install actually exposes, so pick an exact selector from a family other than the working model. Never invent an alias or assume a vendor label implies a different model.

Run the reviewer as its own snapshot-only process, with the trail and the relevant transcript excerpts inlined in the prompt (the flags leave it no tools, so it reads only what the prompt carries):

```bash
omp --model <exact-selector> -p --mode json --no-tools --no-skills --no-rules --no-extensions --no-session "<the trail, the excerpts, and the four questions below>"
```

In Hermes the equivalent is `hermes -z "<prompt>" --provider <provider> -m <model> -t '' --ignore-rules --usage-file <path>`. Either way, read the provider and model back out of the run's own output (the JSON response metadata, or the usage file) instead of trusting the selector you passed: fuzzy matching and fallbacks can land on the model you were trying to avoid.

The reviewer reads the audit trail and the run's transcript excerpts, then flags what the user should pay attention to. Not a redo of the work, a scan for what's suboptimal or risky.

- Decisions logged with weak or absent evidence.
- Verification steps skipped or claimed without proof in the transcript.
- Choices that look risky in hindsight (premature, scope-creeping, papering over a symptom).
- Gaps the user would otherwise miss on a casual skim.

Every reply for a run that produced a trail ends with an "Attention" section. Lead with the model that actually answered, on its own line (`reviewed by <provider>/<model>`), then list each flag pointing to specific rows or moments. "No flags" is a valid value. The model name is not. If no second family is available, or you could not confirm which model answered, write `reviewed by: blocked — <reason>` and keep the flags you have. A same-model pass reported as cross-model is worse than no review.

## Reviewing the trail

Read top to bottom, follow the evidence pointers, spot-check. GitHub renders a committed TSV as a table. `column -s$'\t' -t decisions.tsv` renders it in a terminal.

## Composing this skill

Other skills route their audit trail here instead of inventing one. Reference it by name and let it own the format. Don't restate the columns.
