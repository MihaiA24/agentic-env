# pstack workflow: verify first, then design with evidence

Lauren Tan (@poteto) explains how she works with pstack in two articles:

- [Part 1: Verification is all you need](https://x.com/poteto/status/2094457600259842065) ([local copy](../poteto/pstack-part-1.md))
- [Part 2: The art of supervising someone smarter than you](https://x.com/poteto/article/2097732320606507506) ([local copy](../poteto/pstack-part-2.md))

[What the articles say](#what-the-articles-say) summarises each idea and links the step that applies it. [Apply it to a repository](#apply-it-to-a-repository) sets up one repository with this stack's skills. Her example verifier for a fictional app is [poteto/verification-skill-example](https://github.com/poteto/verification-skill-example).

## What the articles say

### Part 1: verification is the foundation

- **Verification closes the loop.** An agent that can drive the app and see the result keeps working until the task succeeds, without you as the bottleneck. Treat the verification skill as critical infrastructure. → [Steps 2–6](#2-create-the-verifier-and-its-cli)
- **Choose a controllable runtime.** Use the richest control your stack offers: Chrome DevTools Protocol for web and Electron, the simulator for iOS, lldb or a dev-only sidecar when nothing else exists. The harder the app is to control and debug, the less agents can do with it. → [Steps 1–2](#1-get-one-user-path-running)
- **Build the lever.** Give agents a tool, not only markdown: a small CLI that drives and debugs the app (navigate, interact, snapshot, screenshot, trace, console and network logs, doctor, cleanup). Agents run one command instead of writing a throwaway script, which saves tokens and makes verification reproducible. Make the CLI good and error-free before anything more advanced. → [Step 2](#2-create-the-verifier-and-its-cli)
- **Make the dev environment reproducible.** Seed data, test users and auth, test or staging APIs, and one consistent way to bring the app up. → [Step 2](#2-create-the-verifier-and-its-cli)
- **Map the features.** The feature map has one markdown file per feature: what it does, how a user reaches it, how to drive it, and its gotchas. It is a compact "materialized memory" of the codebase that every contributor's agent shares. → [Step 2](#2-create-the-verifier-and-its-cli)
- **Ask for proof in every prompt.** "Build X. Use /control-app to verify your changes and show me a video and screenshots as proof." For performance, trace the status quo first, make a targeted fix, and confirm the win over repeated runs. For user reports, reproduce first, then fix. → [Step 5](#5-build-with-the-verifier)
- **Parallelize in isolated environments.** She runs agents in the cloud, each on its own machine, rather than many local worktrees. → [Step 5](#5-build-with-the-verifier)
- **Maintain it daily.** Agents update the map as they work; `/maintain-verification-skill` catches what they miss. → [Step 6](#6-keep-the-verifier-sharp)
- **Garden the codebase.** "Every weed you pull becomes a rule": a lint, a type, a check. Constraints in code guide agents better than instruction files. → [Step 6](#6-keep-the-verifier-sharp)

### Part 2: understand the problem, then plan with code

- **Two failure modes.** Agents fail when the intent is under-specified or when they lack context. The fix is better context, not more detailed orders. → [Step 7](#7-resolve-unclear-problems-and-designs)
- **Let the agent restate the problem.** Ask it to explain the report in its own words before anything else. You catch misreadings early, and you avoid steering it with your own hypothesis. → [Step 7](#7-resolve-unclear-problems-and-designs)
- **Build a mental model you can check.** `/how` traces the mechanism, `/why` finds the historical intent, `/teach` explains both to you, and `/recall` restores context from earlier sessions. Use `/teach` after implementation too: "why this way and not the other?" → [Steps 5](#5-build-with-the-verifier) and [7](#7-resolve-unclear-problems-and-designs)
- **Work backwards for shared code.** Write the caller's tutorial first with `/technical-writing` and `/unslop`. It shows what will be built and gives the agent a target to check its work against. → [Step 7](#7-resolve-unclear-problems-and-designs)
- **Plan with code.** Don't accept the first design, and don't overcook an abstract plan. Prototype the alternatives, drive them with the verifier, and choose from the evidence. Adversarial review of an abstract plan produces imagined risks. → [Step 7](#7-resolve-unclear-problems-and-designs)
- **Architect bigger changes.** Ground the problem, sketch competing interfaces as types and call sites, judge them, and implement against the chosen sketch. Scrap it when call sites repeat the same workaround or the types need escape hatches such as `any` or forced casts. → [Step 7](#7-resolve-unclear-problems-and-designs)
- **Plan documents come last and stay short-lived.** Write an execution plan only after the design settles. Every task carries its own proof, because passing tests alone do not prove the code works. Keep each PR small, and delete the plan when the work lands. → [Step 7](#7-resolve-unclear-problems-and-designs)

### What this stack uses instead

| In the articles | In this stack |
|---|---|
| `/poteto-mode` and its playbooks | Name the skill in your prompt; [skill routing](skill-routing.md) helps you pick it |
| `/control-app` | The `/verify-<app>` skill you generate in step 2 |
| A CLI of drive commands | The same CLI, plus checks with expected results you approve (steps 2–3) |
| `.cursor/skills/verify-<app>/references/features/` | `.agents/skills/verify-<app>/features/` |
| Cursor cloud agents and `/swarm` | Local agents, each with its own checkout, ports, profile and data; no cloud fan-out |
| `/architect` with a cross-model judge | `/codebase-design` (Design It Twice) plus prototypes |
| Multi-phase plan playbook | `/to-spec` or `/to-tickets` |
| Dr Eggbot, routines and automations | Not included; schedule runs yourself (step 6) |
| Gardening by hand | `/correct` turns a mistake made twice into a lint, type or check |

## Apply it to a repository

Steps 0–4 run once per repository. Step 5 is the daily loop and step 6 the upkeep. Step 7 applies only when the problem or design is unclear.

### 0. Prepare the host

Install the skills once per host with the [README runbook](../README.md#refresh-skills-on-an-existing-omp-host), or the [copy route](../README.md#python-only-copy-on-windows) on Windows. Start your agent in the project's root.

#### Invoke skills in your harness

The prompts below write `/name`. Use your harness's form:

| Harness | Invoke | Project skills |
|---|---|---|
| OMP | `/skill:<name>` | `.agents/skills/` |
| Claude Code | `/<name>` | `.claude/skills/`; link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>` |
| Codex | `$<name>` | `.agents/skills/` |
| Hermes | `/<name>` | `.agents/skills/`, after you run `hermes skills trust` for the repository yourself |

pstack skills are manual-only. [Claude Code stops a manual skill from loading another one](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), so in Claude Code invoke `/how` and `/why` yourself before `/teach`, and run `/unslop` as its own prompt after `/technical-writing`.

### 1. Get one user path running

The verifier needs a working app to drive. For an existing app, go to step 2: the generator fixes or reports a broken startup before it writes anything.

For an empty repository, pick a stack you can control well (see Part 1) and one useful outcome, then build the smallest working path:

```text
Build the smallest working path for [user outcome] with [stack]. Run it
with disposable data, prove the outcome through the real UI or public
API, and document the launch command and prerequisites.
```

### 2. Create the verifier and its CLI

`/create-verification-skill` reads the repository and writes `.agents/skills/verify-<app>/SKILL.md` with launch, doctor, drive, evidence, cleanup and helper sections. It seeds a feature map of three to five features and proves one of them end to end. It does not require a CLI, so ask for one.

The goal is deterministic commands, kept in the repository, that agents run instead of working out the steps each time. That saves time, context and tokens. The CLI has two layers. Drive commands (doctor, launch, the actions the app needs, logs, cleanup) let an agent explore. Checks cover the scenarios you approved: a concrete behavior, an end-to-end use case, a performance measurement. An agent trusts a check's answer instead of re-verifying it in a loop.

```text
/create-verification-skill for this repository. Also build a small CLI
in the verifier directory, so agents run commands instead of writing
scripts: doctor, launch, the drive commands this app needs, logs,
cleanup, and one check per scenario below. A check uses fixed input,
seeds and clock, compares the result with an expected result, exits
non-zero on a mismatch, and prints JSON with the difference and the
evidence path. A performance check takes a baseline ref, alternates at
least five runs of each side, confirms the work ran, and reports median
and spread. Reuse the repository's own runner and tests. Use
subcommands, rich --help, errors that say what to do instead, and
--dry-run on destructive commands. Show me the evidence for each check.
Scenarios: [behaviors, end-to-end use cases, performance measurements]
```

Without a scenario list, ask it to propose scenarios from the feature map and pick the ones you will maintain. For a batch job such as Spark, a check runs the job on fixture input and compares its output, ignoring row order unless order is part of the contract. If the app has no usable control at all, ask for a dev-only sidecar or a debugger bridge first. Spend time here: every later step depends on these checks.

### 3. Approve the checks with a fresh agent

Trust a check once you have seen it pass on the right result and fail on a wrong one, run by an agent that knows only the skill. Stop the creator's app instances, open a new session in the same checkout, and run:

```text
Use /verify-<app> to run every check from a clean start, following the
skill as written. Then, for each behavior and end-to-end check, break
the behavior once in a scratch change, show me the check failing, and
revert. Report each missing command, prerequisite or step instead of
working around it.
```

Read the evidence and every expected result yourself. When they are right, commit them: they are now the approved behavior. Otherwise, send the report back to the creator session, fix the verifier, and run this step again.

### 4. Point every agent at the verifier

Add this to the repository's `AGENTS.md`, which OMP, Codex, Hermes and Claude Code read. Claude Code (v2.1.277 or later) reads it only when there is no `CLAUDE.md`; if the repository has one, add `@AGENTS.md` to it.

```markdown
## Verification

- `/verify-<app>` (`.agents/skills/verify-<app>/`) launches, drives and checks this app. Run the checks that cover your change and trust their result. Prove new behavior on the real user path, and show the evidence.
- Never change an approved check's expected result yourself. When behavior changes on purpose, show me the old and new result and wait for my approval.
- When you change a feature on purpose, update its file in `.agents/skills/verify-<app>/features/` in the same change.
- Ask before committing, pushing, opening a PR, or touching production, credentials or infrastructure.
```

Keep it this short. The second rule is what makes a check worth trusting: an agent that can rewrite the expected result can make any check pass. Launch, isolation, evidence and cleanup rules live in the verifier, where agents read them when they drive the app.

### 5. Build with the verifier

Each prompt states the outcome and asks for proof. The verifier and `AGENTS.md` carry the rest.

| Job | Prompt |
|---|---|
| Feature | `Build [outcome]. Run the /verify-<app> checks that cover it, propose a check for the new behavior, and show me the evidence.` For a nontrivial change, run `/how [subsystem]` first. |
| Reported bug | `Reproduce [report] with /verify-<app> and propose a check that fails on it. Then fix the cause and show the check passing.` If the cause is unclear, use `/diagnosing-bugs`. |
| Performance | `Run the /verify-<app> performance check for [scenario] against [baseline ref]. Make one targeted fix and run it again.` If no check covers the path, ask the agent to trace it and propose one first. Run `/benchmark-checklist` before you report the number. |
| Check the agent's reasoning | `/teach me why you implemented it this way and not [alternative].` |
| Review | `/code-review [paths] in WIP mode against [baseline commit]. Use [ticket or brief] as the spec.` |
| Hand off | `/handoff for the next agent to [task].` It writes to `$TMPDIR`, not the repository. |

Proof shows the action and its result: screenshots or a recording for a UI; the command, output and exit status for a CLI; requests, responses and stored state for a service.

A proposed check is trusted only after you approve it as in step 3.

`/code-review` freezes a snapshot that includes uncommitted and untracked files, so you do not need to commit first. A repository with no commits has no baseline; ask for a direct read-only review of the files instead.

Only one agent drives an app instance at a time. To work in parallel, give each agent its own checkout (a worktree), ports, profile and data.

### 6. Keep the verifier sharp

```text
/maintain-verification-skill for .agents/skills/verify-<app>.
```

The skill checks every mapped feature against the source, drives each one live, fixes drift inside the verifier, and reports product regressions separately. The `AGENTS.md` rule keeps it from rewriting an approved expected result, so a failing check reaches you as a regression or a change to approve. Lauren runs it daily; run it at least after large changes. To schedule it with cron or CI (`omp -p`, `claude -p`, `codex exec` or `hermes -z`), first prove that one unattended run loads the skill, keeps its evidence and stops cleanly.

Treat the verifier as product code. When the CLI breaks or slows agents down, fix it before other work.

Garden the codebase. When agents make the same class of mistake twice, run `/correct`. It turns the class into an architecture change, a type, a lint or a test that fails on the old mistake, and documentation comes last. Prefer this to another `AGENTS.md` line.

### 7. Resolve unclear problems and designs

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

Part 2's combined prompt, adapted to this stack:

```text
/recall my work on [area] from the past 7 days. Use /how and /why to
explain how [area] works today. Then use /technical-writing to write a
tutorial for a new [module] that removes [problem class], from the
caller's side. /prototype the open questions, drive each variant with
/verify-<app>, and /teach me why the chosen design beats the current one.
```

In Claude Code, send each named skill as its own prompt, in that order.
