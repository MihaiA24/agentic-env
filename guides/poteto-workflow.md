# Apply the pstack workflow to a repository

This guide sets up one repository so that agents can prove their own changes. You add static guardrails, generate a `/verify-<app>` skill whose CLI launches, drives, and checks the app, and point every agent at it.

Steps 0–4 run once per repository. Step 5 is the daily loop and step 6 is the upkeep. Step 7 applies only when the problem or design is unclear.

[About the pstack workflow](poteto-workflow-background.md) summarises Lauren Tan's articles and talk, lists what this stack uses in place of her tools, and gives the reasons behind steps 1–4 and 6. You can follow the steps without it.

## 0. Prepare the host

Set up the host once with the [README runbook](../README.md#refresh-skills-on-an-existing-omp-host), or the [copy route](../README.md#python-only-copy-on-windows) on Windows. The runbook's `agentic-bootstrap` updates the agents and refreshes the skills, and its final doctor flags anything left. An older Claude Code can ignore the `AGENTS.md` rules from [step 4](#4-point-every-agent-at-the-verifier). Start your agent in the project's root.

### Invoke skills in your harness

The prompts below write `/name`. Use your harness's form:

| Harness | Invoke | Project skills |
|---|---|---|
| OMP | `/skill:<name>` | `.agents/skills/` |
| Claude Code | `/<name>` | `.claude/skills/`. The step 4 `AGENTS.md` lines point the agent at `.agents/skills/`; to type `/verify-<app>`, link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>` |
| Codex | `$<name>` | `.agents/skills/` |
| Hermes | `/<name>`; `/skill <name>` when a Hermes command has the same name | `.agents/skills/`, after you run `hermes skills trust` for the repository yourself |

pstack skills are manual-only, except `/technical-writing`, which the agent also loads when a document is the deliverable. Some load others by name: `/teach` loads `/how`, `/why` and `/unslop`; `/recall` loads `/unslop`; `/blast-radius` loads `/unslop`, plus `/review-loop` for a big change; `/technical-writing` loads `/unslop`. OMP, Codex and Hermes let the skill you invoked load them. [Claude Code loads a manual skill only when your message names it](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), even when another skill asks for it. In Claude Code, name every skill the recipe loads in the same message, each as a separate word with no punctuation attached: `/teach me how sessions expire. Run /how /why and /unslop as needed`.

## 1. Get one user path running

The verifier needs a working app to drive. For an existing app, go to [Add static guardrails](#add-static-guardrails). The step 2 generator fixes or reports a broken startup before it writes anything.

For an empty repository, pick a stack you can control well and one useful outcome. For what makes a stack controllable, see [Part 1: verification is the foundation](poteto-workflow-background.md#part-1-verification-is-the-foundation). Then build the smallest working path:

```text
Build the smallest working path for [user outcome] with [stack]. Run it
with disposable data, prove the outcome through the real UI or public
API, and document the launch command and prerequisites.
```

### Add static guardrails

Set up lint rules, types, and import boundaries before agents write much code in the repository. This section has two prompts. Send the ones that apply, in this order.

1. One command may already run every check locally and in CI, with the compiler's strict mode and the linter as errors. If it does, and you have seen each check fail on a violation and pass without it, skip this prompt. Otherwise, turn on what the stack already ships:

   ```text
   Turn on [compiler]'s strict mode and [linter] for this repository, as
   errors. Fix the violations if there are few; otherwise fail only on new
   ones. Make one command run every check, and point CI at it. Ask before
   adding a dev dependency. Show me each check failing on a scratch
   violation, then passing after the revert.
   ```

2. For each misuse that you have already corrected agents on here, and that `/correct` has not banned yet, run `/correct`. If you have none, skip this prompt. [Step 6](#6-keep-the-verifier-sharp) covers the mistakes that agents make later.

   ```text
   /correct I have corrected agents for [pattern] here, as in [commit or
   file]; use [replacement] instead. Ban it in [directories].
   ```

`/correct` is in the `default` profile. It adds each ban with the repository's own tools and proves that each new check fails on that past mistake. No disable comment can turn a ban off. The agent may propose an exception, scoped to one file in the lint configuration, but adds it only when you tell it to.

## 2. Create the verifier and its CLI

```text
/create-verification-skill for this repository. Show me the evidence
for the feature you prove. Start the hand-off with a short summary in
plain language: the stack and surfaces you identified, what the CLI
can do, which features are mapped, and what is unproven or unmapped.
```

The skill needs your input at these points:

1. **Review the inventory.** The skill reads the repository and shows the stack, each surface with its features, the driver and debug tools it proposes for each surface, and the features it will map first. Tell it what is missing or wrong. When the stack offers no debug tools for a surface, the inventory proposes a dev-only sidecar or a debugger bridge. Agree to one before the skill builds the CLI. If the agent starts writing files without showing an inventory, the installed skill is probably out of date. Stop the run and repeat [step 0](#0-prepare-the-host).
2. **Read the hand-off.** By now the skill has written `.agents/skills/verify-<app>/`: a `SKILL.md`, the driver CLI, a smoke test, and a feature map of the three to five features users reach most. It has proved one feature end to end, run every other recipe and each debug command once, and run the smoke test with the repository's own runner. Read the evidence for the proved feature. The hand-off also lists:
   - Recipes marked unproven. A recipe that fails for a reason outside the repository, such as a missing system tool, comes with the command that failed.
   - Environments this machine cannot provide, such as another OS, a desktop session, or an external service. For each one the hand-off proposes a way to recreate it, such as a container image, a VM, or an emulator. The skill installs nothing, and you choose which proposal to use.
   - Every variant, feature, and surface that the map leaves out, including each documented variant that no recipe drives. The hand-off asks which to map next.

Spend time on this step. [The CLI matters most](poteto-workflow-background.md#step-2-the-cli-matters-most) says why, and describes what the CLI and the feature map contain.

## 3. Add checks and approve them with a fresh agent

A check pins a scenario you will maintain: a concrete behavior, an end-to-end use case or a performance measurement. Add checks only for the scenarios you want locked down; the drive commands and the feature map cover the rest.

```text
Add a check to the /verify-<app> CLI for each scenario below. A check
uses fixed input, seeds and clock, compares the result with an
expected result, exits non-zero on a mismatch, and prints JSON with
the difference and the evidence path. A performance check takes a
baseline ref, alternates at least five runs of each side, confirms the
work ran, and reports median and spread. Reuse the repository's own
runner and tests. Show me the evidence for each check.
Scenarios: [behaviors, end-to-end use cases, performance measurements]
```

Without a scenario list, ask it to propose scenarios from the feature map and pick the ones you will maintain. For a batch job such as Spark, a check runs the job on fixture input and compares its output, ignoring row order unless order is part of the contract.

Trust a check once you have seen it pass on the right result and fail on a wrong one, run by an agent that knows only the skill. Stop the app instances the check author started, open a new session in the same checkout, and run:

```text
Use /verify-<app> to run every check from a clean start, following the
skill as written. Then, for each behavior and end-to-end check, break
the behavior once in a scratch change, show me the check failing, and
revert. Report each missing command, prerequisite or step instead of
working around it.
```

Read the evidence and every expected result yourself. When they are right, commit them: they are now the approved behavior. Otherwise, send the report back to the session that wrote the checks, fix the verifier, and run this step again.

## 4. Point every agent at the verifier

Add this to the repository's `AGENTS.md`, which OMP, Codex, Hermes and Claude Code read. Claude Code reads it in every session from v2.1.281 (the stack's floor is newer), but only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above it. If one does, import `AGENTS.md` from it: `@AGENTS.md` in a root file, `@../AGENTS.md` in `.claude/CLAUDE.md`.

```markdown
## Verification

- `/verify-<app>` (`.agents/skills/verify-<app>/`) launches, drives and checks this app. Run the checks that cover your change and trust their result. Prove new behavior on the real user path, and show the evidence.
- Never change an approved check's expected result yourself. When behavior changes on purpose, show me the old and new result and wait for my approval.
- When you change a feature on purpose, update its file in `.agents/skills/verify-<app>/features/` in the same change.
- Ask before committing, pushing, opening a PR, or touching production, credentials or infrastructure.
```

Keep it this short. Launch, isolation, evidence and cleanup rules live in the verifier, where agents read them when they drive the app. Keep `/verify-<app>` model-invocable, so that agents load it through the first rule.

## 5. Build with the verifier

Each prompt states the outcome and asks for proof. The verifier and `AGENTS.md` carry the rest.

| Job | Prompt |
|---|---|
| Feature | `Build [outcome]. Run the /verify-<app> checks that cover it, propose a check for the new behavior, and show me the evidence.` For a nontrivial change, run `/how [subsystem]` first. |
| Reported bug | `Reproduce [report] with /verify-<app> and propose a check that fails on it. Then fix the cause and show the check passing.` If the cause is unclear, use `/diagnosing-bugs`. |
| Performance | `Run the /verify-<app> performance check for [scenario] against [baseline ref]. Make one targeted fix and run it again.` If no check covers the path, ask the agent to trace it and propose one first. Run `/benchmark-checklist` before you report the number. |
| Check the agent's reasoning | `/teach me why you implemented it this way and not [alternative].` |
| Review | `/code-review [paths] in WIP mode against [baseline commit]. Use [ticket or brief] as the spec.` |
| Pull request | `/pr for this branch. In the body, put the proof: each command that proves the change with its output, from the check command or /verify-<app>, and screenshots for a UI.` |

Proof shows the action and its result. For a UI that is screenshots before the action and of the end state, with a video when the states in between matter. For a CLI it is the command, output and exit status, and for a service the requests, responses and stored state.

A proposed check is trusted only after you approve it as in step 3.

`/code-review` freezes a snapshot that includes uncommitted and untracked files, so you do not need to commit first. A repository with no commits has no baseline; ask for a direct read-only review of the files instead.

Only one agent drives an app instance at a time. To work in parallel, give each agent its own checkout (a worktree). The verifier CLI derives that checkout's ports, profile and data, and refuses an instance another checkout started.

## 6. Keep the verifier sharp

```text
/maintain-verification-skill for .agents/skills/verify-<app>. Also run
every approved check from a clean start. Report each failure with its
old and new result, and do not edit any expected result.
```

The skill checks every mapped feature against the source, runs the verifier's smoke test, drives each feature live, fixes drift inside the verifier, and reports product regressions separately. It ends by offering to map the unmapped entries this machine can drive.

Read the diff afterwards. The skill may edit the verifier scripts that hold the checks. The prompt and the `AGENTS.md` rule tell it not to change an expected result, but nothing enforces them. A changed expected result is a change for you to approve, not drift.

Run the skill at least after large changes. To schedule it with cron or CI (`omp -p`, `claude -p`, `codex exec`, or `hermes -z`), first prove that one unattended run loads the skill, keeps its evidence, and stops cleanly.

As the map grows, keep it sweepable. Group the README index by area and order it as a top-to-bottom regression pass. Describe flows that cross features, such as two sessions at once, a global shortcut or state shared between views, in `features/journeys.md` and list it last, so a full sweep ends with them. Maintenance drives it like any other feature file. Split a feature file once one of its sections needs its own preconditions, and keep every entry runnable without reading source.

Treat the verifier as product code. When the CLI breaks or slows agents down, fix it before other work.

When agents make the same class of mistake twice, run `/correct`. It turns the class into an architecture change, a type, a lint or a test that fails on the old mistake, and documentation comes last. Prefer this to another `AGENTS.md` line. When the pattern is already common, a new lint first blocks only new occurrences. Then clean up the old ones in their own commits and delete deprecated code, because the next agent copies whatever it finds.

## 7. Resolve unclear problems and designs

Use only the parts the task needs. A small change you already understand goes straight to step 5. [Skill routing](skill-routing.md) has a prompt for each skill.

1. **Restate.** Give the agent the report, not your theory:

   ```text
   Read [report or thread]. Restate in your own words and in plain
   English what you think the underlying issue is. Separate what was
   observed from what is assumed. Do not propose a fix yet.
   ```

2. **Build the model.** Use `/how` for what runs and in what order, `/why` for the history and constraints behind it, and `/recall` for what earlier sessions tried. These explain code and history. Use the verifier to check claims about runtime behavior.
3. **Settle the choices only you can make.** With the model built, run `/grill-with-docs` on the plan. It asks the open decisions in rounds, each with a recommended answer, records resolved terms in `CONTEXT.md` and offers an ADR only for a decision that is hard to reverse. Use `/grilling` when nothing should be written down. Send measurable questions to a prototype instead.
4. **Write the caller's tutorial** for shared code: `/technical-writing`, then `/unslop`. Keep it as documentation if the module ships.
5. **Prototype the open questions.** `/prototype` builds throwaway UI variants behind a switcher, or a standalone page for a state model. Drive each variant with `/verify-<app>` and choose from the captured evidence. For a consequential interface, compare at least three sketches with `/codebase-design` (Design It Twice). Remove the prototype code once the decision is folded into the real code.
6. **Plan only when the work spans sessions or people.** After the design settles, use `/to-spec` or `/to-tickets`. Each ticket names the `/verify-<app>` action and the result that proves it. Delete temporary plans when the work lands.

You can combine the parts in one prompt:

```text
/recall my work on [area] from the past 7 days. Use /how and /why to
explain how [area] works today. Then use /technical-writing to write a
tutorial for a new [module] that removes [problem class], from the
caller's side. /prototype the open questions, drive each variant with
/verify-<app>, and /teach me why the chosen design beats the current one.
```

In Claude Code, send it as one message and add `/unslop` to it as a separate word: `/recall`, `/technical-writing` and `/teach` load it.
