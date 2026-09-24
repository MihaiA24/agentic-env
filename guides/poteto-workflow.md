# Start a new repo with the selected pstack skills

Use this guide in the repository you want to develop. It adapts Lauren Tan's pstack workflow to [our selected skills](../DECISIONS_AI_TOOLING.md#6-skills). You do not need her Cursor or Grok Bot setup.

The instructions below apply to your project. [The Atlas example](#worked-example-atlas) is optional reading, not an app or CLI installed by this stack. [The comparison with Lauren's workflow](#what-the-articles-use-that-this-stack-does-not) is at the end.

## Start here

1. **Prepare your host once.** Check [skill installation and invocation](#before-you-start). Skip reinstalling if your reviewed skills already load.
2. **Get one real user path running.** In an empty repo, build the smallest useful path first. In an existing app, exercise a path it already supports. Use [the startup prompts](#check-that-the-app-runs).
3. **Prepare the verifier.** Give the agent [the setup prompt in step 1](#1-create-the-project-verifier). It covers the executable tooling and feature map described in steps 2 and 3. These are one setup task, not three separate generations.
4. **Test and review the handoff.** Start a fresh agent session with [the replay prompt](#test-with-a-fresh-agent). Then [review the verifier files](#review-before-committing), using the setup brief as the specification. Resolve supported findings before product work.
5. **Develop and review.** Use [step 5](#5-use-the-verifier-on-real-changes) for each understood feature or fix. It includes separate review and handoff prompts.

Reuse a working verifier. Use [step 4](#4-keep-the-verifier-useful) when it has drifted. Use [steps 6–9](#part-2-understand-the-problem-then-design) only when the problem or design is unclear, or the work needs a durable plan. You do not run every skill for every task.

## Before you start

### Refresh the installed skills

Run this once when setting up a macOS/Linux host or adopting reviewed updates. Preserve intentional edits to installed skills first. Replace `/path/to/.dotfiles` with your checkout path.

```bash
cd /path/to/.dotfiles/agentic-env
uv tool install --force .
agentic-install-skills-mcps --skill-profile default --yes
agentic-stack-doctor
agentic-skill-drift --no-upstream
```

This installs the curated skills for Hermes, Claude Code, and Codex. OMP reads Claude's skill links. It installs no MCPs. For OMP, also check the `skills` mapping in `~/.omp/agent/config.yml` using the [refresh runbook](../README.md#refresh-skills-on-an-existing-omp-host). Native Windows and standalone copies use the [copying route](../README.md#python-only-copy-on-windows).

Investigate doctor and drift failures. Do not use `--update-baseline` to clear them. `foreign:<source>` means the recorded source differs, not necessarily the content. `--no-upstream` compares installed skills with local sources, not newer upstream revisions. These checks prove installation, not application behavior.

### Invoke skills in your harness

The prompts use `/name` as shorthand. Translate it to the form your harness accepts. Replace bracketed inputs with your task details and `<app>` with the name chosen from your repository.

| Harness | Invoke a skill | Project-local skill discovery |
|---|---|---|
| OMP | `/skill:<name>`, or ask it to load `skill://<name>` and use it | Reads `.agents/skills/` |
| Claude Code | `/<name>` | Reads `.claude/skills/`. Link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>`. |
| Codex | `$<name>` | Reads `.agents/skills/` |
| Hermes | `/<name>` | Reads `.agents/skills/` after you run `hermes skills trust` for the repository |

Run the Hermes trust command yourself. An agent must not grant trust or change global runtime settings for you.

Pstack skills are manual-only. OMP hides them from its automatic skill list but can load them by name. Hermes ignores the flag, so the skill's own guard is a behavioral instruction, not an enforced boundary. In OMP and Hermes, invoking a recipe authorizes the skills it names.

[Claude Code blocks model invocation of manual-only skills](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill). Invoke dependencies yourself in separate prompts before requesting synthesis. For example, `/teach` needs separate `/how` and `/why` invocations; `/technical-writing` needs a separate `/unslop` pass. Codex recipe composition is untested. Named loading does not prove a composed recipe works.

After host setup, start your coding agent in your project's root, not the `.dotfiles` checkout. Confirm `create-verification-skill`, `code-review`, and `handoff` are discoverable. In Claude Code, check the `/` menu yourself without running the skills; in Codex, check its skill list. In OMP or Hermes, use this loading check:

```text
Load create-verification-skill, code-review, and handoff by name.
Report whether each loads. Do not execute their recipes yet.
```

Shared skills stay on the host. App-specific verification belongs in the repository's `.agents/skills/`. `/code-review` bundles the six shared coding standards. A repo `CODING_STANDARDS.md` is only for repo-specific rules or waivers of individual rules. The shared standards apply when you run the review; they are not automatically injected into implementation sessions.

### Check that the app runs

For an empty repo, choose the stack and one useful outcome, then ask:

```text
Build the smallest working path for [user outcome] using [agreed stack].
Read any project instructions first. Run the result with disposable data
and prove the outcome through the real user interface or public API.
Document the launch command and prerequisites. Do not create a verifier
for planned features yet. Do not commit, push, or change global settings.
Stop only the processes you started and retain the proof.
```

For example, the first outcome could be creating one record and finding it after restarting the app. Settle an unclear outcome with [step 6](#6-restate-the-problem-and-build-a-mental-model) before building it.

For an existing app, use this instead:

```text
Read this repository's instructions and find its documented launch command,
existing drivers, and project verifier. Start an isolated development
instance and exercise one existing user path. Report the exact commands,
readiness check, result, and any missing prerequisites. Reuse existing
tooling. Do not create a new verifier yet, change global settings, commit,
or push. Stop only the processes you started.
```

Continue once that path works. If startup fails, fix it as a separate task or record the blocker before generating instructions. Use disposable data, test accounts, and isolated ports or profiles. Production access, infrastructure changes, and credential changes need separate authorization.

## Part 1: establish verification

### 1. Create the project verifier

Invoke `create-verification-skill` with this brief once the app runs. If an existing verifier has the sections and feature map below, test its handoff first. Use step 4 for drift in a complete verifier. Use this setup brief to fill missing structure or control tooling without discarding working parts.

```text
/create-verification-skill for this repository. Prepare it so another
coding agent can verify its work without this conversation.
Record the current commit, if one exists, and existing local changes
before editing, so the later review has a baseline.

Reuse the documented runner, existing automation, and any usable verifier.
Deliver .agents/skills/verify-<app>/SKILL.md, a map of the main existing
features, and executable commands for one representative user scenario.
Record the exact scenario and its starting state for the next agent.

Reuse a working scripted control path. If the next agent would need to
reconstruct scripts, launch state, or evidence collection, implement the
smallest missing helper now. Do not add a second automation framework.
Every documented command must exist. Exercise the recorded scenario's
commands; mark other feature recipes unverified until they are run.
Any helper you add must target its owned run, expose --help, return stable
results and evidence paths, and exit nonzero with a useful error on failure.
Give destructive operations --dry-run and observe what it actually skips.

Cover launch, readiness, read-only doctor, real user interaction, observed
results and side effects, evidence, and cleanup. Use disposable data and
owned instances. Keep credentials out of instructions and proof artifacts.

Prove the scenario end to end. Exercise a useful failure case and check
cleanup safety, including after failed attempts. Keep the evidence after
cleanup. Distinguish mapped, exercised, and blocked paths. Mark unexercised
recipes as unverified and check that every feature-index link resolves.

Return replay instructions, prerequisites, evidence locations, and how to
load the skill in the harnesses I use. Do not change product behavior to
make verification pass. Report product or startup blockers. Do not commit,
push, grant trust, change global settings, or schedule automation.
```

The installed generator requires the creator to prove one scenario. This setup brief requires reusable executable tooling; the replay prompt below adds proof by a fresh agent. Neither changes the installed skill.

The generated `SKILL.md` needs `name` and `description` frontmatter and these sections:

| Section | Required content |
|---|---|
| Launch | Exact command, configuration, test data, owned ports or profiles, and observed readiness signal |
| Doctor | Read-only check of the intended build, owned instance, valid auth, and correct data location |
| Drive | Real user commands or stable selectors, expected results, and starting state |
| Evidence | Action, resulting state, side effects, and a location that survives cleanup |
| Cleanup | Teardown of owned processes and disposable state, including failed attempts |
| Helpers | Executable scripts with documented invocations, or the existing commands they reuse |

The creator must follow these instructions successfully before handing them over. One proved scenario establishes the verifier, not whole-app coverage. Open the evidence yourself, then run the fresh-agent check and review below.

### 2. Make verification reproducible

A new CLI is optional. A reusable executable control path is required for handoff. Do not wait for several agents to repeat the work before filling a known tooling gap.

Use the richest control already available, such as the project's browser automation, Chrome DevTools Protocol, a PTY driver, HTTP commands, or native debugging tools. Add only the missing operations needed to drive and observe the app. A development-only sidecar is an option when the app has no usable control.

If you need a helper, require it to:

- Target the run it owns, using an explicit run ID or equivalent ownership check.
- Drive real user actions and wait for observable results rather than fixed sleeps.
- Expose its available commands through `--help` and return stable results and evidence paths, such as JSON.
- Exit nonzero on failure and explain the next useful action.
- Offer `--dry-run` for destructive operations. Observe what it skips rather than trusting the flag's name.
- Remove only owned resources and keep evidence outside disposable app state.

Document seed data, test accounts, required auth setup, and authorized test or staging APIs without storing credentials. Readiness only means the app is up. Doctor must also establish that it is the intended instance and build.

#### Test with a fresh agent

Stop the creator's app instances and leave its chat session idle. Open a separate session in the same checkout, with no prior conversation, and supply the verifier path and recorded scenario. Use the discovery rules above. In Claude Code, create the project-local link if needed without replacing existing files, then invoke the generated skill yourself.

```text
Use [generated verifier path] to repeat [recorded scenario]. Read the
repository instructions and verifier; do not use the creator's session.
Start your own isolated instance from the documented initial state.
Run launch, doctor, drive, evidence, and cleanup in order.

Do not reconstruct missing scripts or silently repair instructions.
Report missing prerequisites and commands as handoff failures. Preserve
evidence, including failures. Confirm cleanup leaves it accessible.
Report the exact commands, observed result, and any coverage gaps.
Do not edit files other than run artifacts, commit, or push.
```

Return failures to the creator, or give a new repair session the setup brief and replay report if no creator session exists. Repair verifier gaps, report product bugs separately, and repeat the check in another fresh session.

The replay passes when both agents prove the same scenario and retain evidence after cleanup. Repeat in each harness you intend to support. Report unavailable runtimes as untested; discovery alone is not a pass. Then [review the verifier changes](#review-before-committing) against the setup brief. Setup is complete after the replay passes and supported review findings are resolved.

Only one agent may drive shared app state at a time. Parallel implementations need separate checkouts, ports, profiles, and data. Read-only source research can run concurrently.

### 3. Map the app's existing features

The setup task creates `features/README.md` and one file per main feature, usually three to five initially. The index holds shared starting-state, evidence, and skip-reporting conventions. Each feature file uses these four sections in order:

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with <harness>`
4. `Gotchas`

Pair each entry point with an exact drive command and observable result. A checkbox and a menu action need separate recipes if both implement the feature. Proving one does not prove the other. Record blocked routes with the attempted action and missing prerequisite.

Every index link must resolve. Confirm each added feature exists from a concrete source path, but keep implementation details out of the map. Add cross-feature journeys when needed and expand coverage as work touches more of the app. Mark unexercised recipes as unverified, not working coverage. See [the complete feature-file example](#example-feature-map-entry).

### 4. Keep the verifier useful

Run maintenance after substantial changes or when the instructions stop matching the app. This is a full-map pass, not the affected-path check for each change. Lauren recommends daily maintenance; use a cadence that matches your project's churn.

```text
/maintain-verification-skill for [verifier directory]. Check every mapped
feature against source and exercise it live. Drive shared state serially.
Fix only documentation and helper drift inside the verifier directory,
and rerun corrected recipes. Report product regressions separately with
reproduction evidence; do not redefine expected behavior to hide them.
Keep evidence after cleanup. List blocked paths and missing prerequisites.
Report clean, changed, or blocked. Do not commit, push, or open a PR.
```

Independent source readers may run in parallel with enforced read-only permissions. One coordinator drives the app serially, checks each fresh instance with Doctor, and checks again after surprises or failures. Short-lived CLIs may need a fresh isolated session per drive.

- **Clean** means every mapped feature received source and live coverage without corrections.
- **Changed** means verifier corrections were made and proved by rerunning them.
- **Blocked** means coverage or a safe correction could not be completed.

A feature marked "verified-unreachable" needs a concrete prerequisite and the route attempted. It proves an obstacle, not working behavior. A missing prerequisite in the map is documentation drift to correct.

Report unclear product intent rather than guessing whether to change the map. Keep transient run notes out of commits. Product fixes belong in step 5.

### 5. Use the verifier on real changes

Record the baseline commit and existing local changes before editing. Name the user-visible outcome, read the affected feature-map entries, and use the verifier throughout implementation.

```text
Implement [approved outcome or ticket]. Read the affected verifier recipes
and establish the baseline first. Keep the change focused.
Use [project verifier] on disposable state to exercise the real user path,
its relevant failure cases, and neighboring behavior that could regress.
Check side effects and persistence where applicable. Correct failures and
repeat the same scenario. Keep useful regression tests.
Update the verifier for intentional behavior changes after proving them.
Retain the action, resulting state, exact commands, and evidence locations
through cleanup. Report blocked paths and risks. Do not commit or push.
```

For a UI, retain the interaction and resulting screen. For a CLI, retain the invocation, stdout/stderr, exit status, and changed files. For a service, retain requests, responses, and relevant stored state. Passing tests alone does not establish live behavior.

For a reported bug, use `/diagnosing-bugs` when the cause is unclear. Capture the reported path before editing when possible, fix its cause, and run the same path afterward. The report remains evidence even if local reproduction fails. Record the differing conditions rather than applying a guessed fix.

For performance work, define the start and end events before measuring. Keep fixture, machine, build mode, and cache policy consistent; separate cold and warm runs. Use repeated baseline and post-change runs, retain all samples and traces, and report the median and spread. Prefer a production build for user-performance claims. Report inconclusive results when noise obscures the effect.

#### Review before committing

Run this after verifier setup as well as after product changes. Invoke `/code-review` separately, naming a real baseline commit and the intended paths. Its scoped WIP snapshot includes uncommitted changes and non-ignored untracked files, so there is no need to commit first.

Inspect runtime evidence separately. Reviewers read the frozen snapshot and supplied context, not arbitrary evidence paths. Put relevant redacted observations in the task brief. Supply the pre-existing-change notes recorded before editing; the snapshot alone cannot identify which uncommitted edits predate the task.

```text
/code-review the intended work in [paths], in WIP mode against
[baseline commit]. Use [task brief or ticket] as the specification.
Include [pre-existing-change notes] and the brief's recorded observations
in the review context. Review Standards and Spec separately. Flag uncertain
scope rather than guessing which edits belong to this task.
Report findings only. Do not edit, commit, push, or publish anything.
```

In a new Git repository with no first commit, the snapshot helper has no valid baseline. Report that limitation and request a direct read-only review of the files and acceptance criteria instead. Do not create a commit merely to make the helper run.

Fix supported findings and rerun affected verification before review is complete. When a defect recurs, encode the lesson in a type, lint, shared helper, or runtime check rather than another generic instruction. The shared standards remain review-time rules, not automatic implementation instructions.

#### Hand off to another agent

Keep reusable verifier files in the repository. Use the existing `/handoff` skill for the current task's state:

```text
/handoff for the next agent to [next task]. Reference the repository,
current revision and uncommitted work, approved task, verifier path,
replay command and initial state, evidence locations, prerequisites,
proved paths, and remaining blockers. Name the skills to invoke next.
Reference existing artifacts instead of copying them. Redact secrets.
```

The skill writes to the OS temporary directory, not the repository. Give the next agent that file and access to the same checkout. It summarizes the work; it does not replace the fresh-agent replay.

For another machine, use an authorized transfer of the matching repository revision, tracked edits, and untracked files, including the verifier. Transfer the handoff and evidence too, then check their references. A patch alone may omit new files. `/handoff` does not package, commit, or upload the work; publication still needs separate approval.

## Part 2: understand the problem, then design

Use only the steps needed to resolve uncertainty. For an understood small change, return to step 5.

### 6. Restate the problem and build a mental model

Start with the report, not your proposed fix:

```text
Read [report or thread]. Restate in your own words and in plain English
what you think the underlying issue is. Separate observations from
assumptions and proposed solutions. List what the report does not tell
us. Do not propose a fix yet or change any files.
```

Correct misunderstandings before investigating. Ask for observed behavior, supporting code or historical evidence, hypotheses, and what would distinguish them.

| Skill | Use it to answer |
|---|---|
| `/how` | What runs, where, and in what order? |
| `/why` | What evidence explains the design, and which constraints must remain? |
| `/teach` | Why this approach rather than an alternative? It combines `/how` and `/why`. |
| `/recall` | What did earlier OMP or Hermes sessions try or learn? Name the topic, workspace, and time range. |

These skills explain code and history; they do not prove runtime behavior. `/recall` reads transcripts, not the durable memory bank. Skip it when the handoff is sufficient. `/why` should distinguish sources searched without results from sources it could not access. The articles' chat, monitoring, and analytics integrations are not installed by this guide.

Continue when the problem, constraints, and remaining unknowns are explicit. Use the verifier to check consequential runtime claims.

### 7. Work backwards from the caller's experience

Use this for shared code with real callers. Skip it for a change confined to one component.

Ask `/technical-writing` for a short caller tutorial before implementation. Each step should produce a visible result, including a failure case. Then use `/codebase-design` to assess what callers must know, which rules the module owns, and how consumers can test it. Invoke `/unslop` for the writing pass; follow the separate-invocation rules for Claude Code.

Reuse an existing operation when its semantics fit. Do not add a pass-through module or an extension point for hypothetical callers. Turn unresolved semantics into experiments in step 8. If the module ships, keep the validated tutorial as product documentation; otherwise remove the temporary draft after the work lands.

### 8. Answer design questions with prototypes

Define a question and comparison criteria before building alternatives. Our `/prototype` comes from Matt Pocock's skills, not Lauren's `/poteto-mode`.

| Question | Method | What it proves |
|---|---|---|
| What should this UI look like? | `/prototype` creates three structurally different variants by default, at most five, preferably on an existing route with `?variant=` and a switcher | The sketch's layout and interaction |
| Do these state rules make sense? | `/prototype` creates a standalone HTML page with visible state and walkthroughs | The modeled transitions, not application integration |
| Which timing, service, CLI, or native approach works? | Request a small throwaway experiment per viable alternative, using the existing runner | The behavior exercised under the recorded conditions |

UI prototypes use stubbed mutations. Logic prototypes run outside the app. Neither establishes production persistence. For a real timing question, exercise the actual operation with disposable data and controlled conditions.

Compare alternatives from the same starting state. For UI work, include keyboard access, focus, relevant error paths, and layout movement. Capture the action as well as the result. An accessibility tree does not prove screen-reader announcements; those require an assistive-technology check. Repeat timing measurements and report their spread.

For a consequential interface decision, use `/codebase-design` and its Design It Twice reference. Compare at least three independent sketches with common constraints, caller examples, types, invariants, and failure behavior. This is not Lauren's `/architect` arena and does not guarantee different model families or a cross-judge. Test measurable unknowns instead of substituting adversarial review of a code-free plan.

Choose a design from the evidence before production implementation. Revisit it if implementation exposes missing state or repeated caller workarounds. Rewrite the chosen UI under production constraints and remove prototype variants and switchers from shipped code. Creating a preservation branch, committing, or publishing it requires separate approval.

### 9. Write an execution plan only when needed

Plan after the design settles, when work spans sessions or people:

- `/to-spec` synthesizes a specification and checks testing seams with you. It uses `docs/agents/issue-tracker.md` and asks where to publish if that file is missing.
- `/to-tickets` proposes complete, demoable slices and genuine blocking dependencies. It can write local tickets under `.scratch/<feature-slug>/issues/<NN>-<slug>.md` while tracker configuration is unresolved.

Ask to see the breakdown before writing ticket files or publishing issues. Each ticket needs the chosen semantics, exact verifier actions, observable results, existing behavior to preserve, and blockers. Do not split a small feature into database, API, and UI tickets that cannot demonstrate an outcome independently. See [the example ticket](#example-implementation-ticket).

A mechanical migration may need expand–contract: introduce the replacement, migrate callers in verifiable batches, then remove the old form. Preserve visual behavior, including known quirks, and keep redesign separate. Each affected interaction needs before/after proof, not only a passing build.

Implement an approved unblocked ticket using step 5. Mark only criteria actually proved. If implementation invalidates a design assumption, report the evidence before widening the task. After the work lands, remove temporary plans and scratch files while preserving useful documentation and agreed evidence. Do not delete tracker history, close parent issues, or publish without authorization.

## Worked example: Atlas

This is our fictional web task board, not Lauren's desktop-assistant example with the same name. Assume it already has a documented launch command, browser automation, and create, complete, reopen, and filter flows. Undo completion is a proposed feature. Nothing in this section is installed tooling or evidence of a run.

In your project, derive names and commands from its code. Do not add Playwright, these features, or this CLI merely to match the example.

### Example control commands

Suppose the existing driver needs a helper. After implementing and exercising it, an agent might document commands like these:

```bash
node .agents/skills/verify-atlas/control-atlas.mjs launch --run r1 --seed basic
node .agents/skills/verify-atlas/control-atlas.mjs doctor --run r1
node .agents/skills/verify-atlas/control-atlas.mjs complete "Write report" --run r1
node .agents/skills/verify-atlas/control-atlas.mjs snapshot --run r1
node .agents/skills/verify-atlas/control-atlas.mjs cleanup --run r1 --dry-run
node .agents/skills/verify-atlas/control-atlas.mjs cleanup --run r1
```

These commands do not constitute the full proof. The recipe must also check persistence and side effects, retain evidence, and test failure and cleanup behavior. Use the actual run ID, not the illustrative `r1`.

### Example feature-map entry

This file describes existing completion behavior. It assumes the helper implements every command shown, including both completion entry points.

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

### Example implementation ticket

Suppose users struggle to recover accidental completions in the Active view. Compare a toast, an inline recovery row, and a recently-completed tray before choosing. Check recovery effort, multiple completions, filter changes, and keyboard focus. Separately test what happens when Undo arrives before the save finishes.

If you choose the tray and settle the semantics below, the resulting ticket could be:

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

These are example product decisions, not defaults chosen by a skill. Add Undo to the working feature map only after implementation and live verification.

## What the articles use that this stack does not

Lauren Tan's [Part 1 announcement](https://x.com/poteto/status/2094457600259842065) links her verification article; [Part 2](https://x.com/poteto/status/2097732320606507506) covers understanding and design. This repository keeps the [complete Part 1 text](../poteto/pstack-part-1.md) and [complete Part 2 text](../poteto/pstack-part-2.md). Steps 1–9 retain that order, but the startup instructions above are specific to this stack.

| In Lauren's articles | In this stack |
|---|---|
| Dr Eggbot creates an engineer bot | You invoke the selected skills in your coding agent. No bot-creation step is needed. |
| `/poteto-mode` and Cursor playbooks | Direct skill invocation, `/prototype`, and `/to-spec` or `/to-tickets` when needed |
| `.cursor/skills/verify-<app>/references/features/` | `.agents/skills/verify-<app>/features/` |
| Cursor Cloud Agents | Local agents with isolated checkouts, ports, profiles, and data. Shared app driving stays serial. |
| `/swarm` | Repeated local scenarios establish repeatability, not cloud scale, independent environments, or fuzzing coverage. |
| `/architect` and its multi-model arena | Ground the problem, compare interfaces with `/codebase-design`, and measure unknowns. This does not reproduce the arena. |
| Multi-phase plan validator and execution engine | `/to-spec` and `/to-tickets` produce reviewed work items. No automatic engine is provided. |
| Routines and Automations | Separately authorized scheduling through cron, systemd, or CI and a non-interactive harness |

The articles call the generated verifier `/control-app`; it is not another skill to install. Lauren's [example verifier](https://github.com/poteto/verification-skill-example) documents a desktop assistant and CLI commands, but does not include their implementation.

Before scheduling runs with `omp -p`, `claude -p`, `codex exec`, or `hermes -z`, prove one unattended run can load its skills, start its environment, retain evidence, and stop safely. Reading feedback, reproducing reports, modifying code, and publishing changes require separate permissions. A feedback message cannot authorize production actions.

### Build the lever: Lauren's rule and ours

Lauren's [pinned `principle-build-the-lever`](https://github.com/cursor/plugins/blob/c1c0a32/pstack/skills/principle-build-the-lever/SKILL.md) calls for a tool for any non-trivial work and counts a tool file in the diff as proof of applying the principle. In Part 1 she builds and polishes a verification CLI early, alongside the feature map.

We do not install that principle skill. [STANDARDS §2](../agentic_env/vendored/mattpocock/skills/code-review/STANDARDS.md#2-build-the-lever-narrowed) narrows it to repetitive or hard-to-review work and applies when `/code-review` runs. [STANDARDS §6](../agentic_env/vendored/mattpocock/skills/code-review/STANDARDS.md#6-encode-lessons-in-structure) covers encoding recurring lessons in structure.

This guide requires an executable handoff during verifier setup. Reuse existing commands when they suffice; build a helper when the next agent would otherwise have to reconstruct the work. Neither the bundled standards nor the installed generator alone enforces the fresh-agent replay. The setup and replay prompts above make those requirements explicit.

For shorter prompts by task, use [Choose a skill for the job](skill-routing.md).
