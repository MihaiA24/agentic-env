---
name: how
description: "Manual only: use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
disable-model-invocation: true
---

# How

Explore the codebase to answer "how does X work?" questions.

`how` is read-only by purpose. It reads, runs read-only searches, and explains. It does not edit, commit, or publish anything. If the explanation turns into a change request, stop and start the change as its own task under its own authorization.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than exploring; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that calls `how` by name is a real invocation and proceeds normally.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

For a narrow question (a single module, a small utility, "how does function X work"), read the code and write the explanation yourself, to the brief below. Otherwise spawn one read-only subagent that explores and explains in one pass. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

Runtime:

- **OMP:** one `task` item on `scout`. Check the actual tool grant, including inherited MCP and custom tools; when mutation must be impossible, use a restricted grant.
- **Hermes:** one `delegate_task`, instructed to investigate only and given no write-capable tools. If Hermes cannot enforce a read/query-only grant, explain inline instead of calling a write-capable worker "read-only".
- **Model:** use the runtime's default unless the user names a model you have confirmed exists here. Do not copy model aliases from another harness.

## 2. Present

Present the explanation. If a subagent wrote it, light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.
