---
name: why
description: "Manual only: use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Discovers available MCPs and queries each evidence category (source control, issue tracker, long-form docs, real-time chat, infrastructure observability, error tracking, product analytics warehouse) in parallel, then returns a cited read on decisions and tradeoffs. Use how for runtime behavior."
disable-model-invocation: true
---

# Why

Investigate the motivation and intent behind code.

Companion to the `how` skill. `how` answers what the code does and how it works. `why` answers what forces led to its shape.

## Operating posture

Operate as a **careful, cautious, and precise investigator**. Be honest about what you know vs what you're inferring. Read `references/epistemics.md` for the full confidence framework and phrasing guide. The synthesizer must follow it.

`why` is an investigation. It reads code, history and the evidence sources the user has already authorized, and it writes nothing back to them. Read-only is a property of the tools each investigator is given, not of the sentence in its prompt telling it to behave. Give investigators read and query tools; withhold write, ticket-mutation, commit, push and publication tools. A prompt prohibition is guidance for judgment, never a permission boundary.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than spawning investigators; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that calls `why` by name, including `recall`'s source sweep, is a real invocation and proceeds normally.

## Step 1. Understand the Target and the Question

Parse what the user is asking. The **target** is usually a chunk of code, a pattern, a feature, or a named design decision. The **question** is usually a design rationale, a tradeoff, a motivating edge case, an external constraint, dead code, or a broad history sweep.

If the target is vague ("why do we do it this way?" with no clear referent), make your best guess from conversation context (open files, recent edits, what was just discussed). State your interpretation briefly so the user can redirect if you're off, then proceed.

## Step 2. Establish the Code Anchor

Before spawning investigators, anchor the investigation in concrete code. You need:

- The relevant file path(s) and line range(s)
- The key symbols (function names, class names, constants)
- An initial commit list. The last few commits touching the target.
- PR numbers from merge commits (pattern `(#1234)` in the subject line)

Build this inline.

```bash
# Blame target lines for last-touch commits
git blame -L <start>,<end> <file>

# Full file history, with patches, through renames
git log --follow -p -- <file>

# Last N commits touching the file, PR numbers visible
git log --oneline -20 -- <file>

# Extract PR numbers from a commit message
git log -1 --format=%B <commit>
```

Pull PR bodies and discussion via `gh` for any substantive commits:

```bash
gh pr view <number> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews
```

Capture this as seed context (file paths, symbols, commits, PR numbers, linked ticket IDs). Pass it to the investigators.

## Step 3. Spawn Parallel Investigators (default posture)

**Default to the full parallel investigation.**

### Discovery

Before spawning investigators, list the evidence sources actually available and authorized in this runtime. Use the active tool inventory, server status and exposed resource metadata (`mcp://` in OMP); disabled, gated or unauthenticated sources are unavailable. Do not open credential-bearing configuration just to inventory server names, and never assume a source is reachable because its playbook exists here.

Map each available MCP to one evidence category:

1. Source control history
2. Issue / ticket tracker
3. Long-form documents
4. Real-time team chat
5. Infrastructure observability
6. Error / exception tracking
7. Product analytics warehouse

Check source-control access through git and the available forge tools; do not assume `gh` is installed or authenticated. For the other six, classify using the MCP name, server instructions, tool names, and resource descriptors. If an MCP could fit more than one category, choose the one matching its primary evidence. Record ambiguous cases in the coverage map.

Aim for a complete **coverage map**, not a minimal one. Document the null, don't skip the search.

Launch all matching investigators in a single dispatch so they run concurrently. Don't ask one agent to cover multiple sources.

Subagent config (each):
- **OMP:** one item per category in a single `task` call. Use a read-only agent (`scout`) for source control and filesystem evidence. For an MCP-backed category, use an agent that can reach the MCP tools, granted query tools only. Investigators do not write files, mutate tickets, comment, commit or publish.
- **Hermes:** one `delegate_task` per category, all dispatched together, each given only the tools its source needs.
- **Model:** the runtime default unless the user names a model confirmed available here. Do not copy model aliases from another harness, and do not claim source diversity from dispatch count.

If a source cannot be delegated with an actual read/query-only grant, run its queries in the main thread and record that limitation. Do not mistake a tool list that adds capabilities for one that removes write access. Main-thread queries are read-only behavior, not a sandbox. A constrained search is not an unavailable source.

Each investigator gets:
1. The base prompt from `references/investigator-prompt.md`
2. The category playbook `references/sources/<source>.md` for the selected MCP, adapted from the examples in `references/source-playbook.md`
3. The cross-cutting `references/sources/incident-postmortem.md` **if the target code looks defensive** (null checks, retry logic, timeout handling, rate limiting, feature flags, egress guards, OOM handlers)
4. The code anchor from Step 2 (file paths, symbols, commit hashes, PR numbers, ticket IDs)
5. The user's original question

### Investigator roster. One per available evidence category

Spawn one investigator per category that has a matching authorized source. Each owns exactly one tool or MCP. Query only sources the user has already connected and authorized for this work; do not reach for a new account, credential or workspace to fill a category.

Each entry names the category and the kind of "why" it uniquely surfaces. Use it to know what to expect back, how to name a gap when a category returns empty, and (only in the rare provably-irrelevant case) to justify a skip.

