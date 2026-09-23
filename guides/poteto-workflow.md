# Start a new repo with the selected pstack skills

This guide sets up verification in a repository with the skills this stack installs. It adapts Lauren Tan's [Complete Guide to pstack, Part 1](https://x.com/poteto/status/2094457600259842065) on verification and [Part 2](https://x.com/poteto/status/2097732320606507506) on understanding and design to [our selected skills](../DECISIONS_AI_TOOLING.md#6-skills). The steps follow the articles' order. They are not a chain to run for every task.

## Before you start

### Refresh the installed skills

Run these commands from the `agentic-env` directory of your `.dotfiles` checkout. Replace `/path/to/.dotfiles` with the directory where you cloned it.

```bash
cd /path/to/.dotfiles/agentic-env
uv tool install --force .
agentic-install-skills-mcps --skill-profile default --yes
agentic-stack-doctor
agentic-skill-drift --no-upstream
```

The install writes the curated profile for Hermes, Claude Code, and Codex, and OMP reads Claude's skill links. It installs no MCPs. For OMP, the [refresh runbook](../README.md#refresh-skills-on-an-existing-omp-host) also checks the `skills` mapping in `~/.omp/agent/config.yml`.

Inspect doctor and drift failures before you continue, and never clear them with `--update-baseline`. A `foreign:<source>` finding means the recorded source differs, not necessarily the content.

### Invoke skills in your harness

The prompts in this guide write skills as `/name`. Use your harness's form:

| Harness | Invoke a skill | Loads the repo's `.agents/skills/` |
|---|---|---|
| OMP | `/skill:<name>`, or ask it to read `skill://<name>` | Yes |
| Claude Code | `/<name>` | No, it reads `.claude/skills/`. Link `.claude/skills/verify-<app>` to `../../.agents/skills/verify-<app>`. |
| Codex | `$<name>` | Yes |
| Hermes | `/<name>` | Only after you run `hermes skills trust` for the repository |

Run the Hermes trust command yourself. Do not let the agent grant trust or change runtime settings for you.

Pstack skills are manual-only. OMP and Claude Code honor that flag and hide them from the model's automatic skill list. Hermes ignores it, so the skill's own guard stops a run you did not request. Invoking a recipe authorizes the skills it names, so `/teach` may run `/how`, `/why`, and `/unslop`.

The vendored recipes that run other skills target OMP and Hermes only. Claude Code blocks one skill from invoking a manual-only skill, so there `/teach` cannot run `/how` or `/why`, and `/technical-writing` cannot run `/unslop`. `/recall` reads only OMP and Hermes session history. In Claude Code, invoke each skill yourself, one per prompt, including each part of the combined prompt in step 7. Codex is untested.

### Open the target repository

Start your harness in the repository root and ask:

```text
Load the create-verification-skill, maintain-verification-skill, how, and
teach skills by name. Report whether each loads. Do not run them.
```

Keep only app-specific verification knowledge in the repo's `.agents/skills/`. The shared skills stay on the host.

### Check that the app runs

Find the project instructions, run command, existing drivers, and any project-local verifier. Reuse a working verifier, and use step 4 if it has drifted. For an empty repo, first build and run the smallest useful user path, and do not map planned features. If an existing app will not start, fix or report that before writing verification instructions.

Use disposable data, test accounts, and isolated ports or profiles. Production data, credentials, infrastructure, and global runtime settings need separate authorization.

## What the articles use that this stack does not

Lauren works in Cursor and Grok Bot. These parts of the articles depend on them or on pstack skills we did not select:

