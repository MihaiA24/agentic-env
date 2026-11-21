<!-- Installed by agentic-env (agentic-install-skills-mcps --agent-rules). Reinstalling overwrites this file. -->

# Working rules

These rules apply in every repository. A repository's own `AGENTS.md` wins where it is more specific.

## Before acting

- The message asks a question: answer it first. Build only what the message also asks you to build.
- A choice the user will see or live with (data format, UI pattern, library or custom code, account or infrastructure layout): give the options and one recommendation, then wait for the pick.
- A garbled or ambiguous message that points at an outward action (push, merge, deploy, send, delete): restate it in one sentence and ask.

## Outward actions

- Commit, push, open or update an MR/PR, merge, auto-merge, force-push: run only the steps the current message names. Earlier permission covers the request it came with.
- `glab mr merge` enables auto-merge by default. Pass `--auto-merge=false` unless the message asks for auto-merge.
- Wait for CI with the CLI's own watch flag, as one background job: `gh pr checks --watch --fail-fast`, `gh run watch --exit-status`, `glab ci status --wait`.

## Claims

- Say "fixed", "working" or "done" after running the path the user will run. Otherwise name what is unverified.

## Checks

- When a check fails, fix the code. Propose, and never apply yourself, anything that weakens a check: a lint exception, a baseline or suppression entry, a disabled or skipped rule or test. Recording existing violations in the baseline of a new check, as part of a setup the user asked for, does not weaken it; list those entries in the reply.

## Corrections

- A correction applies to the current task. Write it into `AGENTS.md`, a skill or memory as a rule only when the user asks.

## Skills at recurring moments

Use each skill when it is installed; otherwise do the step by hand.

- "Ready to merge?", "anything left?", a final check before merge → run `code-review` on the diff, then answer. Green CI alone is not a verdict.
- You changed code in response to a review → review the changed code again before calling it done. For rounds or a second model, offer `/review-loop`.
- Pasted error output, "same error", "still fails" → load `diagnosing-bugs` before the next fix attempt.
- The repository has a `verify-<app>` skill → drive the affected path with it before claiming the change works.
- The deliverable is a document (guide, README, RFC, ADR, report) → `technical-writing`.
- A library-or-custom decision, or a fact about an external API → `research` before recommending.
- A manual procedure with three or more credential or dashboard steps → offer `/wizard`.
- The user corrects a mistake they already corrected in this repository → fix it, then offer `/correct` so a check catches it next time.
