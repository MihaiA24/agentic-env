# Skill cheatsheet

All 43 installed skills: 19 from Matt Pocock and 14 from pstack, grouped below by when you use them, plus ponytail (6), caveman (2) and the two opt-in Spark skills. Packs are defined in [`agentic_env/skill-packs.json`](../agentic_env/skill-packs.json). To pick a route for a task, use [skill routing](skill-routing.md). Invocation syntax per harness is in [Invoke skills in your harness](poteto-workflow.md#invoke-skills-in-your-harness).

**Starts** column:
- **Agent**: model-invocable; the agent picks it on its trigger.
- **You**: manual-only (`disable-model-invocation: true`); name it in the prompt, or invoke a skill that names it.

Unlike pstack's `/poteto-mode`, nothing here lets the agent escalate to a manual skill mid-task. Name it in the prompt when needed.

## During implementation

| Skill | From | Starts | When | Why |
|---|---|---|---|---|
| ponytail | ponytail pack | Always on, injected | Every change | Smallest change, reuse what exists, fix the root cause. A small diff is cheap to verify. |
| `/verify-<app>` checks | Generated per repository | Always on, through `AGENTS.md` | Every user-visible change | Proof on the real path. Approved checks stop the agent re-verifying in loops. |
| `diagnosing-bugs` | Matt | Agent | Something fails, throws or is slow | Builds a reproducible feedback loop before guessing a fix. |
| `tdd` | Matt | Agent | You ask for test-first | One behavior test at a time through the public interface, so tests survive refactors. |
| `blast-radius` | pstack | You | Risky change: lifecycle, shared state, downstream consumers | Finds what breaks outside the diff and proves, by running real code, the one fact that makes it safe. |
| `benchmark-checklist` | pstack | You | A measured number you'll report or act on | Checks what limits the number and that the work actually ran before you trust it. |
| `apache-spark-static` / `apache-spark-runtime` | This repository (opt-in) | Agent, if installed | Spark code, without or with execution evidence | Spark-specific correctness and performance risks. |

While it works, the agent can also pick `codebase-design`, `prototype`, `research` and `domain-modeling` on its own. For nontrivial changes, add `/how [subsystem]` to the prompt.

## Understand and decide (before code)

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `recall` | pstack | You | Rebuild the context of earlier sessions |
| `how` | pstack | You | How the current code works, and where a change should go |
| `why` | pstack | You | Why the code has its shape, from history and documents |
| `teach` | pstack | You | `how` and `why` explained to you; also after implementation |
| `research` | Matt | Agent | Outside facts from primary sources, saved as a file |
| `grilling` | Matt | Agent | Decisions only you can make, asked in rounds |
| `grill-with-docs` | Matt | You | `grilling` plus `domain-modeling`; writes the glossary and ADRs as you go |
| `domain-modeling` | Matt | Agent | Keep terms in `CONTEXT.md` consistent; check your claims against the code |
| `codebase-design` | Matt | Agent | Interface and seam design: simple interfaces that hide a lot of logic |
| `prototype` | Matt | Agent | Answer a measurable design question with throwaway code |
| `improve-codebase-architecture` | Matt | You | Report-only survey for code that can be restructured |
| `wayfinder` | Matt | You | Work too big for one session: a map of decision tickets |
| `to-spec` / `to-tickets` | Matt | You | Durable plan or tickets once the design settles; publishing needs your approval |

To ground a grilling session in facts, run `/how` and a scoped `/why` first, then `/grill-with-docs` on the plan. In Claude Code, send them as three separate prompts.

## Review and ship

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `code-review` | Matt | Agent | Review against the coding standards and against the spec, on a frozen snapshot of the changes |
| `interrogate` | pstack | You | Review by several models when a costly-to-undo doubt remains after the evidence |
| `pr` | Matt | Agent | Drafts the PR body; pushing it needs your approval |
| `technical-writing` | pstack | You | Substantial human-facing documentation |
| `unslop` | pstack | You | Remove AI-style tells from finished prose |
| `show-me-your-work` | pstack | You | Decision log for long or unattended runs |

## Setup, upkeep and learning

| Skill | From | Starts | Use it for |
|---|---|---|---|
| `create-verification-skill` | pstack | You | Once per repository: verifier, CLI and feature map |
| `maintain-verification-skill` | pstack | You | Periodically: re-check the whole feature map |
| `writing-for-agents` | Matt | Agent | Editing skills, `AGENTS.md` or `CLAUDE.md` |
| `wizard` | Matt | You | Script a manual step only you can do, such as credentials or infrastructure |
| `handoff` | Matt | You | Transfer work to another agent (written to `$TMPDIR`) |
| `retro` | Matt | You | After a costly session: report problems in the environment; changes nothing |
| `reflect` | pstack | You | After a costly detour: turn it into reviewed skill edits |
| `correct` | pstack | You | A mistake made twice becomes a guard: architecture, type, lint or test |
| `wait-what` | Matt | You | An explanation didn't land: re-explain it |

## Not for the implementation loop

- **`interrogate`:** it runs several models and costs a lot. Keep it for contested designs.
- **`grilling`, `grill-with-docs`:** they stop to wait for your answers.
- **`to-spec`, `to-tickets`:** they end by publishing.
- **`teach`, `how`, `why`:** read-only. They explain; they don't change anything.
