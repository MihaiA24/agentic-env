---
name: how
description: "Manual only: use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

`how` is read-only by purpose. It reads, runs read-only searches, and explains. It does not edit, commit, or publish anything. If the explanation turns into a change request, stop and start the change as its own task under its own authorization.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than exploring; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that calls `how` by name is a real invocation and proceeds normally.

## Step 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): explain it yourself, inline. Read the code, then write the answer using the structure in `references/explainer-prompt.md`. No subagents.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview) **and genuinely separable**: the question splits into slices each of which can be traced without waiting on another slice's findings. Go to Step 2.

When in doubt, take the simple path. Fan-out that hands back what one read would have found costs more than it explains, and a slice that needs another slice's answer serializes anyway.

## Step 2. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct, independent slice of the subsystem. Dispatch them in one batch so they run concurrently, and give each explorer the prompt in `references/explorer-prompt.md` with its angle filled in.

Runtime:

- **OMP:** one item per angle in a single `task` call, on the read-only `scout` agent. Read-only is enforced by the agent type, not by the prompt.
- **Hermes:** one `delegate_task` per angle, dispatched together, each instructed to investigate only and given no write-capable tools.
- **Model:** use the runtime's default unless the user names a model you have confirmed exists here. Do not copy model aliases from another harness.
- If Hermes cannot enforce a read/query-only grant, investigate inline instead of calling a write-capable worker "read-only".

Explorers return findings, not prose. Go to Step 3.

## Step 3. Synthesize (complex questions only)

Merge the explorer findings into one explanation. Their slices overlap and can contradict; reconcile them and re-read the code yourself wherever they disagree.

Do this inline when the findings are small enough to hold. When they are not, delegate it to a single synthesizer (OMP `scout`, Hermes `delegate_task` without write tools) built from `references/explainer-prompt.md` with every explorer's findings filled in.

## Step 4. Present

Present the explanation to the user. If a subagent wrote it, light edits for clarity or conversation context are fine. Do not substantially rewrite it.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.

## Reference files

- `references/explorer-prompt.md`. Prompt template for one exploration angle.
- `references/explainer-prompt.md`. Prompt template and output structure for the explanation, with or without explorer findings.

Load references through the runtime's own skill lookup (`skill://how/references/<file>` in OMP, `skill_view` in Hermes). Do not hard-code a checkout path.
