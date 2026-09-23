# Start a new repo with the selected pstack skills

Use this guide to establish a verification loop, then develop features, diagnose bugs, and make design decisions with [our selected skills](../DECISIONS_AI_TOOLING.md#6-skills). It adapts Lauren Tan's [Complete Guide to pstack, Part 1](https://x.com/poteto/status/2094457600259842065) on verification and [Part 2](https://x.com/poteto/status/2097732320606507506) on understanding and design. The linked posts are announcements; the repository keeps the [complete Part 1 text](../poteto/pstack-part-1.md) and [complete Part 2 text](../poteto/pstack-part-2.md).

The numbered steps follow the articles' order, with host setup kept separate. You do not run all of them for every task. Start from the row that matches your situation:

| Starting point | Begin here | Result before moving on |
|---|---|---|
| New or unfamiliar repo without a usable verifier | Prerequisites, then [steps 1–3](#1-create-the-project-verifier) | One real user path proved, with reusable instructions and preserved evidence |
| Verifier instructions no longer match the app | [Step 4](#4-keep-the-verifier-useful) | Corrected instructions, rerun proof, and explicit coverage gaps |
| Small feature or fix you already understand | [Step 5](#5-use-the-verifier-on-real-changes) | A focused change and proof of its user-visible behavior |
| Unclear report, new interface, or consequential design choice | [Steps 6–8](#6-restate-the-problem-and-build-a-mental-model), then step 5 | A grounded problem and a design supported by a working experiment |
| Settled design spans sessions or people | [Step 9](#9-write-an-execution-plan-only-when-needed) | Small implementation slices, each with observable acceptance criteria |

The worked example is **Atlas, a fictional web task board**, not Lauren's desktop-assistant example with the same name. Assume it already supports creating, completing, reopening, and filtering tasks. Undo completion is a proposed feature that the verifier does not yet cover. Example commands, APIs, and evidence layouts illustrate what to ask for; they are not tools installed by this stack or results of a run. Replace `/verify-atlas` with your generated verifier's name.

## Before you start

### Refresh the installed skills

Refresh when setting up the host or adopting reviewed skill updates, not before every task. Preserve intentional edits to installed skills first. Run these commands from the `agentic-env` directory of your `.dotfiles` checkout. Replace `/path/to/.dotfiles` with the directory where you cloned it.

```bash
cd /path/to/.dotfiles/agentic-env
uv tool install --force .
agentic-install-skills-mcps --skill-profile default --yes
agentic-stack-doctor
agentic-skill-drift --no-upstream
```

The install writes the curated profile for Hermes, Claude Code, and Codex, and OMP reads Claude's skill links. It installs no MCPs. For OMP, the [refresh runbook](../README.md#refresh-skills-on-an-existing-omp-host) also checks the `skills` mapping in `~/.omp/agent/config.yml`.

Inspect doctor and drift failures before you continue, and never clear them with `--update-baseline`. A `foreign:<source>` finding means the recorded source differs, not necessarily the content. `--no-upstream` checks the installed skills against local sources; it does not check for newer upstream changes. These checks prove installation and wiring. They say nothing about whether a project verifier works.

This managed refresh is for macOS/Linux. For standalone copies, including native Windows, use the [copying routes and discovery checks](../README.md#python-only-copy-on-windows) instead.

### Invoke skills in your harness

The prompts below use `/name` as shorthand. Translate every named skill to your harness's form:

| Harness | Invoke a skill | Loads the repo's `.agents/skills/` |
|---|---|---|
| OMP | `/skill:<name>`, or explicitly ask it to load `skill://<name>` and use it for the task | Yes |
| Claude Code | `/<name>` | No, it reads `.claude/skills/`. Link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>`. |
| Codex | `$<name>` | Yes |
| Hermes | `/<name>` | Only after you run `hermes skills trust` for the repository |

Run the Hermes trust command yourself. Do not let the agent grant trust or change runtime settings for you.

Pstack skills are manual-only. OMP and Claude Code honor that flag and hide them from the model's automatic skill list. Hermes ignores it, so the skill's own guard tells the agent to stop a run you did not request; this is not an enforced runtime boundary. In OMP and Hermes, invoking a recipe authorizes the skills it names, so `/teach` may run `/how`, `/why`, and `/unslop`.

The vendored recipes that run other skills target OMP and Hermes only. [Claude Code blocks model invocation of manual-only skills](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), so there `/teach` cannot invoke `/how` or `/why`, and `/technical-writing` cannot invoke `/unslop`. In Claude Code, invoke each dependency yourself in a separate prompt, then ask for synthesis of those results rather than relying on nested invocation. `/recall` reads only OMP and Hermes session history. Codex recipe composition is untested; named loading is not evidence that a whole recipe works.

### Open the target repository

Start your harness in the repository root and ask:

```text
Load the create-verification-skill, maintain-verification-skill, how, and
teach skills by name. Report whether each loads. Do not run them.
```

Keep only app-specific verification knowledge in the repo's `.agents/skills/`. The shared skills stay on the host. Loading a skill for this discovery check does not authorize executing its recipe.

### Check that the app runs

Find the project instructions, run command, existing drivers, and any project-local verifier. Reuse a working verifier, and use step 4 if it has drifted. For an empty repo, first build and run the smallest useful user path, and do not map planned features. If an existing app will not start, fix or report that before writing verification instructions.

For an existing app, use a bounded first prompt:

```text
Read this repository's instructions and find its documented launch command,
existing drivers, and project verifier. Start an isolated development
instance and exercise one existing user path. Report the exact commands,
readiness check, result, and any missing prerequisites. Reuse existing
tooling. Do not create a new verifier yet, change global settings, commit,
or push. Stop only the processes you started.
```

For an empty repo, replace "one existing user path" with the smallest useful outcome you want to build, such as "create one task and see it after reload." Build that path using the agreed stack first. A feature map of planned screens is not a substitute for a running app.

Use disposable data, test accounts, and isolated ports or profiles. Production data, credentials, infrastructure, and global runtime settings need separate authorization.

## What the articles use that this stack does not

Lauren works in Cursor and Grok Bot. These parts of the articles depend on them or on pstack skills we did not select:

| In the articles | Tied to | Use instead |
|---|---|---|
| Dr Eggbot and the engineer bots it creates | Grok Bot | Nothing. We don't use Dr Eggbot. Invoke the skills yourself. |
| `/poteto-mode` and its playbooks, pinned as a Custom Mode | pstack in Cursor | Invoke skills directly. Use `/prototype` in step 8 and `/to-spec` or `/to-tickets` in step 9. |
| `.cursor/skills/verify-<app>/references/features/` | Cursor | `.agents/skills/verify-<app>/features/` |
| Cloud Agents for parallel work | Cursor | Lauren prefers separate cloud machines to local worktrees. Here, drive shared app state serially. Parallel implementations each need their own checkout, ports, profile, and data. |
| `/swarm` across cloud agents | Cursor Cloud Agents | Repeat the same verifier scenario and compare results. This shows local repeatability. It does not give you cloud scale, fuzzing coverage, or independent environments. |
| Routines and Automations for daily maintenance and report reproduction | Grok Bot, Cursor | A cron job, systemd timer, or CI schedule that runs your harness non-interactively with `omp -p`, `claude -p`, `codex exec`, or `hermes -z`. It needs its own setup and authorization. |
| `/architect` | Unselected pstack skill | Ground the problem, compare caller-facing sketches with `/codebase-design`, and measure open questions with `/prototype`, as in step 8. This is a manual adaptation, not the original architecture arena. |
| `principle-build-the-lever` | Unselected pstack skill | [CODING_STANDARDS §2](../CODING_STANDARDS.md#2-build-the-lever-narrowed) and the CLI checklist in step 2 |

These substitutions keep the method but lose some platform capabilities. Before scheduling anything, prove one unattended run can load the intended skills, start its own environment, retain evidence, and stop safely. A headless command alone does not establish that.

## Part 1: establish verification

Verification closes the development loop. The agent changes the code, drives the real app, observes the result and side effects, and corrects the implementation until it meets the task. Lauren treats the verifier as critical infrastructure because it lets agents check their own attempts instead of making you test every iteration.

Her opening "gardener" argument also applies. When an agent repeats a mistake, fix it with stronger types, compiler checks, lints, or a shared implementation instead of making the agent instructions ever longer. Keep that principle alongside runtime verification. [CODING_STANDARDS §6](../CODING_STANDARDS.md#6-encode-lessons-in-structure) describes our version.

For the worked examples below, assume Atlas already has a documented development command and Playwright-based browser automation. Completing a task has two entry points: a checkbox and a task-row menu. These are illustrative assumptions. Do not add Playwright, a menu, or any other tooling to your own app because of them.

### 1. Create the project verifier

Lauren recommends asking Dr Eggbot to create an engineer bot that runs `/create-verification-skill`. We do not use Dr Eggbot. Once the app runs and no usable verifier exists, invoke the skill yourself. If a verifier already works, reuse it; if it has drifted, go to step 4.

The installed generator first answers five questions from the repository:

| Question | What the generated verifier must know |
|---|---|
| Surface | What a user touches: browser, terminal, desktop app, API, mobile app, or library |
| Run | The actual launch command, readiness signal, required configuration, auth, and seed data |
| Drive | Existing runners and drivers, plus stable selectors or commands for real user paths |
| Observe | Screenshots, recordings, terminal output, responses, logs, files, or stored state |
| Isolate | Which ports, profiles, and data belong to this run, and whether parallel instances are possible |

The next agent to read the verifier may know nothing about the app, so the verifier must contain executable instructions, not a list of tools to investigate later.

```text
/create-verification-skill for this repository. Reuse its documented
runner and existing automation before adding helpers or dependencies.
For Atlas, map the existing create, complete, reopen, and filter flows.
Undo completion is planned, not existing coverage.

Use an isolated instance and disposable state. Prove completing a task
end to end through the UI: capture the action, the updated list, and the
state after reload. Clean up what you started, including failed attempts,
and confirm the evidence survives. List mapped features not exercised.
Report how to load the generated skill in the harnesses I use.
Do not commit, push, grant project trust, or change global configuration.
```

Expect `.agents/skills/verify-<app>/SKILL.md` with `name` and `description` frontmatter, plus these sections:

| Section | Concrete Atlas example of the required detail |
|---|---|
| Launch | Exact project command, isolated port and data directory, and a readiness check that actually succeeded |
| Doctor | Read-only confirmation of the expected app/build, owned instance, usable auth, and correct data directory |
| Drive | Actual accessible names and commands for creating a task, selecting its completion checkbox, and switching filters |
| Evidence | Where to retain the action recording, before/after views, and independent readback of the saved change |
| Cleanup | How to stop the run's owned processes and remove its temporary state without deleting evidence |
| Helpers | Executable scripts, if any, with their invocations; reuse existing drivers when no helper is needed |

The generated layout might be:

```text
.agents/skills/verify-atlas/
  SKILL.md
  features/
    README.md
    create-task.md
    complete-task.md
    reopen-task.md
    filter-tasks.md
```

The app name and feature boundaries come from the repository. The articles call the generated skill `/control-app`; that is not another skill you need to install. Lauren's [example verifier](https://github.com/poteto/verification-skill-example) shows a finished desktop-app verifier with Cursor paths and a larger feature map. It documents CLI commands but does not include their implementation, so do not copy those commands and assume they exist.

**Creation is complete when:** the agent has followed its own Launch, Doctor, Drive, Evidence, and Cleanup instructions in order, shown one real feature working, confirmed the evidence survives cleanup, and checked named discovery in a fresh session of each harness you use. A generated file that has never been executed is still a draft. One proved feature establishes the verifier but does not cover the whole application.

Open the evidence yourself. If an unrelated missing asset blocks startup, the verifier may create temporary scaffolding only when it labels that scaffolding and removes it during cleanup. Use the discovery and trust rules in the prerequisites; the agent does not grant trust on your behalf.

### 2. Make verification reproducible

Give the agent the control you have by hand: interaction, debugging, logs, and performance traces. Prefer the richest runtime already available, such as Chrome DevTools Protocol for web and Electron apps, an iOS simulator, or lldb for a native process. A development-only sidecar is an option when the app otherwise exposes no usable control.

Lauren considers this control important enough to influence stack choice. For an existing project, first find the control you already have. Atlas's existing browser automation may already capture screenshots, recordings, traces, console output, and network traffic. A short, proved recipe is better than introducing a second driver.

#### Build a helper only for repeated work

Lauren's "Build the Lever" principle turns repeated interaction into a small CLI, so the agent runs one command instead of writing another throwaway script. The article recommends building that CLI early. Our installed skill reuses the existing runner first and adds a wrapper only when repeated work shows the runner is too awkward to use directly. [CODING_STANDARDS §2](../CODING_STANDARDS.md#2-build-the-lever-narrowed) explains the local threshold.

The command groups in her example are inspection, navigation, interaction, performance, log streaming, and health/cleanup. You do not need all of them. Start with the paths you actually repeat, and make them reliable before adding more.

A useful helper:

- Hides repeated mechanics behind a small interface. For example, one `complete` command can locate the task's row, act through the UI, wait for an observable result, and return that result. A collection of coordinate clicks and fixed sleeps leaves every agent to reconstruct the workflow.
- Targets the run it owns instead of attaching to an arbitrary open browser or server.
- Supports `--dry-run` on destructive commands such as cleanup. Observe what the dry run really skips; the name alone does not prove that files, processes, or network resources are untouched.
- Reveals functionality gradually through subcommands, with a `--help` that explains the commands actually available.
- Says what went wrong in each failure and which next command can resolve it.
- Returns JSON or another stable format that carries results and evidence paths, so the agent does not have to interpret decorative terminal text.

For Atlas, after repeated scripts justify a helper:

```text
Wrap the existing Atlas driver in a small executable CLI inside
.agents/skills/verify-atlas/. Add no second automation framework.
Cover the repeated launch, doctor, complete, reopen, filter, reload,
snapshot, and cleanup operations. Keep UI mutations on real user paths.
Take an explicit run ID so commands cannot drive another session.
Document invocations in SKILL.md and expose --help and JSON output.
Give cleanup a --dry-run and verify its actual side effects.
Exercise every documented command, including a useful failure case,
then repeat one complete proof from two fresh launches. Keep evidence
outside disposable app state. Do not commit or push.
```

The interface might look like this. These commands are illustrative, not installed:

```bash
node .agents/skills/verify-atlas/control-atlas.mjs launch --run r1 --seed basic
node .agents/skills/verify-atlas/control-atlas.mjs doctor --run r1
node .agents/skills/verify-atlas/control-atlas.mjs complete "Write report" --run r1
node .agents/skills/verify-atlas/control-atlas.mjs snapshot --run r1
node .agents/skills/verify-atlas/control-atlas.mjs cleanup --run r1 --dry-run
node .agents/skills/verify-atlas/control-atlas.mjs cleanup --run r1
```

For a misspelled task title, useful hypothetical error output would be:

```json
{"ok":false,"error":"No task titled 'Write reprot'. Run snapshot --run r1 to inspect visible tasks."}
```

Also document how to seed development data, which test accounts to use, which authorized test or staging APIs to call, and how to bring up the environment consistently. Keep credentials out of the verifier and proof artifacts. A readiness check is not the same as Doctor. An HTTP response can show that a server is up without proving it is the intended build, account, or run.

**The control path is ready when:** documented commands have run successfully, an error gives a usable next step, repeated fresh runs produce the expected behavior, and cleanup removes only owned resources while preserving proof. Diagnose inconsistent runs before treating their results as evidence.

Lauren introduces Cloud Agents here to increase parallelism once verification works. Locally, the requirement is isolation. Concurrent implementations need separate checkouts, ports, browser profiles, and data, and only one agent drives shared app state at a time. Independent source-only research can still run in parallel. Do not mistake local repetition for `/swarm`'s cloud scale or fuzzing coverage.

### 3. Map the app's existing features

The feature map is a searchable description of what the app does, how a user reaches each feature, and how to prove it works. Lauren calls it "materialized memory." Agents share it as a compact summary, and the code remains the source of truth. The map saves agents from rediscovering navigation and preconditions on every task.

`features/README.md` indexes one file per feature and holds shared baseline, driving, evidence, and skip-reporting conventions. Each feature file has four sections, in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. Pair each action with an exact drive command and an observable result. Keep internal implementation tours out of this user-facing map.

An illustrative `features/complete-task.md`, using the hypothetical helper from step 2:

```markdown
# Complete a task

Mark an active task done, remove it from Active, and find it under
Completed after reload.

## Sub-features

- complete-checkbox: complete through the task checkbox.
- complete-menu: complete through the task-row menu.
- complete-persist: completion survives reload and changes filter membership.

## How to get to it (user POV)

From All, select a task's completion checkbox, or open its More actions
menu and choose Mark complete. Active hides completed tasks; Completed
shows them.

## Driving it with control-atlas

Preconditions: this run's Doctor passes. The basic seed contains active
tasks "Write report" and "Buy milk". Start in All, using
`node .agents/skills/verify-atlas/control-atlas.mjs filter all --run r1`.

- Checkbox: `node .agents/skills/verify-atlas/control-atlas.mjs complete "Write report" --run r1`.
  The task remains in All with completed state. Capture the action and result.
- Menu: `node .agents/skills/verify-atlas/control-atlas.mjs complete "Buy milk" --via menu --run r1`.
  The task shows completed state through this separate entry point.
- Filter: `node .agents/skills/verify-atlas/control-atlas.mjs filter active --run r1`.
  Neither task is shown. Switch with `filter completed --run r1` using the
  same helper invocation; both tasks appear.
- Persistence: `node .agents/skills/verify-atlas/control-atlas.mjs reload --run r1`.
  Both tasks remain under Completed. Capture the reloaded view and a
  read-only stored-state observation where the app exposes one safely.

## Gotchas

- Missing from Active does not mean deleted. Check Completed as well.
- Wait for the expected state or save response, not a fixed sleep.
- Start each independent recipe from its stated seed; do not reuse mutated
  data and silently change the expected result.
```

Use the run ID produced for your actual session instead of the example's `r1`. If the helper does not exist, record exact commands for the existing driver instead. An example command in this guide is not verification tooling.

The article aims to catalog every feature; the installed generator starts with the main three to five. Extend the map as changes touch other areas, or request a deliberate coverage expansion:

```text
Extend the project verifier's map to the remaining user-facing features
that exist today. Cite the source entry point behind each addition.
Follow features/README.md and exercise each new recipe on disposable
state. Report what you could not drive and why. Do not map planned
features, commit, or push.
```

**The map is useful when:** every index entry resolves to a feature file, each described entry point has a drive recipe and expected result, and coverage limits are explicit. Proving the checkbox path does not prove the menu path. Record a blocked path with the attempted action and missing prerequisite, not as a pass through some other path. Add cross-feature journeys where real interactions cross those boundaries. Do not add flows that exist only in plans.

### 4. Keep the verifier useful

Lauren recommends running `/maintain-verification-skill` at least daily. Agents update the map as part of ordinary changes, and maintenance catches what they miss. Match the cadence to your app's churn. Run it after substantial changes or when instructions stop matching the app. Scheduled runs need separate setup and authorization.

Full maintenance is not the affected-path check for every change. The installed maintenance skill:

1. Reconciles the feature index and its files.
2. Reads the source behind every mapped feature. Independent read-only readers may work in parallel; in OMP these are `scout` tasks. Without enforced read-only delegation, the coordinator reads the source itself.
3. Reconciles drift and newly discovered features. Every map change needs source evidence.
4. Drives every mapped feature serially, even if the source looks unchanged. It health-checks each new instance and checks again after surprises or failures.
5. Fixes verifier problems, reruns corrected recipes, preserves evidence, and reports product regressions separately.

For a long-lived web app, one coordinator drives one isolated instance. A short-lived CLI may need a fresh isolated session for each drive. Follow the verifier's Launch model; not every app runs like a long-lived server.

Triage determines what may change:

| Finding | Atlas example | Action |
|---|---|---|
| Documentation drift | An intentional rename changed Completed to Done | Update the map and prove the corrected route |
| Harness gap | Users can reach the menu action, but the helper cannot | Fix the verifier-owned helper and rerun the action |
| Product regression | Completion unexpectedly disappears after reload | Preserve reproduction evidence and report the product bug; do not redefine expected behavior |
| Unclear intent | The observed change has no established requirement | Report the ambiguity instead of guessing whether it is the new contract |

```text
/maintain-verification-skill for .agents/skills/verify-atlas.
Check the map against source and exercise every mapped feature.
Drive shared state serially. Fix only documentation and harness drift
inside the verifier directory, and rerun every corrected recipe.
Report product regressions separately with reproduction evidence.
Keep evidence after cleanup. List each blocked path, the attempted
route, and the missing prerequisite. End with clean, changed, or blocked,
explaining any incomplete coverage. Do not commit, push, or open a PR.
```

The outcomes have specific meanings: **clean** means complete source and live coverage with no correction needed; **changed** means proven verifier corrections; **blocked** means coverage or a safe correction could not be completed. When the skill marks a path "verified-unreachable," it has proved an obstacle. That result says nothing about whether the feature works.

**Maintenance is complete when:** every mapped feature has source coverage and a live result or explicit blocker, each retained correction has rerun evidence, and changes stay inside the verifier directory. Inspect the report and evidence; keep transient run notes out of commits. A product fix is a separate task under step 5.

### 5. Use the verifier on real changes

Day to day, the loop is short:

1. Name the user-visible outcome and read the affected feature-map entries.
2. Establish a known baseline. For a bug, capture the failing path when possible; for performance, measure before editing.
3. Make a focused change, then drive the affected user paths and check side effects.
4. If the result is wrong, use the observed failure to correct the implementation and repeat.
5. Update the verifier for intentional changes, check affected neighboring flows, and clean up while retaining evidence.

Choose relevant success, cancellation, error, empty-state, and persistence cases. Do not run every conceivable case for every edit. Keep useful regression tests, but passing tests do not prove that the user path works.

#### Build a feature with a defined outcome

If the feature is still ambiguous, use Part 2 first. Once the Undo design is chosen:

```text
Implement the agreed Atlas Undo completion design in [ticket or decision].
Reuse the existing task-state operations where their semantics fit.
Use /verify-atlas on disposable state to complete a task, undo it through
the chosen control, and reload to confirm the saved result.
Exercise the ticket's repeated-completion, dismissal, and failure cases,
plus existing complete, reopen, and filter paths that could regress.
Show the interaction and resulting state with video or screenshots.
Update the feature map and any helper that needs to drive the new action.
Keep the change focused. Do not commit or push.
```

Do not add Undo to the map as working coverage until the behavior exists and its recipe has been exercised. The interface examples in Part 2 are proposals until selected and implemented.

#### Fix a reported bug

```text
Bug: reopening a task from Completed does not show it under Active until
reload. Use /verify-atlas to capture that path on disposable state before
editing, then find and fix the cause. Run the same path afterward and
show the before/after evidence, including state after reload.
If this environment cannot reproduce it, report what differs and what
evidence is missing rather than applying a guessed fix.
Keep a regression test for the failure where practical, and check the
affected reopen and filter paths. Do not commit or push.
```

The report is evidence even when local reproduction is blocked. A useful handoff distinguishes a confirmed fix, a plausible explanation, and a missing reproduction. Use `/diagnosing-bugs` for an unclear cause rather than patching the first plausible symptom.

#### Improve performance with comparable measurements

Lauren first traces the status quo, makes a targeted fix, and uses `/swarm` to collect more verification runs. Locally, repeat a controlled scenario instead:

```text
Investigate Atlas initial load with a fixed fixture of 2,000 tasks.
Define the start and end events for time-to-usable-board before measuring.
Use /verify-atlas and the existing tracing tools to collect repeated
baseline runs. Keep the fixture, machine, build mode, and cache policy
consistent, and separate cold from warm runs.
Identify the measured bottleneck, make one targeted fix, then repeat the
same scenario. Report all samples, the median and spread, and trace paths.
Check the affected functional flows as well. Do not commit or push.
```

A production build is usually a better basis for user-performance claims than a development server, if the app supports one. Say how many samples you took and what reset between runs. Do not invent timings or declare a win from one fast sample.

If noise obscures the effect, report the result as inconclusive and improve the measurement before changing more code. Local repeated runs do not reproduce `/swarm`'s independent environments or fuzzing coverage.

#### Reproduce feedback before automating fixes

Lauren uses feedback-channel reports as triggers for cloud reproduction, and may automate fixes once she trusts the verifier. Start with one report by hand. Once reliable, a scheduled or event-driven job can reproduce reports in its own environment and retain evidence. Grant permission to read feedback, reproduce it, modify code, and publish anything as separate decisions. A channel message must not authorize production actions.

**A change is ready for your review when:** the handoff names the behavior changed, the checks actually run, evidence locations, any blocked paths, and remaining risks. For a UI, retain the interaction and resulting screen. For a CLI, retain the invocation, stdout/stderr, exit status, and changed files. For a service, retain requests, responses, and relevant stored state. Evidence must remain after cleanup.

Review the diff and proof before committing. When the same defect recurs, encode the lesson in the strictest mechanism that fits, such as a type, a lint, or a verifier recipe, rather than another generic instruction.

## Part 2: understand the problem, then design

Lauren identifies two recurring failures: the agent misunderstands your intent, or it lacks the context to do the work correctly. Use the steps below to resolve those gaps before implementation. An understood small change still goes straight to step 5.

### 6. Restate the problem and build a mental model

#### Restate before prescribing

Ask the agent to restate a report before it proposes a fix. Keep your own hypothesis out of the prompt. This compresses a noisy conversation, exposes misunderstandings while they are cheap to correct, and gives the agent room to find a cause you did not anticipate.

```text
Read [report or thread]. Restate in your own words and in plain English
what you think the underlying issue is. Separate observations from
assumptions and proposed solutions. List what the report does not tell
us. Do not propose a fix yet or change any files.
```

For example, an Atlas user reports: "With Active selected on my phone, I accidentally completed 'Pay rent'. It vanished, and finding it under Completed took too long." Someone replies: "Add a five-second undo toast."

A premature answer is "Implement a toast that calls Reopen." A useful restatement is:

> Completing a task immediately removes it from the Active view. A user who completes the wrong task must leave that view to recover it. The user can recover it by opening Completed and choosing Reopen, but the reporter found that slow. We know the reported experience; we do not yet know whether list movement caused the mistake, whether Reopen restores the old position, or what recovery keyboard users need. A toast and a five-second duration are proposals, not requirements.

Correct the restatement if it misses the problem. Then investigate the unknowns rather than treating the proposed fix as the specification.

For an ambiguous failure, use Lauren's "what we know, what data, best hypotheses" pattern:

```text
Investigate why reopened Atlas tasks appear at the bottom of the list.
Give me the observed behavior, the code and historical evidence behind
it, and your best hypotheses. Say what would distinguish them. Use only
authorized sources and list missing evidence. Do not fix anything yet.
```

Use `/diagnosing-bugs` when you need a full diagnosis loop. Capture a reproducible failing path with the verifier to guide the fix, not to decide whether to believe the report. If your environment cannot reproduce it, record the conditions and the coverage limit.

#### Choose the explanation you need

These skills build a mental model. They do not, by themselves, prove runtime behavior.

| Skill | Question it answers | Useful Atlas prompt |
|---|---|---|
| `/how` | What runs, where, and in what order? | `/how does completing a task reach stored state and update the Active filter? Include what Reopen does differently and how ordering is decided.` |
| `/why` | What evidence explains the current design? | `/why does Reopen put tasks at the bottom? Start with Git history and project documents. I am considering changing this: identify constraints to preserve and evidence that remains missing.` |
| `/teach` | Can I understand and assess the agent's reasoning? | `/teach me why you implemented [change] this way rather than [alternative]. Explain the tradeoffs and distinguish code reading from behavior already verified.` |
| `/recall` | What did we learn or try in earlier sessions? | `/recall my Atlas completion and Reopen work in this workspace over the last 7 days. Then compare it with [new report] and check the current state.` |

`/how` handles a small question inline and uses parallel read-only explorers when the subsystem splits into independent parts. `/why` searches source control and, within your requested scope, already-authorized evidence sources.

Lauren also uses PR comments, tickets, design documents, chat, monitoring, error tracking, and analytics. The article mentioning them does not make those integrations available here. Ask `/why` to list the categories it did not search, and keep "not found" separate from "could not search."

`/teach` composes `/how` and `/why`, preserves their uncertainty, and replies without changing code or writing lesson files. Teaching also helps the agent, because explaining the mechanism forces it to read the code instead of asserting a plausible story. Collect any new runtime evidence as a separate verifier task, then ask `/teach` to explain it.

`/recall` reconstructs in-scope transcripts and the shared record of reports, fixes, and reverts, then checks the current state. It is not the same as querying a durable memory bank. Name the topic, workspace, and time range; skip it when you already have a sufficient handoff or no relevant history. Its transcript support is limited to OMP and Hermes, as noted in the prerequisites.

**Move on when:** the problem is clear, the affected runtime path and historical constraints are understood, and each remaining unknown is explicit. Read-only findings are evidence about code or history; verify consequential claims about the running app separately.

### 7. Work backwards from the caller's experience

For shared code or a package, write the caller's tutorial before the implementation. Lauren used this approach for Dune, her team's desktop framework. Describe building an app with the code, then work backwards to the interface. Writing the tutorial first keeps the design focused on what callers do, instead of filling a plan with implementation details.

Use `/technical-writing` to keep four different jobs separate: a tutorial builds something visible; a how-to solves a specific problem; a reference describes APIs and options; an explanation covers background and tradeoffs. The skill ends with `/unslop`. Here, ask only for the tutorial.

Skip this step if Undo belongs in one existing component. Use it if several actual callers need shared behavior. Do not invent a package or an extension point for hypothetical future callers.

```text
Use the /how and /why findings, plus relevant /recall results, to define
what the existing Atlas task module must preserve. Use
/technical-writing to draft a short caller tutorial for adding Undo
completion to a view. Put it in .scratch/undo-completion/tutorial.md.
Show one visible result at each step, including a failed or stale Undo.

Use /codebase-design to assess the interface implied by the tutorial.
Explain what the caller must know, what complexity the module hides,
and how a consumer would test it. Stop before implementation.
Then /teach me the tradeoffs, citing existing code and evidence already
collected. Separate a predicted improvement from a demonstrated one.
Do not commit or push.
```

In Claude Code, invoke the named skills yourself in separate prompts, including `/unslop`, rather than relying on the combined recipe above.

An illustrative caller tutorial might propose this sequence. These are candidate APIs, not Atlas code or a library shipped by this stack:

```ts
const completed = await board.complete(taskId);
// The task leaves Active. Show an Undo action for this completion.

const restored = await board.undoCompletion(completed.operationId);
// On success, the same task returns to Active at its previous position.
```

The tutorial should show how the UI offers those actions and displays the outcome. The sketch alone leaves open questions about interface, depth, locality, testability, and existing constraints:

- Can Undo expire? What happens after a reload, another completion, or an intervening edit? How does the caller recognize a rejected operation? Callers depend on these behaviors, so they are part of the interface.
- Does the module hide restoration and consistency rules that callers would otherwise duplicate? If Undo is exactly Reopen, reuse Reopen rather than adding a pass-through module.
- Is the rule owned in one place, or must every view keep its own copy of previous state?
- Can a consumer complete and undo through this interface and observe the result without reaching into internal storage?
- Does the proposal respect what `/why` found? A nicer-looking call is not enough if it loses required behavior.

State only the semantics you have settled. Turn unresolved questions into experiments in step 8. A tutorial is a target for verification, not proof that the proposed implementation works.

**Move on when:** you can follow the caller's path, understand its success and failure outcomes, and name what remains to be measured. If the shared module ships, turn the validated tutorial into real documentation. Otherwise keep it temporary and remove it after the work lands.

### 8. Answer design questions with prototypes

Do not accept the agent's first design, and do not keep refining an abstract plan without evidence. Lauren uses throwaway alternatives to answer open questions before committing to production code. Define the question and the comparison criteria first.

Our `/prototype` comes from Matt Pocock's skills, not Lauren's `/poteto-mode` playbook. Choose the route by the question you need answered:

| Question | Local route | What the result can prove |
|---|---|---|
| What should this UI look like? | `/prototype`: three structurally different variants by default, at most five, preferably on the existing browser route with `?variant=` and a switcher | Layout and interaction of the sketch, driven by the verifier |
| Does this logic or state model make sense? | `/prototype`: one standalone HTML page with visible state, free-play controls, and guided walkthroughs | Whether the modeled transitions express the intended rules; review it separately from the app |
| Which behavior, timing strategy, CLI, service, or native approach works? | Ordinary request for a small throwaway script per alternative | The behavior actually exercised under the recorded conditions |

The UI branch can create a throwaway route when no existing page is suitable. Its mutations use stubs, not the real backend. The logic page is not part of the running app. Neither proves production persistence or integration.

#### Compare an interaction

"Design Undo" is too vague. Ask a question about a user's action:

```text
/prototype the Undo completion affordance on the existing Atlas board.
Question: with Active selected on a narrow mobile viewport, can a user
recover an accidental completion without leaving the view?
Build three structurally different variants behind ?variant=: a toast,
an inline recovery row, and a recently-completed tray. Keep all prototype
mutations in memory, separate from real application writes.

Use /verify-atlas to drive each variant from the same baseline:
complete and undo one task; complete two and undo the first; change the
filter before undoing. Also try a keyboard-only path. Capture the action
and result, compare the criteria below, and give me the variant URLs.
Recommend one, then stop so I can choose. Do not commit, push, or create
branches.
```

Collect the same observations for each variant:

| Criterion | Observation to collect |
|---|---|
| Recovery effort | Actions needed from mistaken completion to restoration |
| Task identity and position | Before/after screenshots and visible state for the same task |
| Multiple completions and filter changes | Which Undo actions remain reachable, and what each restores |
| Keyboard access and focus | A keyboard-only drive, including focus after the task disappears and returns |
| Accessibility | Accessible names, focus, and live-region structure; actual screen-reader announcements require an assistive-technology check |
| Layout stability | A recording or layout measurements showing whether the list shifts under a tap target |

A screenshot of the final state does not establish the interaction. A browser accessibility tree does not establish what a screen reader actually announces. Record those limits. If you measure timing, repeat the same scenario and report the spread; timing from a sketch does not predict production performance.

#### Explore the state rules

```text
/prototype the Undo completion state model as a logic prototype.
Question: is Undo identical to Reopen, or must it restore more?
Expose each task's status, position, and completion time. Include guided
walkthroughs for immediate Undo, completing two tasks and undoing one,
editing a completed task before Undo, and ordinary Reopen from Completed.
Keep state in memory. Stop so I can open the HTML file and try the cases.
Do not commit or push.
```

Click through the walkthroughs yourself. "That should not be possible" or "I expected the old position back" identifies a problem in the model before the implementation depends on it. The agent may also drive the standalone page if it has a suitable browser tool, but that is model evidence, not a run of the real app.

#### Measure a timing or behavior question

```text
Compare two approaches when Undo happens before a completion save
finishes: queue Reopen after the save, or cancel the pending completion
where the existing save mechanism supports cancellation.
Use the smallest throwaway script per viable alternative in a scratch
directory. Reuse the existing runner or /verify-atlas driver. Exercise
the real save path with disposable data and a controlled delay.
Record action order, responses, and stored state after reload. Repeat
under the same conditions and distinguish unsupported cancellation from
a failed implementation. Recommend an approach and stop before production
changes. Do not commit or push.
```

This is an ordinary experiment request, not a third `/prototype` branch. For a CLI, inspect output, exit status, and written files. For a service, inspect requests, responses, and stored state. Choose observations that answer the question, even when an easier measurement is available.

#### Compare interfaces for larger changes

For a larger change, Lauren's `/architect` grounds the problem, sketches competing interfaces, cross-judges and synthesizes them, implements against the sketch, and discards a design when implementation disproves it. We do not install that skill or its multi-model arena.

Use `/codebase-design`'s Design It Twice reference when there is a real interface decision. It sends three or more independent designers with different constraints, such as minimizing the interface or making the common caller trivial. They return caller examples, types, invariants, error modes, hidden complexity, and tradeoffs. Compare depth, locality, and where callers cross into the module. This does not guarantee different model families or an independent cross-judge.

Lauren's example is rate limiting for external webhooks. Our adapted prompt is:

```text
We need rate limiting for external webhooks. Use /how and /why to ground
current ownership and delivery guarantees. Use /codebase-design and its
Design It Twice reference to compare three interfaces. Give each designer
the same constraints and ask for caller usage, types, and failure behavior.
Answer measurable unknowns with throwaway experiments against disposable
state. Recommend a design with evidence and unresolved limits.
Stop before implementation so I can review it. Do not commit or push.
```

During implementation, unexpected parameters or state are a reason to revisit the sketch. Repeated workarounds at unrelated callers or forced type escapes are evidence that the interface may be wrong. Rework or discard the design instead of spreading the workaround. This is not an instruction to restart for every new detail.

Do not send a code-free plan through adversarial reviewers as a substitute for these experiments. Lauren warns that such reviews invent theoretical risks. Review concrete designs, code, and measured behavior.

**Move on when:** you have chosen an alternative and recorded the question, evidence, tradeoff, and remaining limits where the work is tracked.

`/prototype` offers to preserve its source on a throwaway branch; creating that branch, committing, or publishing a pointer requires separate approval. Keep evidence accessible until implementation is verified.

Rewrite the winning UI under production constraints, remove the variants and the switcher from shipped code, and keep or discard the scratch prototype as agreed. Do not let prototype shortcuts slip into production code unnoticed.

### 9. Write an execution plan only when needed

Plan after the design settles, when work spans sessions or people. Lauren's multi-phase playbook turns the design into small, verifiable PRs, validates the plan's structure with a script, and executes it item by item. Our substitutes are `/to-spec` and `/to-tickets`; this guide does not provide her plan validator or an automatic execution engine.

- `/to-spec` synthesizes a specification from the conversation, checks testing seams with you, and publishes only after approval. It uses `docs/agents/issue-tracker.md`; if that is missing, it asks where to publish rather than choosing a tracker.
- `/to-tickets` proposes complete, demoable vertical slices with genuine blocking dependencies. It asks you to review granularity and dependencies before publication. It can write one local file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`; when tracker configuration is missing, local files are its fallback while it asks where work belongs.

Both methods need an explicit publication boundary. If you want drafts only, say so; even local ticket files are writes. Do not split a small feature into "database," "API," and "UI" tickets that cannot demonstrate anything independently.

```text
/to-tickets for the settled Undo completion design and prototype verdict.
Split only where each slice delivers a complete, verifiable outcome.
Each ticket must name the /verify-atlas action, the observable result,
and existing behavior that must remain unchanged. Include only genuine
blocking dependencies. Show me the breakdown and wait for approval before
writing ticket files or publishing issues. Do not commit or push.
```

For a complete example, suppose the prototypes led you to choose a recently-completed tray with task-specific Undo actions. The following semantics are illustrative product decisions, not defaults the skill chooses for you:

```markdown
# 01: Undo completion from the Active view

**What to build:** A recently-completed tray lets a user restore an
accidentally completed task without leaving Active. Each completion has
its own Undo action until the user dismisses it, navigates away, or reloads.
Undo restores the task's active state and previous position. If a task
was edited since completion, reject Undo visibly rather than overwrite
newer work; ordinary Reopen remains available through Completed.

When Undo is chosen during a pending save, wait for the completion save,
then restore the task. Report either save failure without claiming that
restoration succeeded. The tray is session-local, not durable undo history.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] /verify-atlas completes a task in Active, chooses its Undo action,
      and captures the task restored to its previous position.
- [ ] Reload and inspect stored state: the restored task is still active.
- [ ] Complete two tasks, undo the first, and confirm the second stays
      completed. Capture the interaction and both stored states.
- [ ] Choose Undo while the completion save is delayed. Once both writes
      finish, reload and confirm active state. Exercise a failed save too.
- [ ] Edit a completed task before Undo: the edit survives, Undo reports
      rejection, and Reopen still works through Completed.
- [ ] Exercise the keyboard recovery path and the tray's dismissal rules.
- [ ] Existing create, complete, reopen, and filter paths still work.
- [ ] The feature map documents the new behavior and its proved recipe.
```

Write the semantics you actually chose into your ticket instead of copying the example's. A fresh agent should not need your previous conversation to learn the acceptance criteria. If the slice is too large, split by complete supported cases, keeping unsupported cases explicit rather than shipping silent failure.

For a wide mechanical migration that cannot land safely as independent vertical slices, `/to-tickets` supports expand–contract: introduce the new form, migrate callers in verifiable batches, then remove the old form after every batch finishes. Do not retain compatibility paths once migration is complete. Lauren's StyleX example adds a strict constraint. Preserve visual behavior, including existing bugs, and do not mix migration with redesign.

```text
/to-tickets for the settled UI-library migration. Keep each slice
reviewable and runnable. Preserve current visual behavior, including
known quirks. Every ticket needs a before/after visual comparison and
live verification of the affected interaction, not only a passing build.
Separate unrelated fixes. Show the tickets before any publication.
```

Once a ticket and its implementation are authorized, work on any ticket whose blockers are complete:

```text
Implement [approved ticket path or URL]. Read its design decisions and
blockers first. Work on this slice only, using disposable data.
Run /verify-atlas for its acceptance criteria and affected existing paths.
Show the action, resulting state, side effects, and evidence locations.
Keep useful regression tests; passing tests alone are not live proof.
If implementation invalidates a design assumption, explain the evidence
before widening the task. Update the verifier for intended behavior
changes, and mark only criteria you actually proved. Do not commit or push.
```

For the handoff, keep the ticket state, changed behavior, evidence locations, and remaining blockers explicit. Use `/recall` for relevant OMP/Hermes history, but treat the current checkout and ticket as authoritative.

After the work lands, remove temporary local plans and scratch files while preserving useful product documentation and agreed evidence. Do not delete the tracker history, close parent issues, or publish changes without authorization.

For a small change you already understand, skip the plan and return to [step 5](#5-use-the-verifier-on-real-changes). [Choose a skill for the job](skill-routing.md) provides shorter prompts for individual routes.
