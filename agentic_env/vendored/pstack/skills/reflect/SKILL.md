---
name: reflect
description: "Manual only: review the current session's transcript through three lenses, surface durable learnings, and route each to a concrete edit on an existing skill. Run when the user says reflect or /reflect. Never start a reflection on your own."
disable-model-invocation: true
---

# Reflect

Manual skill. Run it when the user says reflect, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of reading transcripts.

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

Use the runtime's current-session handle or transcript path; never choose a chat merely because it is newest. In OMP, known same-run agent IDs can be read through `history://<id>`; filesystem transcripts live under `~/.omp/agent/sessions/<workspace-directory>/`, with child transcripts in the matching session directory. In Hermes, use the current session ID to locate its record under the active Hermes home's `sessions/` or `state.db`.

Read only this session and its named children. Session headers contain metadata, not necessarily the opening user prompt; establish the session identity before reading message records. Do not sample other chats to find a match. If the runtime does not expose an unambiguous current transcript, pass a tight digest of this conversation instead.

### 2. Run three reviewers in parallel

Three lenses, one dispatch. In OMP use one `task` batch with read-only `scout` agents; in Hermes delegate only if the granted tools can actually exclude writes. Reviewers may query already-authorized sources cited in this session. If a restricted grant is unavailable, the parent gathers that evidence and supplies it to tool-less reviewers. A prohibition in the prompt is not a permission boundary.

| Lens | Prompt template |
|---|---|
| Judgment | `references/judgment-reviewer.md` |
| Tooling | `references/tooling-reviewer.md` |
| Divergent | `references/divergent-reviewer.md` |

Load each template from the skill's own directory (`skill://reflect/references/<file>` in OMP, `skill_view` in Hermes) and pass it verbatim, substituting the transcript path or digest where marked.

Subagents of one session run on the models that session is configured with, so three lenses are not three model families. If you want real model diversity, resolve exact selectors with `omp models --json` and run the same three prompts as separate processes instead — `omp --model <exact-selector> -p --mode json --no-tools --no-skills --no-rules --no-extensions --no-session "<template + transcript digest>"`, or `hermes -z "<prompt>" --provider <provider> -m <model> -t '' --ignore-rules --usage-file <path>` — reading the provider and model back out of each run's own output. That route trades the lookups for distinct models, because those flags leave the reviewer no tools. Pick one route, and name it in the summary. Never report same-model lenses as a multi-model review.

### 3. Synthesize

Synthesize inline using `references/synthesizer.md`, with every reviewer's full output. Spot-verify citations using authorized sources, marking unreachable ones unverified. Delegate only when the volume justifies it and a read/query-only grant is available. Preserve the structured Accepted / Rejected / Backlog result.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, test, or doctor check, move it from Accepted to Backlog. Prose asks every future agent to remember; a mechanism just fails.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent on this machine. Do not auto-apply.

Nothing files itself. Backlog items are reported to the user, not written to a tracker, and creating an issue, a branch, a commit or a PR is a separate ask each time. Reflection produces edits in the working tree and a list; publication is the user's call.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): write it through the `writing-for-agents` skill, which owns how agent-facing instructions are shaped, and keep the target skill's existing structure and vocabulary.
- `tune description: <skill path>`: the skill exists but didn't trigger when it should have. Rewrite the description around the triggers that were missed, again through `writing-for-agents`, and change nothing else in the body.
- `new skill: <kebab-name>`: only when no existing skill is a real home. Draft it through `writing-for-agents` and follow the conventions of the skills already installed here. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog reported for the user to file: `<item>`. One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
