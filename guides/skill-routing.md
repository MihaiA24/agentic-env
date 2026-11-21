# Choose a skill for the job

Use a skill only when the task needs one; otherwise do the work. This guide follows [Decisions §6](../DECISIONS_AI_TOOLING.md#6-skills) and lists every curated skill, grouped by when you use it: 19 from Matt Pocock, 17 in the pstack pack (16 pstack skills and the local `review-loop`), three from ponytail, two from caveman, and four opt-in first-party skills: two for Spark, `static-guardrails` and `delete-comments`. [`agentic_env/skill-packs.json`](../agentic_env/skill-packs.json) defines the packs. For host setup and a project verifier, use [the pstack workflow](poteto-workflow.md); the implementation, prototype and maintenance routes below use that verifier.

Invoke a skill in your prompt with your harness's syntax, listed in [Invoke skills in your harness](poteto-workflow.md#invoke-skills-in-your-harness). Invoking a recipe authorizes its named dependencies; Claude Code still loads a manual dependency only when your message names it. Reading a skill to check discovery does not invoke it.

The **Starts** column says who starts a skill:

- **Agent**: model-invocable; the agent picks it on its trigger.
- **You**: manual-only (`disable-model-invocation: true`); name it in the prompt, or invoke a skill that names it (in Claude Code, name it in the same message too). The agent does not start one on its own. With the [agent rules](../README.md#agent-rules) installed, it offers `/review-loop`, `/wizard` and `/correct` at their moments and you decide.

## Start without a skill

| Situation | Route |
|---|---|
| A small change you already understand | Implement it and exercise the affected user path with the project verifier. Show the evidence; skip the planning document, interview and critique. |
| A report you cannot restate yet | Have the agent [restate it](poteto-workflow.md#7-resolve-unclear-problems-and-designs) before any fix |
| Proof that a change works | The project verifier, on the affected paths |

The [agent rules](../README.md#agent-rules), installed by `agentic-bootstrap`, put these defaults in every session, with the skill to use at recurring moments: a merge-readiness question, a fix made after a review, a repeated error, and a mistake you correct a second time.

## During implementation

| Skill | From | Starts | When | Why |
|---|---|---|---|---|
| `ponytail` | ponytail | Agent | Writing, fixing, refactoring or reviewing code | Smallest complete change: reuse what exists, fix the root cause, say what was skipped. A small diff is cheap to verify. |
| `/verify-<app>` checks | Generated per repository | Always on, through `AGENTS.md` | Every user-visible change | Proof on the real path. Approved checks stop the agent re-verifying in loops. |
| `diagnosing-bugs` | Matt | Agent | Something fails, throws or is slow | Builds a reproducible feedback loop before guessing a fix. |
| `resolving-merge-conflicts` | Matt | Agent | A merge or rebase stops on conflicts | Rebuilds each side's intent from history before resolving. Stages only what it resolved or fixed, and finishes the merge or rebase only when you asked for that. |
| `tdd` | Matt | Agent | You ask for test-first | One behavior test at a time through the public interface, so tests survive refactors. |
| `blast-radius` | pstack | You | Risky change: lifecycle, shared state, downstream consumers | Finds what breaks outside the diff and proves, by running real code, the one fact that makes it safe. |
| `benchmark-checklist` | pstack | You | A measured number you'll report or act on | Checks what limits the number and that the work actually ran before you trust it. |
| `caveman` | caveman | Agent | You ask for terse replies ("be brief", "less tokens") | Shorter replies with the technical content kept exact. |
| `apache-spark-static` / `apache-spark-runtime` | This repository (opt-in) | Agent, if installed | Spark code, without or with execution evidence | Spark-specific correctness and performance risks. |

While it works, the agent can also pick `codebase-design`, `prototype`, `research` and `domain-modeling` on its own. For nontrivial changes, add `/how [subsystem]` to the prompt.

## Understand and decide (before code)

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `sharpen` | pstack | You | A shallow prompt: name what an expert would do, start from and check, then get the rewritten prompt |
| `recall` | pstack | You | Resuming earlier work: rebuild the context of earlier sessions |
| `how` | pstack | You | How the current code works, and where a change should go |
| `why` | pstack | You | Why the code has its shape, from history and documents; scope it to one target and question |
| `teach` | pstack | You | `how` and `why` explained to you; also after implementation, to explain the agent's work and reasoning |
| `research` | Matt | Agent | Outside facts from primary sources; cited reply by default, reusable note when requested or needed |
| `grilling` | Matt | Agent | Goals, constraints or choices only you can make, asked in rounds |
| `grill-with-docs` | Matt | You | A plan to stress-test: `grilling` plus `domain-modeling`, writing the glossary and ADRs as you go |
| `domain-modeling` | Matt | Agent | Keep terms in `CONTEXT.md` consistent; check your claims against the code |
| `codebase-design` | Matt | Agent | Interface and seam design: simple interfaces that hide a lot of logic |
| `prototype` | Matt | Agent | An unknown an experiment can measure, answered with throwaway code and the verifier |
| `improve-codebase-architecture` | Matt | You | Report-only survey for code that can be restructured |
| `wayfinder` | Matt | You | Work too big for one session: a map of decision tickets |
| `to-spec` / `to-tickets` | Matt | You | A settled design that needs coordination across sessions or people; publishing needs your approval |

To ground a grilling session in facts, run `/how` and a scoped `/why` first, then `/grill-with-docs` on the plan.

## Review and ship

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `code-review` | Matt | Agent | Review against the coding standards and against the spec, on a frozen snapshot of the changes |
| `review-loop` | pstack pack (local) | You | Review in rounds by one or more other models until a gate passes: approval, a score, or a round cap |
| `pr` | Matt | Agent | Drafts the PR body; pushing it needs your approval |
| `caveman-commit` | caveman | Agent | A Conventional Commits message: why over what; writes the message, doesn't commit |
| `technical-writing` | pstack | Agent | Substantial human-facing documentation; loads when a document is the deliverable |
| `unslop` | pstack | You | Remove AI-style tells from finished prose |
| `show-me-your-work` | pstack | You | Decision log for long or unattended runs |

## Setup, upkeep and learning

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `create-verification-skill` | pstack | You | Once per repository: verifier, driver CLI, smoke test and feature map |
| `maintain-verification-skill` | pstack | You | The verifier no longer matches the app: rerun the smoke test and re-check every mapped feature |
| `create-formal-verification-skill` | pstack | You | A promise that must hold however events interleave: a project skill that checks it formally on each change |
| `maintain-formal-verification-skill` | pstack | You | Verified code changed: bring the model back in line with the code and rerun it |
| `statechart` | pstack | You | Check a TLA+ model with TLC: a chart of the flow, or the path that breaks a rule. A formal verification skill usually loads it |
| `static-guardrails` | This repository (opt-in) | You | Once per repository, before agents write much code: compiler, lint, import boundaries and dead code; existing violations fixed or kept in a baseline outside the code, so only new ones fail |
| `delete-comments` | This repository (opt-in) | You | Clear a scope's comments into deletions, short ADRs and issue drafts, then ban new comments with a ratchet |
| `writing-for-agents` | Matt | Agent | Editing skills, `AGENTS.md` or `CLAUDE.md` |
| `wizard` | Matt | You | Script a manual step only you can do, such as credentials or infrastructure |
| `retro` | Matt | You | After a costly session: report problems in the environment; changes nothing |
| `correct` | pstack | You | A mistake made twice becomes a guard: architecture, type, lint or test |
| `ponytail-audit` | ponytail | Agent | Whole-repo quality report, ranked: bugs, security, load, untested risk, slow paths, and what to delete; changes nothing |
| `ponytail-debt` | ponytail | Agent | Collect `shortcut:` comments (and older `ponytail:` ones) into a ledger of deliberate shortcuts; changes nothing |
| `wait-what` | Matt | You | An explanation didn't land: re-explain it |

## Not for the implementation loop

- **`review-loop`:** each round spends other models and waits for them. Run it when the change is ready for review, not while you are still building.
- **`grilling`, `grill-with-docs`:** they stop to wait for your answers.
- **`to-spec`, `to-tickets`:** they end by publishing.
- **`teach`, `how`, `why`:** read-only. They explain; they don't change anything.

## Use explanation skills only for their own questions

Choose the skill that answers your question.

`/how` explains the current mechanism: what runs, where, and in what order.

```text
/how does [feature] handle [case]? Point to the relevant code and explain
it briefly. Do not change anything.
```

`/why` investigates why the code has its current shape. It searches broadly by default. For everyday use, specify one target, one question, and a source scope. The prompt below starts with Git history and project documents, widening only to authorized sources if the question remains open. It is read-only and reports unsearched or unreachable sources as coverage limits.

```text
/why does [module] [behavior]? Start with Git history and project documents.
Widen only to sources I have authorized, and list any evidence you could
not reach.
```

`/teach` explains how engineering work functions and why it was done that way. It uses `/how` and `/why`, separates evidence from inference, and states uncertainty. Diagrams use a format the session can render, such as Mermaid or plain text; image generation requires an available tool. It does not change code or create a course or learning workspace.

```text
/teach me why you implemented [change] this way and not [alternative].
What tradeoffs did you make, and which parts did you verify?
```

`/recall` reconstructs recent work from this workspace's session history and shared project record. Skip it when there is no relevant history.

```text
/recall my work on [topic] in this repository over the last 7 days.
Check the current state before recommending the next action.
```

## Choose Spark review by evidence

Use [`/apache-spark-static`](../agentic_env/skills/apache-spark-static/SKILL.md) for code and initial-plan review without running the workload. Known or estimated input volume refines the findings; unknown volume does not block review. Static findings cannot establish a measured bottleneck or speedup.

Use [`/apache-spark-runtime`](../agentic_env/skills/apache-spark-runtime/SKILL.md) when live cluster metrics or completed-run artifacts are available. Live plans, task populations, duration, and cost remain provisional until the actual action finishes. Ask for analysis only when you want diagnosis and ranked experiments before edits or reruns.

Both first-party skills are outside the default profiles; use the [Apache Spark installation route](../README.md#apache-spark-optimize-existing-jobs). Choose by available evidence, not job size; neither is a required first step for the other. Both preserve results and authorization boundaries without requiring a vendor platform or cluster upgrade.

## Settle human goals with grilling

Use `/grilling` to settle goals, constraints, or tradeoffs that require your choice before design begins. Use `/grill-with-docs` when the answers should stay in the repository: it also records resolved terms in `CONTEXT.md` and offers an ADR for a decision that is hard to reverse. Run `/how` and a scoped `/why` first, so you answer with the code's mechanism and history in view. Use experiments for measurable questions rather than repeating interviews about an abstract plan.

## Measure unknowns with a prototype

Use a prototype to answer a measurable question about an interaction, state model, or layout:

```text
/prototype the unresolved [interaction or state-model question].
Use /verify-<app> where applicable to exercise the result and capture evidence.
Compare the alternatives against the question. Stop before production
implementation so I can choose.
```

## Design a new interface from the caller's side

For a new module or API, describe how callers will use it before writing the implementation:

```text
Use /technical-writing to draft a short tutorial showing how a caller
would use [module]. Apply /unslop to it. Use /codebase-design to assess the
interface and its tradeoffs. Stop before implementation.
```

## Review in rounds with other models

`/review-loop` sends a frozen snapshot of the change to one or more other models, fixes the findings you would also fix, and reviews again until the gate passes. Put the gate in the prompt. Without one, it runs one reviewer from another provider for at most three rounds and stops when no blocker or should-fix finding is open.

```text
/review-loop this branch with a council of [model], [model] and [model].
Max 5 rounds, until each gives at least 9/10. Add [model] only once the
others reach 8.5. Out of scope: [what reviewers must leave alone].
```

State what is out of scope: every round grades the change against that brief. Fixes stay in the working tree; a commit, a push and PR text are separate requests. It needs the `omp` CLI for its reviewers. Use `code-review` for a routine single review.

## Plan durable work after the design settles

Use `/to-spec` or `/to-tickets` after the design settles, when work needs coordination across sessions or people. Each slice must name a live verification action and its expected result. Both skills end with publication. Require a separate approval before the agent publishes.

```text
/to-tickets for the settled [design]. In each ticket, name the /verify-<app>
action and the observable result that proves it. Show me the tickets and
do not publish them until I approve.
```

## Verify affected paths, and maintain the whole map separately

For an ordinary change, verify the affected paths. Do not run full maintenance for every change.

Invoke `/maintain-verification-skill` separately. It checks the feature map against the source, exercises every mapped feature, fixes verifier drift, and reports product regressions separately. See [Keep the verifier sharp](poteto-workflow.md#6-keep-the-verifier-sharp) for the prompt.

## Prove promises that must hold on every ordering

Run `/create-formal-verification-skill` once for code whose promise must hold however events interleave, such as a retry that must never charge twice. It writes a project skill that checks the promise on each change, and TLA+ results go through `/statechart`. Run `/maintain-formal-verification-skill` after changes to the verified code. See [Check rules on every ordering](poteto-workflow.md#check-rules-on-every-ordering) for the prompt and the Java prerequisite.

## Add static guardrails once

`/static-guardrails` sets up compiler strictness, lint bans whose errors name the fix, import boundaries and dead-code checks. It fixes existing violations or lists them in a baseline outside the code, so only new ones fail, and no comment in the code can disable a ban. Run it once, before agents write much code. Later, `/correct` handles a mistake made twice. The skill is opt-in. [Add static guardrails](poteto-workflow.md#add-static-guardrails) has the install command and the prompt.

## Clear comments, then ban them

`/delete-comments` sorts every comment in the scope you name as a tautology, excuse, stale comment or decision record, adapted from Matt Pocock's prompt. It deletes the comment, drafts an issue for the hack an excuse hides, or moves the decision into a short ADR. Then an ast-grep rule bans new comments, and the files it did not clean stay in a ratchet list until a later run cleans them. Tool directives and `shortcut:` markers stay. The skill is opt-in; [Add static guardrails](poteto-workflow.md#add-static-guardrails) has the prompt.

## Vet performance numbers before you use them

Run `/benchmark-checklist` before a speedup, regression, or library choice goes into a report, PR, or decision. It names what limits the number, checks errors and that the work really ran, and alternates at least five runs per side. A single ballpark run is allowed when you ask for one, and the report says so.

## Learn from a session, then make the lesson stick

Pick by what should change:

- `/retro` reports environment candidates, ranked by severity: navigation pointers, missing or unwired checks, standards rules, expensive tool calls, no-op instructions, missing information. It changes nothing.
- `/correct` takes a mistake class seen at least twice and makes it impossible, preferring architecture, then types, then a lint whose error names the fix, then a test, and docs last. It proves each guard fails on a real past mistake. It prepares one commit-sized change per class; you approve each commit.

## Methods this stack does not include

This stack excludes `/poteto-mode`, `/architect`, `/swarm` and `/no-comments`. For planning, use the routes above rather than the articles' `/poteto-mode`. Local subagents do not replace `swarm` coverage. Instead of `/no-comments`, the installed agent rules say to write no comments, `/delete-comments` clears a scope and bans new ones, and `/static-guardrails` blocks disable comments on bans.
