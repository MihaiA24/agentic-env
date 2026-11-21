---
name: create-verification-skill
description: "Manual only: generate a project-local verification skill and driver CLI that drive your app the way a user does — any language, framework, or platform. Run when the user asks: /create-verification-skill, \"make a control skill for this repo\", or when a project has no scripted way to prove UI/CLI/service behavior. Never start this on your own."
disable-model-invocation: true
---

# Create a verification skill

Manual skill. Run it when the user asks for it, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of generating anything.

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local skill (`.agents/skills/verify-<app>/`) tailored to the repo, with a driver CLI that agents run instead of writing throwaway scripts. You write the generator's output for the next agent, not for a human: it will be read cold, mid-task, by an agent that has never seen the app.

## 1. Interview the repo, not the user

Answer these from the codebase and only ask the user what you cannot observe:

- **Stack:** languages, frameworks and their versions from the manifests and lockfiles; the test runner, type checker and linter; the command CI runs. These decide the CLI's language, the harness to reuse and the runner for the smoke test.
- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, an API, a mobile app, a library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first — Playwright/Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port. Only then pick a generic recipe: browser/CDP for web and Electron, a tmux/PTY harness for CLI/TUI, plain HTTP for services. Drive through the repo's own runner and its documented commands. A second test framework standing beside the existing one is a maintenance burden the repo did not ask for.
- **Observe:** what evidence can be captured? Videos, screenshots, accessibility snapshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** derive ports, browser profile and data dir from the checkout path, so two checkouts run side by side. If the app cannot run twice, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session.

Then show the user, in a few lines, the stack and surface you found, and ask whether any part is missing, such as a service, tool or internal library the repo doesn't declare. Add what they name before generating.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating; a skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `.agents/skills/verify-<app>/SKILL.md` with YAML frontmatter (`name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it — without frontmatter the skill never registers) and these sections, each grounded in what the interview actually found (no placeholders left):

- **CLI:** one driver command in the skill directory, in the repo's main language, that every other section calls. It has a subcommand for doctor, launch, each drive action, each debug command and cleanup. Every subcommand has `--help` with a real example from this repo, prints JSON on stdout, and turns each error into the command to run instead. Destructive subcommands take `--dry-run`. The CLI and any helper are executable, and the skill body shows each invocation. For a full command surface, compare [poteto/verification-skill-example](https://github.com/poteto/verification-skill-example). It has no licence, so read it for ideas and write the code yourself.
- **Launch:** the exact command that starts the app for verification, and how to tell it's ready (a log line, a prompt). Launch must reach a usable state from an empty data dir, including any migrations and seed data. Ready means usable, not just that a process answers. A database health check can pass while its init scripts are still running. Include teardown. For a short-lived CLI or TUI there is no server to keep alive: launch means build the binary (or install deps) once, then start each drive in its own isolated PTY or tmux session.
- **Doctor:** one read-only check that answers "is this instance worth driving?" — process up, right version/build, port owned by us, auth valid. It reports who owns the port and whether the running build matches the checkout's current source, and it refuses an instance another checkout started. A stale build is not evidence. An agent runs this first whenever anything looks off.
- **Drive:** the harness recipe with real selectors/commands from this repo, not examples. Prefer stable handles (ARIA labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Debug:** commands that show the agent what happened, from what the surface exposes: for a UI, a screenshot, the accessibility tree, console and network; for a CLI or TUI, the PTY transcript and the exit code; for a service, the request, the response and the stored state. Each command writes its artifact to the evidence location and prints the path.
- **Evidence:** what to capture for a proof and where it goes. State the proof standards: exercise the real user path, not internal setters or test-only endpoints; capture the action and the resulting state, not just the final screen; verify side effects (files written, rows inserted, messages sent) alongside what's visible; mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser. A change's proof covers every entry point, mode and enabled flag variant the change affects, through the success, cancel, error, empty and persistence paths. Each step waits for an observable end state; a fixed sleep proves nothing. `eval` only reads state after the user path ran. For UI, screenshots are the default proof: one before the trigger and one of the stable end state, with snapshots as support. Record a video when the proof depends on the states in between, such as loading, animation or the order of updates.
- **Cleanup:** how to tear down instances the run created. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never the evidence: proof artifacts survive the teardown, in a location the skill names.
- **Smoke test:** one test in the skill directory, run by the repo's own test runner: the CLI's launch, then doctor, then one drive on seed data, then cleanup. The skill body shows the exact command, with the test's path: runners often skip hidden directories such as `.agents/`, so the runner's output must list the test as run. It proves the CLI still works, and `/maintain-verification-skill` keeps it green.

## 3. Seed the feature map

Create `.agents/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify (aim for the top 3-5 to start, from routes, commands, menus, or docs). Follow the shape in `references/feature-map-example/`, read as `skill://create-verification-skill/references/feature-map-example/README.md` in OMP or through `skill_view` in Hermes, with a README index and one file per feature. Each file answers, from the user's point of view: what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. The four H2s are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. The README index gives each feature the words users call it, such as "left sidebar" for `left-rail.md`, so a request in the user's words resolves to one file. If the seed data lacks a precondition that a journey needs, the journey reports a failure and the reason goes in that feature's `Gotchas`. Never weaken the journey to make it pass. The map is the repo's maintained verification source; a proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature (one is enough; the map exists so later runs can cover the rest), capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location — a cleanup that eats the proof fails this step. Then run the smoke test with the command the skill shows; this step is done when the runner's output lists it as run and passed. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable. If you proved it in a stand-in for the real target (a container in place of a fresh VM, a local stack in place of a remote one), list every setup step the stand-in did that the target will not. Those steps stay unverified until a run on the real target covers them.

## 5. Offer the maintenance loop

Point the user at `/maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.

## 6. Register it on the runtime that will use it

A generated skill nobody loads is a file. OMP discovers project-local skills under the repo's `.agents/skills/`; confirm the new directory shows up before you hand it over. Hermes is the secondary runtime here, and it only discovers a project's `.agents/skills/` after the human runs `hermes skills trust` for that directory. Never trust it for them and never edit their global Hermes configuration: either ask them to run the trust command, or hand the next agent the explicit-file route (`skill_view` on `.agents/skills/verify-<app>/SKILL.md`). Say in the hand-off which of the two applies, so nobody assumes discovery that isn't there.