1. **Source control investigator**. Git history, `gh` for PRs, code comments, tests. Always spawn. The only guaranteed source. Best at surfacing *implementation-time rationale captured during review*.

2. **Issue / ticket tracker investigator** (e.g. Linear, Jira, GitHub Issues, Plane, Shortcut MCP). Best at surfacing *the product or business forcing function*. Strongest when the why is external to engineering.

3. **Long-form documents investigator** (e.g. Notion, Confluence, Google Docs, Coda MCP). Best at surfacing *long-form design rationale*. Where the why is written out before it becomes code.

4. **Real-time team chat investigator** (e.g. Slack, Discord, Microsoft Teams, Mattermost MCP). Best at surfacing *real-time deliberation that never reached a doc*. Especially important when the source control, ticket, and doc paper trail is thin.

5. **Infrastructure observability investigator** (e.g. Datadog, New Relic, Honeycomb, Grafana, Splunk MCP). Infra/runtime view. Best at surfacing *infrastructure and runtime reality that motivated the code*. Strongest when the target reacts to an infra signal (timeouts, retries, rate limits, circuit breakers).

6. **Error / exception tracking investigator** (e.g. Sentry, Rollbar, Bugsnag, Airbrake MCP). Best at surfacing *the specific exceptions and error trajectories that motivated defensive or corrective code*. Strongest for catch blocks, null guards, type checks, retries, and other defenses.

7. **Product analytics warehouse investigator** (e.g. Databricks, Snowflake, BigQuery, ClickHouse, dbt, Redshift MCP). Product/data view. Best at surfacing *product and data reality that shaped the code*. Strongest for flag-gated code, experiment-driven ships, data migrations, and "where did this number come from" questions.

### When to skip an investigator

Only skip with an **explicit, written justification** that goes in the final "Sources Consulted" section. Three valid reasons:

- **No authorized source is available for that category** in this environment: no MCP, or one that is configured but disabled or unauthenticated. Flag this as a gap, not a choice. Example: "Real-time team chat skipped. No matching MCP available, so the conversational record was not searchable."
- **The source is provably irrelevant**, not just "probably irrelevant." A high bar. Example: "Error / exception tracking skipped. Target is a build-time script with no runtime code path."
- **The ask sets an explicit scope.** The user, or a recipe they invoked such as `teach`'s narrow default, names the sources to search. Search those, and record each other category as "not searched: outside the requested scope". That line is a coverage limit, not a null result, and the Confidence Summary says the read comes from a scoped search.

If your scope assessment suggests a single-commit trivial target where the PR description already contains the complete answer, you may answer inline **only after** confirming every in-scope category search would be redundant: all seven available categories without an explicit scope, the requested ones with it. Categories outside an explicit scope still appear in Sources Consulted as coverage limits. Say so explicitly. This should be rare.

## Step 4. Synthesize

Synthesize inline using `references/synthesizer-prompt.md`. Delegate synthesis only when the findings are too large to handle clearly in the parent and a read/query-only agent is available.

Spot-verify citations using the same authorized sources. An unreachable citation is marked unverified, not dropped or asserted. A delegated synthesizer uses the runtime default model unless the user names a confirmed one.

The synthesizer gets:
1. The investigator findings, including any null results and any categories skipped with justification
2. The code anchor from Step 2 (file paths, symbols, commit hashes, PR numbers, ticket IDs)
3. The user's original question
4. The epistemics framework from `references/epistemics.md`
5. The synthesizer prompt template from `references/synthesizer-prompt.md`

## Step 5. Present

Take the synthesizer's output and present it to the user. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.

## Output Format

The output structure is the one in `references/synthesizer-prompt.md`: The Question, The Code in Question, What We Found, What We Can Reasonably Infer, Competing Hypotheses, What We Don't Know, Sources Consulted, Confidence Summary. Adapt as needed, but keep the confidence separation intact, and keep Sources Consulted as one line per investigator, including the ones that returned nothing or were skipped, with the reason.

After the Sources Consulted block, if the user's `why` question is a precursor to actually changing this code, convert the lineage findings into a Preserve / Change / Avoid / Risk constraint set suitable for planning the change.

## Common Failure Modes to Avoid

- **Recency bias**. Assuming the most recent commit is authoritative. The current shape is often the accretion of many earlier decisions. Trace back.
- **Counting dispatch as coverage**. Seven subagents on one model over two reachable sources is two sources searched, not seven. Report what was searched, not how many agents ran.
- **Treating a prompt as a permission**. "Investigators shouldn't write" is a behavioral instruction. If an investigator holds write tools, the boundary is the tool grant, and the coverage map should say what access it actually had.

## Reference Files

- `references/epistemics.md`. Confidence tiers and phrasing guide. The synthesizer must follow it.
- `references/investigator-prompt.md`. Base prompt template for investigator subagents.
- `references/source-playbook.md`. Index pointing at the category playbooks below.
- `references/sources/*.md`. One self-contained example playbook per category, plus cross-cutting `incident-postmortem.md`. Give an investigator the single file that matches its category and adapt it to the available MCP.
- `references/synthesizer-prompt.md`. Prompt template for the synthesizer subagent, including the output format.

Load references through the runtime's own skill lookup (`skill://why/references/<file>` in OMP, `skill_view` in Hermes). Do not hard-code a checkout path. Sibling skills (`how`, `unslop`) are referenced by name and resolved the same way.
