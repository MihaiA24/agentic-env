# About the pstack workflow

This page is background for [Apply the pstack workflow to a repository](poteto-workflow.md). It summarises the ideas behind that guide's steps, lists what this stack uses in place of pstack's own tools, and gives the reasons behind steps 1–4 and 6. Nothing here is a required step, and the step numbers refer to the guide.

Lauren Tan (@poteto) explains how she works with pstack in two articles and a talk:

- [Part 1: Verification is all you need](https://x.com/poteto/status/2094457600259842065) ([local copy](../poteto/pstack-part-1.md))
- [Part 2: The art of supervising someone smarter than you](https://x.com/poteto/article/2097732320606507506) ([local copy](../poteto/pstack-part-2.md))
- [All Code Is Slop (Except Mine)](https://www.youtube.com/watch?v=O_zcc6Xl12g), a talk

[What the articles say](#what-the-articles-say) and [what the talk adds](#what-the-talk-adds) summarise each idea and link the step that applies it. Her example verifier for a fictional app is [poteto/verification-skill-example](https://github.com/poteto/verification-skill-example). Steps 2, 5 and 6 adopt its checkout isolation, proof rules, cross-feature journeys and map layout. It has no licence and omits its driver script, so this repository links to it instead of copying it.

## What the articles say

### Part 1: verification is the foundation

- **Verification closes the loop.** An agent that can drive the app and see the result keeps working until the task succeeds, without you as the bottleneck. Treat the verification skill as critical infrastructure. → [Steps 2–6](poteto-workflow.md#2-create-the-verifier-and-its-cli)
- **Choose a controllable runtime.** Use the richest control your stack offers: Chrome DevTools Protocol for web and Electron, the simulator for iOS, lldb or a dev-only sidecar when nothing else exists. The harder the app is to control and debug, the less agents can do with it. → [Steps 1–2](poteto-workflow.md#1-get-one-user-path-running)
- **Build the lever.** Give agents a tool, not only markdown: a small CLI that drives and debugs the app (navigate, interact, snapshot, screenshot, trace, console and network logs, doctor, cleanup). Agents run one command instead of writing a throwaway script, which saves tokens and makes verification reproducible. Make the CLI good and error-free before anything more advanced. → [Step 2](poteto-workflow.md#2-create-the-verifier-and-its-cli)
- **Make the dev environment reproducible.** Seed data, test users and auth, test or staging APIs, and one consistent way to bring the app up. → [Step 2](poteto-workflow.md#2-create-the-verifier-and-its-cli)
- **Map the features.** The feature map has one markdown file per feature: what it does, how a user reaches it, how to drive it, and its gotchas. It is a compact "materialized memory" of the codebase that every contributor's agent shares. → [Step 2](poteto-workflow.md#2-create-the-verifier-and-its-cli)
- **Ask for proof in every prompt.** "Build X. Use /control-app to verify your changes and show me a video and screenshots as proof." For performance, trace the status quo first, make a targeted fix, and confirm the win over repeated runs. For user reports, reproduce first, then fix. → [Step 5](poteto-workflow.md#5-build-with-the-verifier)
- **Parallelize in isolated environments.** She runs agents in the cloud, each on its own machine, rather than many local worktrees. → [Step 5](poteto-workflow.md#5-build-with-the-verifier)
- **Maintain it daily.** Agents update the map as they work; `/maintain-verification-skill` catches what they miss. → [Step 6](poteto-workflow.md#6-keep-the-verifier-sharp)
- **Garden the codebase.** "Every weed you pull becomes a rule": a lint, a type, a check. Constraints in code guide agents better than instruction files. → [Step 6](poteto-workflow.md#6-keep-the-verifier-sharp)

### Part 2: understand the problem, then plan with code

- **Two failure modes.** Agents fail when the intent is under-specified or when they lack context. The fix is better context, not more detailed orders. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Let the agent restate the problem.** Ask it to explain the report in its own words before anything else. You catch misreadings early, and you avoid steering it with your own hypothesis. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Build a mental model you can check.** `/how` traces the mechanism, `/why` finds the historical intent, `/teach` explains both to you, and `/recall` restores context from earlier sessions. Use `/teach` after implementation too: "why this way and not the other?" → [Steps 5](poteto-workflow.md#5-build-with-the-verifier) and [7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Work backwards for shared code.** Write the caller's tutorial first with `/technical-writing` and `/unslop`. It shows what will be built and gives the agent a target to check its work against. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Plan with code.** Don't accept the first design, and don't overcook an abstract plan. Prototype the alternatives, drive them with the verifier, and choose from the evidence. Adversarial review of an abstract plan produces imagined risks. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Architect bigger changes.** Ground the problem, sketch competing interfaces as types and call sites, judge them, and implement against the chosen sketch. Scrap it when call sites repeat the same workaround or the types need escape hatches such as `any` or forced casts. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)
- **Plan documents come last and stay short-lived.** Write an execution plan only after the design settles. Every task carries its own proof, because passing tests alone do not prove the code works. Keep each PR small, and delete the plan when the work lands. → [Step 7](poteto-workflow.md#7-resolve-unclear-problems-and-designs)

## What the talk adds

The talk reports the results on her team's agent app: 11,000 pull requests shipped last month, about 227 contributors in October, a stable release about once a day, and a revert rate steady at about 0.5%. Her pyramid orders where to spend time on the agent's environment, starting at the base. Only the first two layers are deterministic:

1. The code itself: API design, architecture, refactoring.
2. Lint rules, type systems, compilers and tests.
3. Runtime and formal verification.
4. Prose for what needs judgment: rules, skills and `AGENTS.md`.

- **Correct with code, not prose.** Each time you correct an agent, turn the correction into a deterministic check, or remove the problem with better API design. Agents copy workarounds, anti-patterns and deprecated code, because those look like the established pattern. → [Step 1](poteto-workflow.md#add-static-guardrails) and [step 6](poteto-workflow.md#6-keep-the-verifier-sharp)
- **Ban what needs nuance.** Her team bans `useEffect` in product code and allows it only inside its framework's APIs. Electron main-process and renderer code live in two top-level directories, and a dependency graph analyzer and lint rules forbid imports between them. Each ban is one less thing to catch in review. → [Step 1](poteto-workflow.md#add-static-guardrails)
- **Replace comments with lint errors.** Agents wrote comments to justify quick fixes such as imperative timers, and the timers spread. The team now bans about 99% of comments, and lint errors tell the agent to fix the root cause. → [Step 1](poteto-workflow.md#add-static-guardrails)
- **Block, then clean up.** "Start with a lint rule to prevent new occurrences of anti-patterns and then clean up those old patterns as well." → [Step 6](poteto-workflow.md#6-keep-the-verifier-sharp)
- **Review the artifacts.** Code review has shrunk to verification artifacts: videos, screenshots, diagrams and formal verification. Most of her tokens go to verification. The feature map gives you and the agent shared words, so "the thingy in the left sidebar" means one feature. → [Steps 2](poteto-workflow.md#2-create-the-verifier-and-its-cli) and [5](poteto-workflow.md#5-build-with-the-verifier)
- **Verify flows formally.** TLA+ model-checks user flows such as notifications across devices, and Lean proves an algorithm in a virtualization library. `/statechart` draws a flow as a state machine from the user's point of view, which she reviews next to videos and screenshots. Formal verification has already found bugs, but she is still experimenting with it and treats it as one more layer, not a guarantee. This stack does not install it.
- **Test UI properties.** [Bombadil](https://github.com/antithesishq/bombadil) runs property-based tests on UIs and has caught UI bugs for her team. This stack does not install it.
- **Foundations before factories.** Automating a loop that produces slop produces more slop. On each release her team runs an agent that fuzzes the app like a user and opens fix pull requests that merge automatically. That works because the codebase makes most pull requests good by default. This stack does not install that release agent.

## What this stack uses instead

| In the articles and talk | In this stack |
|---|---|
| `/poteto-mode` and its playbooks | The prompt names the skill, and [skill routing](skill-routing.md) helps you pick it |
| `/control-app` | The `/verify-<app>` skill you generate in step 2. It stays model-invocable so that agents load it through the step 4 `AGENTS.md` rule. Her example verifier is manual-only. |
| A CLI of drive commands | The same CLI, plus checks with expected results you approve (steps 2–3) |
| `.cursor/skills/verify-<app>/references/features/` | `.agents/skills/verify-<app>/features/` |
| Cursor cloud agents and `/swarm` | Local agents, each with its own checkout, ports, profile and data, kept apart by the verifier CLI; no cloud fan-out |
| `/architect` with a cross-model judge | `/codebase-design` (Design It Twice) plus prototypes |
| Multi-phase plan playbook | `/to-spec` or `/to-tickets` |
| Dr Eggbot, routines and automations | Not included. Step 6 says how to schedule runs yourself. |
| Gardening by hand | `/correct` turns a mistake made twice into a lint, type or check |
| Lint bans and a dependency graph analyzer | `/correct` adds each ban and import boundary with the repository's own tools. Step 1 covers the patterns you already know agents misuse, and step 6 turns each mistake made twice into a check. |
| A ban on about 99% of comments | Not adopted. `/correct` blocks disable comments on bans and proves the block, and it reads comments that justify a workaround as evidence of a mistake class. pstack's `/no-comments` needs Cursor-only agents. |

## Why the steps work this way

### Step 1: static checks run before the verifier

Lint rules, types and import boundaries fail a bad change on every run, before you or the verifier look at it. The verifier in step 2 then covers what they cannot express.

The first prompt turns on the checks the stack already ships and makes one command run them, locally and in CI. `/correct` then adds each ban that is specific to the repository, with the repository's own tools. It fixes the class at the highest level that works, from architecture down to a lint whose error names the replacement.

### Step 2: the CLI matters most

Every later step depends on the CLI. It holds deterministic commands, kept in the repository, that agents run instead of working out the steps each time. That saves time, context, and tokens. Its drive commands are single actions, such as click, fill, or press a key, and each feature recipe combines them. Its ports, profile, and data directory come from the checkout, and its doctor names the process holding its port or display and reports whether the build is current. The drive commands refuse to run against a stale build. With the CLI and the feature map, agents can already explore the app and prove their changes, before any check exists.

The debug tools in the inventory are the ones developers of that stack use by hand beyond logs, such as the Chrome DevTools Protocol, a simulator, a debugger, a profiler or a database's query plan.

The generated `SKILL.md` has CLI, launch, doctor, drive, debug, evidence, and cleanup sections. Each feature's recipe drives every variant the user docs promise for it, such as each documented shortcut, and the map names any variant, feature, or surface it leaves out.

### Step 3: a check replaces repeated verification

An agent trusts a check's answer instead of re-verifying the scenario in a loop. That trust is why you approve each check with a fresh agent first.

### Step 4: agents must not edit expected results

The second `AGENTS.md` rule is what makes a check worth trusting. An agent that can rewrite the expected result can make any check pass.

### Step 6: maintenance can change an expected result

Lauren runs `/maintain-verification-skill` daily. The skill knows nothing about checks, yet it may edit the verifier scripts that hold them, so it can change an expected result. The last sentence of the step 6 prompt and the `AGENTS.md` rule tell it not to, but nothing enforces them. That is why the guide tells you to read the diff.

The guide treats the verifier as product code, because every later step depends on its CLI.
