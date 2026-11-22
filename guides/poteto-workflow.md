# pstack workflow: verify first, then design with evidence

Lauren Tan (@poteto) explains how she works with pstack in two articles and a talk:

- [Part 1: Verification is all you need](https://x.com/poteto/status/2094457600259842065) ([local copy](../poteto/pstack-part-1.md))
- [Part 2: The art of supervising someone smarter than you](https://x.com/poteto/article/2097732320606507506) ([local copy](../poteto/pstack-part-2.md))
- [All Code Is Slop (Except Mine)](https://www.youtube.com/watch?v=O_zcc6Xl12g), a talk

[What the articles say](#what-the-articles-say) and [what the talk adds](#what-the-talk-adds) summarise each idea and link the step that applies it. [Apply it to a repository](#apply-it-to-a-repository) sets up one repository with this stack's skills. Her example verifier for a fictional app is [poteto/verification-skill-example](https://github.com/poteto/verification-skill-example). Steps 2, 5 and 6 adopt its checkout isolation, proof rules, cross-feature journeys and map layout. It has no licence and omits its driver script, so this repository links to it instead of copying it.

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

## What the talk adds

The talk reports the results on her team's agent app: 11,000 pull requests shipped last month, about 227 contributors in October, a stable release about once a day, and a revert rate steady at about 0.5%. Her pyramid orders where to spend time on the agent's environment, starting at the base. Only the first two layers are deterministic:

1. The code itself: API design, architecture, refactoring.
2. Lint rules, type systems, compilers and tests.
3. Runtime and formal verification.
4. Prose for what needs judgment: rules, skills and `AGENTS.md`.

- **Correct with code, not prose.** Each time you correct an agent, turn the correction into a deterministic check, or remove the problem with better API design. Agents copy workarounds, anti-patterns and deprecated code, because those look like the established pattern. → [Step 1](#add-static-guardrails) and [step 6](#6-keep-the-verifier-sharp)
- **Ban what needs nuance.** Her team bans `useEffect` in product code and allows it only inside its framework's APIs. Electron main-process and renderer code live in two top-level directories, and a dependency graph analyzer and lint rules forbid imports between them. Each ban is one less thing to catch in review. → [Step 1](#add-static-guardrails)
- **Replace comments with lint errors.** Agents wrote comments to justify quick fixes such as imperative timers, and the timers spread. The team now bans about 99% of comments, and lint errors tell the agent to fix the root cause. → [Step 1](#add-static-guardrails)
- **Block, then clean up.** "Start with a lint rule to prevent new occurrences of anti-patterns and then clean up those old patterns as well." → [Step 6](#6-keep-the-verifier-sharp)
- **Review the artifacts.** Code review has shrunk to verification artifacts: videos, screenshots, diagrams and formal verification. Most of her tokens go to verification. The feature map gives you and the agent shared words, so "the thingy in the left sidebar" means one feature. → [Steps 2](#2-create-the-verifier-and-its-cli) and [5](#5-build-with-the-verifier)
- **Verify flows formally.** TLA+ model-checks user flows such as notifications across devices, and Lean proves an algorithm in a virtualization library. `/statechart` draws a flow as a state machine from the user's point of view, which she reviews next to videos and screenshots. Formal verification has already found bugs, but she is still experimenting with it and treats it as one more layer, not a guarantee. This stack does not install it.
- **Test UI properties.** [Bombadil](https://github.com/antithesishq/bombadil) runs property-based tests on UIs and has caught UI bugs for her team. This stack does not install it.
- **Foundations before factories.** Automating a loop that produces slop produces more slop. On each release her team runs an agent that fuzzes the app like a user and opens fix pull requests that merge automatically. That works because the codebase makes most pull requests good by default. This stack does not install that release agent.

## What this stack uses instead

| In the articles and talk | In this stack |
|---|---|
| `/poteto-mode` and its playbooks | Name the skill in your prompt; [skill routing](skill-routing.md) helps you pick it |
| `/control-app` | The `/verify-<app>` skill you generate in step 2. Keep it model-invocable so agents load it through the step 4 `AGENTS.md` rule; her example verifier is manual-only. |
| A CLI of drive commands | The same CLI, plus checks with expected results you approve (steps 2–3) |
| `.cursor/skills/verify-<app>/references/features/` | `.agents/skills/verify-<app>/features/` |
| Cursor cloud agents and `/swarm` | Local agents, each with its own checkout, ports, profile and data, kept apart by the verifier CLI; no cloud fan-out |
| `/architect` with a cross-model judge | `/codebase-design` (Design It Twice) plus prototypes |
| Multi-phase plan playbook | `/to-spec` or `/to-tickets` |
| Dr Eggbot, routines and automations | Not included; schedule runs yourself (step 6) |
| Gardening by hand | `/correct` turns a mistake made twice into a lint, type or check |
| Lint bans and a dependency graph analyzer | `/correct` adds each ban and import boundary with the repository's own tools. Name the patterns you already know agents misuse (step 1); later it turns each mistake made twice into a check (step 6). |
| A ban on about 99% of comments | Not adopted. `/correct` blocks disable comments on bans and proves the block, and it reads comments that justify a workaround as evidence of a mistake class. pstack's `/no-comments` needs Cursor-only agents. |

## Apply it to a repository

Steps 0–4 run once per repository. Step 5 is the daily loop and step 6 the upkeep. Step 7 applies only when the problem or design is unclear.

### 0. Prepare the host

Set up the host once with the [README runbook](../README.md#refresh-skills-on-an-existing-omp-host), or the [copy route](../README.md#python-only-copy-on-windows) on Windows. The runbook's `agentic-bootstrap` updates the agents and refreshes the skills, and its final doctor flags anything left. An older Claude Code can ignore the `AGENTS.md` rules from [step 4](#4-point-every-agent-at-the-verifier). Start your agent in the project's root.

#### Invoke skills in your harness

The prompts below write `/name`. Use your harness's form:

| Harness | Invoke | Project skills |
|---|---|---|
| OMP | `/skill:<name>` | `.agents/skills/` |
| Claude Code | `/<name>` | `.claude/skills/`. The step 4 `AGENTS.md` lines point the agent at `.agents/skills/`; to type `/verify-<app>`, link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>` |
| Codex | `$<name>` | `.agents/skills/` |
| Hermes | `/<name>`; `/skill <name>` when a Hermes command has the same name | `.agents/skills/`, after you run `hermes skills trust` for the repository yourself |

pstack skills are manual-only, except `/technical-writing`, which the agent also loads when a document is the deliverable. Some load others by name: `/teach` loads `/how`, `/why` and `/unslop`; `/recall` loads `/unslop`; `/blast-radius` loads `/unslop`, plus `/review-loop` for a big change; `/technical-writing` loads `/unslop`. OMP, Codex and Hermes let the skill you invoked load them. [Claude Code loads a manual skill only when your message names it](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), even when another skill asks for it. In Claude Code, name every skill the recipe loads in the same message, each as a separate word with no punctuation attached: `/teach me how sessions expire. Run /how /why and /unslop as needed`.

### 1. Get one user path running

The verifier needs a working app to drive. For an existing app, go to [Add static guardrails](#add-static-guardrails). The step 2 generator fixes or reports a broken startup before it writes anything.

For an empty repository, pick a stack you can control well (see Part 1) and one useful outcome, then build the smallest working path:

```text
Build the smallest working path for [user outcome] with [stack]. Run it
with disposable data, prove the outcome through the real UI or public
API, and document the launch command and prerequisites.
```

#### Add static guardrails

Lint rules, types and import boundaries fail a bad change on every run, before you or the verifier look at it. Set them up before agents write much code in the repository. The verifier in step 2 then covers what they cannot express.

First turn on what the stack already ships, with a prompt:

```text
Turn on [compiler]'s strict mode and [linter] for this repository, as
errors. Fix the violations if there are few; otherwise fail only on new
ones. Make one command run every check, and point CI at it. Ask before
adding a dev dependency. Show me each check failing on a scratch
violation, then passing after the revert.
```

Then run `/correct` for each misuse you have already corrected agents on here. It is in the `default` profile, and it proves each ban fails on that past mistake.

```text
/correct I have corrected agents for [pattern] here, as in [commit or
file]; use [replacement] instead. Ban it in [directories].
```

`/correct` fixes the class at the highest level that works, from architecture down to a lint whose error names the replacement. No disable comment can turn a ban off. The agent may propose an exception, scoped to one file in the lint configuration, but adds it only when you tell it to.

### 2. Create the verifier and its CLI

`/create-verification-skill` reads the repository and shows you an inventory: the stack, each surface with its features, the driver it proposes for each surface and the features it will map first. It asks what is missing or wrong. Then it writes `.agents/skills/verify-<app>/`. That holds a `SKILL.md` with CLI, launch, doctor, drive, debug, evidence and cleanup sections, the driver CLI itself, a smoke test and a feature map of the three to five features users reach most. Each feature's recipe drives every variant the user docs promise for it, such as each documented shortcut, and the map names any variant, feature or surface it leaves out. It proves one feature end to end, runs every other recipe once, then runs the smoke test with the repository's own runner. A recipe that fails for a reason outside the repository, such as a missing system tool, comes back marked unproven with the command that failed. For each environment this machine cannot provide, such as another OS, a desktop session or an external service, the hand-off proposes a way to recreate it, such as a container image, a VM or an emulator. It installs nothing; you pick. The hand-off ends with the unmapped entries and asks which to map next.

The CLI matters most. It holds deterministic commands, kept in the repository, that agents run instead of working out the steps each time. That saves time, context and tokens. Its drive commands are primitives, such as click, fill or press a key, and each feature recipe combines them. Its ports, profile and data directory come from the checkout, and its doctor names the process holding its port or display and reports whether the build is current. The drive commands refuse to run against a stale build. With the CLI and the feature map, agents can already explore the app and prove their changes. Checks come in step 3.

```text
/create-verification-skill for this repository. Show me the evidence
for the feature you prove.
```

If the app has no usable control at all, ask for a dev-only sidecar or a debugger bridge first. Spend time here: every later step depends on this CLI.

### 3. Add checks and approve them with a fresh agent

A check pins a scenario you will maintain: a concrete behavior, an end-to-end use case or a performance measurement. An agent trusts a check's answer instead of re-verifying it in a loop. Add checks only for the scenarios you want locked down; the drive commands and the feature map cover the rest.

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

### 4. Point every agent at the verifier

Add this to the repository's `AGENTS.md`, which OMP, Codex, Hermes and Claude Code read. Claude Code reads it in every session from v2.1.281 (the stack's floor is newer), but only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above it. If one does, import `AGENTS.md` from it: `@AGENTS.md` in a root file, `@../AGENTS.md` in `.claude/CLAUDE.md`.

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
| Pull request | `/pr for this branch. In the body, put the proof: each command that proves the change with its output, from the check command or /verify-<app>, and screenshots for a UI.` |

Proof shows the action and its result. For a UI that is screenshots before the action and of the end state, with a video when the states in between matter. For a CLI it is the command, output and exit status, and for a service the requests, responses and stored state.

A proposed check is trusted only after you approve it as in step 3.

`/code-review` freezes a snapshot that includes uncommitted and untracked files, so you do not need to commit first. A repository with no commits has no baseline; ask for a direct read-only review of the files instead.

Only one agent drives an app instance at a time. To work in parallel, give each agent its own checkout (a worktree). The verifier CLI derives that checkout's ports, profile and data, and refuses an instance another checkout started.

### 6. Keep the verifier sharp

```text
/maintain-verification-skill for .agents/skills/verify-<app>. Also run
every approved check from a clean start. Report each failure with its
old and new result, and do not edit any expected result.
```

The skill checks every mapped feature against the source, runs the verifier's smoke test, drives each feature live, fixes drift inside the verifier, and reports product regressions separately. It ends by offering to map the unmapped entries this machine can drive. It knows nothing about checks, yet it may edit the verifier scripts that hold them; the last two sentences of the prompt cover that. Neither they nor the `AGENTS.md` rule enforce anything, so read the diff: a changed expected result is a change for you to approve, not drift. Lauren runs it daily; run it at least after large changes. To schedule it with cron or CI (`omp -p`, `claude -p`, `codex exec` or `hermes -z`), first prove that one unattended run loads the skill, keeps its evidence and stops cleanly.

As the map grows, keep it sweepable. Group the README index by area and order it as a top-to-bottom regression pass. Describe flows that cross features, such as two sessions at once, a global shortcut or state shared between views, in `features/journeys.md` and list it last, so a full sweep ends with them. Maintenance drives it like any other feature file. Split a feature file once one of its sections needs its own preconditions, and keep every entry runnable without reading source.

Treat the verifier as product code. When the CLI breaks or slows agents down, fix it before other work.

Garden the codebase. When agents make the same class of mistake twice, run `/correct`. It turns the class into an architecture change, a type, a lint or a test that fails on the old mistake, and documentation comes last. Prefer this to another `AGENTS.md` line. When the pattern is already common, a new lint first blocks only new occurrences. Then clean up the old ones in their own commits and delete deprecated code, because the next agent copies whatever it finds.

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

In Claude Code, send it as one message and add `/unslop` to it as a separate word: `/recall`, `/technical-writing` and `/teach` load it.