| In the articles | Tied to | Use instead |
|---|---|---|
| Dr Eggbot and the engineer bots it creates | Grok Bot | Nothing. We don't use Dr Eggbot. Invoke the skills yourself. |
| `/poteto-mode` and its playbooks, pinned as a Custom Mode | pstack in Cursor | Invoke skills directly. Use `/prototype` in step 8 and `/to-spec` or `/to-tickets` in step 9. |
| `.cursor/skills/verify-<app>/references/features/` | Cursor | `.agents/skills/verify-<app>/features/` |
| Cloud Agents for parallel work | Cursor | Drive one app instance serially. Run agents in parallel only when each has its own worktree, ports, and data directory. |
| `/swarm` across cloud agents | Cursor Cloud Agents | Repeat the verifier run several times and compare the results. |
| Routines and Automations for daily maintenance and report reproduction | Grok Bot, Cursor | A cron job, systemd timer, or CI schedule that runs your harness non-interactively with `omp -p`, `claude -p`, `codex exec`, or `hermes -z`. It needs its own setup and authorization. |
| `/architect` | Unselected pstack skill | `/codebase-design` with `/prototype`, as in step 8 |
| `principle-build-the-lever` | Unselected pstack skill | [CODING_STANDARDS §2](../CODING_STANDARDS.md#2-build-the-lever-narrowed) and the CLI checklist in step 2 |

## Part 1: establish verification

### 1. Create the project verifier

Lauren recommends Dr Eggbot, a Grok bot, to create an engineer bot that runs this skill. We don't use Dr Eggbot. Once the app runs and no usable verifier exists, invoke the skill yourself:

```text
/create-verification-skill for this repository. Reuse its existing runner
and automation before adding helpers or dependencies. Keep the initial
feature map grounded in the main user-facing flows that exist today.
Use disposable state. Prove one mapped feature end to end, capture the
action and resulting state, clean up what you started, and confirm the
evidence survives. Do not commit, push, or change global configuration.
```

Expect `.agents/skills/verify-<app>/SKILL.md` with Launch, Doctor, Drive, Evidence, Cleanup, and Helpers sections. The agent picks the app name. The articles call this skill `/control-app`. Lauren's [example verifier](https://github.com/poteto/verification-skill-example) shows a finished one with Cursor paths and 34 feature files. It lists its CLI commands but omits the script.

### 2. Make verification reproducible

Give the agent the control you have by hand: drive the app, debug it, and take performance traces. Use the richest runtime the stack offers, such as the Chrome DevTools Protocol for web and Electron apps, the simulator for iOS apps, or lldb or a development-only sidecar where nothing else exists.

Lauren wraps that control in a small CLI inside the verifier, so agents run one command instead of writing a throwaway script. Her example has commands such as `doctor`, `snapshot`, `screenshot`, `trace`, and `cleanup`. The installed skill reuses the project's runner and drivers first. Add a CLI when agents keep writing one-off scripts for the same paths, and ask for these properties:

- Commands compose, following John Ousterhout's deep-module idea.
- Any command with destructive side effects accepts `--dry-run`.
- Subcommands reveal functionality gradually.
- Errors tell the agent what to do instead.
- `--help` describes every command.
- Output is machine-readable, such as JSON.

Keep the CLI executable in the verifier's directory and show its invocation in `SKILL.md`. Also write down how to seed development data, which test users and auth to use, which test or staging APIs to call, and the one command that brings the environment up. Make the CLI reliable before you add anything more advanced.

Check that:

- The launch, readiness, drive, evidence, and cleanup instructions match commands the agent ran successfully.
- The agent exercised a real user path and checked its side effects, not only mocks or internal setters.
- Cleanup removed only the run's temporary state and processes. The evidence files still exist.
- A fresh session in each harness you use loads the generated skill by name.

### 3. Map the app's existing features

The feature map lists each feature, what it does, how a user reaches it, and what proves it works. `features/README.md` indexes one file per feature. Each file has four sections: `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`.

The article says the skill catalogs every feature. The installed skill starts with the main three to five. Add the rest as changes touch them or during maintenance. One proved feature establishes the verifier, not full coverage, so record which features remain unexercised.

### 4. Keep the verifier useful

Lauren recommends running `/maintain-verification-skill` at least once a day. Agents also update the map as they change the app, and maintenance catches what they miss. Pick a cadence that matches how often the app changes, and run it after substantial changes or when the instructions stop matching the app:

```text
/maintain-verification-skill for .agents/skills/[verifier].
Check the feature map against source and exercise every mapped feature.
Drive shared app state serially. Fix verifier drift only; report product
regressions separately. Preserve evidence and report any blocked coverage.
Do not commit or push.
```

Source readers may work in parallel, but agents drive a shared app instance serially. Full maintenance is separate from the affected-path checks for an ordinary change.

### 5. Use the verifier on real changes

Name one concrete task and replace `[verifier]` with the generated skill name:

```text
Implement [small feature or fix]. Use /[verifier] to exercise the affected
user path and show the action, resulting state, and relevant side effects.
For a bug, demonstrate the failure before the fix and the same path working
afterward. Keep the change focused. Do not commit or push.
```

For a UI, ask for screenshots or video of the interaction. For a CLI, ask for the invocation, terminal output, exit status, and changed files. For a service, ask for requests, responses, and relevant stored state.

For performance work, trace the current behavior, fix it, and trace the same scenario again. Repeat each side several times and compare the spread, because one run proves little.

Keep useful regression tests, but also exercise the changed behavior. Update the verifier when intended behavior changes.

Lauren also reproduces user reports automatically from a feedback channel. Start with one report by hand, using the prompt above with the report as the bug. Automate it later with the scheduled job from the table above.

## Part 2: understand the problem, then design

### 6. Restate the problem and build a mental model

Ask the agent to restate a report before it proposes a fix. Keep your own hypothesis out of the prompt, so misunderstandings surface before code changes.

```text
Read [report or thread]. Restate the underlying problem in your own words
and in plain English. Separate observations from assumptions. Do not
propose a fix yet.
```

For a failure with an unclear cause, ask for what is known, the data behind it, and the best hypotheses before any fix. `/diagnosing-bugs` runs a full diagnosis loop when you need one.

Then build the mental model:

- `/how` traces runtime mechanics, for example `/how does a user complete the app's main task?`. It sends parallel read-only explorers only when a subsystem splits into independent parts.
- `/why` investigates intent. It always searches Git history, and it searches trackers, chat, and monitoring only through tools the session already has authorized. It lists every source it could not search. Scope it to one target and one question.
- `/teach` explains a change or subsystem through `/how` and `/why`. It edits no code and writes no lesson files. Asking the agent to teach its work also makes it read the code before it states conclusions.

```text
/teach me why you implemented [change] this way and not [alternative].
What tradeoffs did you make, and which parts did you verify?
```

Use `/recall` to rebuild earlier work from this workspace's session history when that history exists.

### 7. Work backwards from the caller's experience

For shared code or a package, write the caller's tutorial before the implementation. `/technical-writing` keeps tutorial, how-to, reference, and explanation apart and ends with an `/unslop` pass. `/codebase-design` assesses the interface the tutorial implies. Add `/recall` first when related history exists.

```text
Use /how and /why to explain how [area] works today. Then use
/technical-writing to draft a tutorial showing how a caller would use the
new [module]. Use /codebase-design to assess its interface. Stop before
implementation. Then /teach me why this design is better than the current
one, and back each claim with code you read or a /[verifier] run.
```

### 8. Answer design questions with prototypes

Don't accept the agent's first design, and don't refine an abstract plan without evidence. Answer open questions with `/prototype`:

- For a UI question, it builds several variants on the existing route, three by default, switched with `?variant=`. The verifier drives each one.
- For a logic or state-model question, it builds one standalone HTML page that steps through hard cases. Review that page yourself, because the app's verifier cannot drive it.

```text
/prototype [open question]. Build two or three alternatives. Use
/[verifier] to drive each one and capture screenshots and measurements.
Compare them against the question. Stop before production code so I can
choose.
```

`/prototype` has no branch for a behavior or timing question, and its UI branch needs a browser route. For those questions, and for CLIs, services, and native apps, ask for the smallest throwaway script per alternative. Observe what you are deciding: log the timing, print the output, or drive it with the verifier.

```text
Prototype [behavior or timing question] with the smallest throwaway script
for each of two or three alternatives, in a scratch directory. Observe the
result with /[verifier], logs, or timing output. Compare the alternatives
and stop before production code so I can choose.
```

Do not send an abstract plan to reviewers. Agents invent theoretical risks when no code backs the plan.

### 9. Write an execution plan only when needed

Plan after the design settles, and only when work spans sessions or people. `/to-spec` and `/to-tickets` publish to the tracker configured in `docs/agents/issue-tracker.md`. `/to-tickets` can write local files under `.scratch/` instead. Lauren deletes her plans when the work lands, so delete those files too. Each slice names a `/[verifier]` action and its observable result, because tests alone are not verification. Approve publication separately.

```text
/to-tickets for [settled design]. Split it into small PRs. In each ticket,
name the /[verifier] action and the observable result that proves it.
Show me the tickets and do not publish them until I approve.
```

For a small change you already understand, implement and verify it directly. [Choose a skill for the job](skill-routing.md) lists prompts for each route.
