---
name: recall
description: "Manual only: reconstruct the user's recent working context from their own chat history, live state, and the shared record (user reports, prior fixes, incidents), then hand back a tight current-state brief. Run when the user asks: 'recall my work on X', 'catch me up', 'what have I been working on', 'where did I leave off'. Never mine transcripts on your own."
disable-model-invocation: true
---

# Recall

Manual skill. Run it when the user asks to be caught up, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of mining transcripts.

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on-topic. Read only what the in-scope threads need, then stop.

Your context lives in two records. Your own chat history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the symptoms users keep reporting, the fixes that shipped and got reverted, the errors still firing in prod. That second record is what the **why** skill searches, across source control, the issue tracker, chat and issue channels, long-form docs, and error tracking. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from your transcripts alone.

The durable memory bank is a different thing again. The `recall` and `reflect` memory tools return stored memories, not transcripts, and they have their own owner. Query them as one more source when they help, and keep the distinction straight in the brief: a remembered fact is not a reconstructed thread.

Transcripts are per workspace. Resolve the active workspace's session directory through the runtime rather than guessing its slug. OMP stores JSONL under `~/.omp/agent/sessions/<workspace-directory>/`, with named child transcripts beside each session. Hermes stores sessions under its active home's `sessions/` and indexes them in `state.db`. JSONL contains both metadata and message records; do not assume every line is a message.

1. Classify, then route. Resuming one specific prior chat is the runtime's own resume (`omp --resume`, `hermes --resume`), not this. Turning a habit into a durable skill is skill authoring, not this. A human-readable summary of your work is a different task. Recall loads working context across recent chats before you act. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days), the topic if named, and the workspace (default the active one. Never read another project's transcripts without being asked). State the scope back. Never quietly turn "all" into "recent N".
3. For one or two chats, search directly. Larger independent slices can use one OMP `task` batch with read-only `scout` agents, or Hermes delegation with an actual read/query-only grant. Without that grant, search in the parent; do not claim a prompt restriction is a sandbox. Order candidate paths by real modification time (OMP `glob` already does this), never UUID order. Search the topic first, then read only matching chats and relevant regions. Skip the current chat and obvious noise (subagent, eval and benchmark chats). Each slice returns one block per chat: topic, user goal, decisions, open threads, struggles and corrections, and artifacts (PRs, tickets, branches), citing the chat UUID.
4. Sweep the shared record whenever the topic names a feature, file, subsystem, area, or bug. This is the default, not a judgment call, and "my work on X" does not exempt it. Hand it to the **why** skill's source investigators, but steer their question from "why was this built this way" to "what's the current state, what's been tried and didn't hold, and what are users still reporting". Reuse its per-source playbooks, run the investigators in parallel with the chat-history mining, and inherit its posture: one investigator per source, null results are findings, skip an unavailable MCP and say so. Fold what comes back into the brief. Skip this step only for pure activity recall with no named target ("what did I do this week"), where your own history and live state are the entire answer.
5. Verify against live state. Take the PRs, branches, and tickets that the mining and the sweep surfaced and check them with `git` and `gh`. When the answer hinges on what an agent actually did (the tools it ran, files it read, errors it hit), read the full transcript, not just a trimmed local copy.
6. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Run the finished brief through the **unslop** skill as an explicit last pass, cite chat findings by UUID and shared-record findings by their source (PR #, ticket ID, chat permalink, error-tracker issue), and sanitize private context before any public output.

**Reply:** the brief, to the contract above.
