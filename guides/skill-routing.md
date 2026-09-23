# Choose a skill for the job

Use this guide to choose a skill for a task, if one is needed. It follows [Decisions §6](../DECISIONS_AI_TOOLING.md#6-skills). For host setup and a project verifier, use [Start a new repo with the selected pstack skills](poteto-workflow.md). The implementation, prototype, and maintenance routes below use that verifier.

Choose the route your task needs. Skip the rest.

Invoke the skill in your prompt with your harness's syntax, listed in [Invoke skills in your harness](poteto-workflow.md#invoke-skills-in-your-harness). Pstack skills and Matt's `to-spec` and `to-tickets` are manual-only, so invoke them by name. Invoking a recipe authorizes its named dependencies. Reading a skill to check discovery does not invoke it.

## Find the route

| Situation | Route |
|---|---|
| A small change you already understand | Implement it directly and exercise the affected path |
| A report you cannot restate yet | A plain-English restatement before any fix |
| How the current code works | `/how` |
| Why the code has its current shape | `/why`, scoped to one target and question |
| You want the agent to explain its work and reasoning | `/teach` |
| You are resuming earlier work in this workspace | `/recall` |
| Goals, constraints, or choices only a person can make | `/grilling` |
| An unknown that an experiment can measure | `/prototype`, with the verifier |
| A new interface that callers will use | `/technical-writing` and `/codebase-design` |
| A consequential doubt that evidence supports | `/interrogate` |
| A settled design needs coordination across sessions or people | `/to-spec` or `/to-tickets` |
| Proof that a change works | The project verifier, on the affected paths |
| The verifier no longer matches the app | `/maintain-verification-skill`, on every mapped feature |

## Make small, understood changes directly

For a small change you already understand, implement it and exercise the affected user path with the project verifier. Show the evidence. Skip the planning document, interview, and critique.

## Restate an ambiguous report before fixing it

Ask the agent to explain an unclear report before proposing a fix:

```text
Read this report and restate the underlying problem in plain English.
Separate observations from assumptions. Do not prescribe a fix yet.
```

## Use explanation skills only for their own questions

Choose the skill that answers your question.

`/how` explains the current mechanism: what runs, where, and in what order.

```text
/how does [feature] handle [case]? Point to the relevant code and explain
it briefly. Do not change anything.
```

`/why` investigates why the code has its current shape. It searches broadly by default. For everyday use, specify one target, one question, and a source scope. The prompt below starts with Git history and project documents, widening only to authorized sources if the question remains open. It is read-only and reports unsearched or unreachable sources as coverage limits.

```text
/why does [module] [behavior]? Start with Git history and project documents.
Widen only to sources I have authorized, and list any evidence you could
not reach.
```

`/teach` explains how engineering work functions and why it was done that way. It uses `/how` and `/why`, separates evidence from inference, and states uncertainty. Diagrams use a format the session can render, such as Mermaid or plain text; image generation requires an available tool. It does not change code or create a course or learning workspace.

```text
/teach me why you implemented [change] this way and not [alternative].
What tradeoffs did you make, and which parts did you verify?
```

`/recall` reconstructs recent work from this workspace's session history and shared project record. Skip it when there is no relevant history.

```text
/recall my work on [topic] in this repository over the last 7 days.
Check the current state before recommending the next action.
```

## Settle human goals with grilling

Use `/grilling` to settle goals, constraints, or tradeoffs that require your choice before design begins. Use experiments for measurable questions rather than repeating interviews about an abstract plan.

## Measure unknowns with a prototype

Use a prototype to answer a measurable question about an interaction, state model, or layout:

```text
/prototype the unresolved [interaction or state-model question].
Use /[verifier] where applicable to exercise the result and capture evidence.
Compare the alternatives against the question. Stop before production
implementation so I can choose.
```

## Design a new interface from the caller's side

For a new module or API, describe how callers will use it before writing the implementation:

```text
Use /technical-writing to draft a short tutorial showing how a caller
would use [module]. Apply /unslop. Use /codebase-design to assess the
interface and its tradeoffs. Stop before implementation.
```

## Reserve interrogate for consequential uncertainty

`/interrogate` runs several models against one frozen snapshot and returns a report. Use it when a mistake would be expensive to undo and specific evidence still leaves doubt. Include that evidence in the prompt. Use `code-review` for routine review; do not interrogate an abstract plan.

## Plan durable work after the design settles

Use `/to-spec` or `/to-tickets` after the design settles, when work needs coordination across sessions or people. Each slice must name a live verification action and its expected result. Both skills end with publication. Require a separate approval before the agent publishes.

```text
/to-tickets for the settled [design]. In each ticket, name the /[verifier]
action and the observable result that proves it. Show me the tickets and
do not publish them until I approve.
```

## Verify affected paths, and maintain the whole map separately

For an ordinary change, verify the affected paths. Do not run full maintenance for every change.

Invoke `/maintain-verification-skill` separately. It checks the feature map against the source, exercises every mapped feature, fixes verifier drift, and reports product regressions separately. See [Keep the verifier useful](poteto-workflow.md#4-keep-the-verifier-useful) for the prompt.

## Methods this stack does not include

This stack excludes `/poteto-mode`, `/architect`, and `/swarm`. For planning, use the routes above rather than the articles' `/poteto-mode`. Local subagents do not replace `swarm` coverage.
