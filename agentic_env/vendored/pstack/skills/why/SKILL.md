---
name: why
description: "Manual only: use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Discovers available MCPs and queries each evidence category (source control, issue tracker, long-form docs, real-time chat, infrastructure observability, error tracking, product analytics warehouse) in parallel, then returns a cited read on decisions and tradeoffs. Use how for runtime behavior."
disable-model-invocation: true
---

# Why

Investigate the motivation and intent behind code. The companion `how` skill answers what the code does and how it works. `why` answers what forces led to its shape.

## Operating posture

Operate as a **careful, cautious, and precise investigator**. Be honest about what you know vs what you're inferring. Read `references/epistemics.md` for the full confidence framework and phrasing guide. The synthesizer must follow it.

`why` is an investigation. It reads code, history and the evidence sources the user has already authorized, and it writes nothing back to them. Read-only is a property of the tools each investigator is given, not of the sentence in its prompt telling it to behave. Give investigators read and query tools; withhold write, ticket-mutation, commit, push and publication tools. A prompt prohibition is guidance for judgment, never a permission boundary.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than spawning investigators; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that calls `why` by name, including `recall`'s source sweep, is a real invocation and proceeds normally.

## Step 1. Understand the Target and the Question

The **target** is usually a chunk of code, a pattern, a feature, or a named design decision. The **question** is usually a design rationale, a tradeoff, a motivating edge case, an external constraint, dead code, or a broad history sweep.

If the target is vague ("why do we do it this way?" with no clear referent), make your best guess from conversation context (open files, recent edits, what was just discussed). State your interpretation briefly so the user can redirect if you're off, then proceed.

## Step 2. Establish the Code Anchor

Before spawning investigators, build the seed context inline: file paths and line ranges, key symbols (functions, classes, constants), the last few commits touching the target, PR numbers from merge commits (pattern `(#1234)` in the subject line), and any linked ticket IDs. Run `git blame -L <start>,<end> <file>` for last-touch commits, `git log --follow -p -- <file>` for full history with patches through renames, `git log --oneline -20 -- <file>` for recent commits with PR numbers visible, and `git log -1 --format=%B <commit>` to extract PR numbers. Then pull the PR bodies and discussion for any substantive commit: `gh pr view <number> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews`. This anchor goes to every investigator and to the synthesizer.

## Step 3. Spawn Parallel Investigators

**Default to the full parallel investigation.** The goal is a complete coverage map, not a minimal one. Document the null, don't skip the search.

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

Spawn one investigator per category that has a matching authorized source, all in a single dispatch so they run concurrently, each owning exactly one tool or MCP. Don't ask one agent to cover multiple sources. Query only sources the user has already connected and authorized for this work; do not reach for a new account, credential or workspace to fill a category.

Subagent config (each):
- **OMP:** one item per category in a single `task` call. Use a read-only agent (`scout`) for source control and filesystem evidence. For an MCP-backed category, use an agent that can reach the MCP tools, granted query tools only. Investigators do not write files, mutate tickets, comment, commit or publish.
- **Hermes:** one `delegate_task` per category, all dispatched together, each given only the tools its source needs.
- **Model:** the runtime default unless the user names a model confirmed available here. Do not copy model aliases from another harness, and do not claim source diversity from dispatch count.

If a source cannot be delegated with an actual read/query-only grant, run its queries in the main thread and record that limitation. Do not mistake a tool list that adds capabilities for one that removes write access. Main-thread queries are read-only behavior, not a sandbox. A constrained search is not an unavailable source.

Each investigator's prompt is `references/investigator-prompt.md` filled in, plus:
- the category playbook `references/sources/<source>.md` for the selected MCP, adapted from the examples in `references/source-playbook.md`
- `references/sources/incident-postmortem.md` **if the target code looks defensive** (null checks, retry logic, timeout handling, rate limiting, feature flags, egress guards, OOM handlers)
- the code anchor and the user's original question

### Investigator roster, one per available evidence category

Each category below is uniquely positioned to surface one shape of "why", shown after "Best at". Use it to know what to expect back, to name a gap when a category returns empty, and, only in the rare provably-irrelevant case, to justify a skip.

1. **Source control** (git history, `gh` for PRs, code comments, tests). Always spawn, the only guaranteed source. Best at *implementation-time rationale captured during review*.
2. **Issue / ticket tracker** (e.g. Linear, Jira, GitHub Issues, Plane, Shortcut MCP). Best at *the product or business forcing function*. Strongest when the why is external to engineering.
3. **Long-form documents** (e.g. Notion, Confluence, Google Docs, Coda MCP). Best at *long-form design rationale*, written out before it becomes code.
4. **Real-time team chat** (e.g. Slack, Discord, Microsoft Teams, Mattermost MCP). Best at *real-time deliberation that never reached a doc*. Especially important when the source control, ticket, and doc paper trail is thin.
5. **Infrastructure observability** (e.g. Datadog, New Relic, Honeycomb, Grafana, Splunk MCP). Best at *infrastructure and runtime reality that motivated the code*. Strongest when the target reacts to an infra signal (timeouts, retries, rate limits, circuit breakers).
6. **Error / exception tracking** (e.g. Sentry, Rollbar, Bugsnag, Airbrake MCP). Best at *the specific exceptions and error trajectories that motivated defensive or corrective code*. Strongest for catch blocks, null guards, type checks, retries, and other defenses.
7. **Product analytics warehouse** (e.g. Databricks, Snowflake, BigQuery, ClickHouse, dbt, Redshift MCP). Best at *product and data reality that shaped the code*. Strongest for flag-gated code, experiment-driven ships, data migrations, and "where did this number come from" questions.

### When to skip an investigator

Only with an **explicit, written justification** that goes in the final Sources Consulted. Three valid reasons:

- **No authorized source is available for that category** in this environment: no MCP, or one that is configured but disabled or unauthenticated. Flag it as a gap, not a choice: "Real-time team chat skipped. No matching MCP available, so the conversational record was not searchable."
- **The source is provably irrelevant**, not just "probably irrelevant." A high bar: "Error / exception tracking skipped. Target is a build-time script with no runtime code path."
- **The ask sets an explicit scope.** The user, or a recipe they invoked such as `teach`'s narrow default, names the sources to search. Search those, and record each other category as "not searched: outside the requested scope". That line is a coverage limit, not a null result, and the Confidence Summary says the read comes from a scoped search.

If your scope assessment suggests a single-commit trivial target where the PR description already contains the complete answer, you may answer inline **only after** confirming every in-scope category search would be redundant: all seven available categories without an explicit scope, the requested ones with it. Categories outside an explicit scope still appear in Sources Consulted as coverage limits. Say so explicitly. This should be rare.

## Step 4. Synthesize

Synthesize inline using `references/synthesizer-prompt.md`. Delegate synthesis only when the findings are too large to handle clearly in the parent and a read/query-only agent is available.

Spot-verify citations using the same authorized sources. An unreachable citation is marked unverified, not dropped or asserted. A delegated synthesizer uses the runtime default model unless the user names a confirmed one.

The synthesizer gets:
1. The investigator findings, including any null results and any categories skipped with justification
2. The code anchor
3. The user's original question
4. The epistemics framework from `references/epistemics.md`
5. The synthesizer prompt template from `references/synthesizer-prompt.md`

## Step 5. Present

Present the synthesizer's output to the user. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.

## Output Format

The structure is the one in `references/synthesizer-prompt.md`: The Question, The Code in Question, What We Found, What We Can Reasonably Infer, Competing Hypotheses, What We Don't Know, Sources Consulted, Confidence Summary. Adapt as needed, but keep the confidence separation intact, and keep Sources Consulted as one line per investigator, including the ones that returned nothing or were skipped, with the reason.

After Sources Consulted, if the user's `why` question is a precursor to changing this code, convert the lineage findings into a Preserve / Change / Avoid / Risk constraint set for planning the change.

## Common Failure Modes to Avoid

- **Recency bias**. Assuming the most recent commit is authoritative. The current shape is often the accretion of many earlier decisions. Trace back.
- **Counting dispatch as coverage**. Seven subagents on one model over two reachable sources is two sources searched, not seven. Report what was searched, not how many agents ran.
- **Treating a prompt as a permission**. "Investigators shouldn't write" is a behavioral instruction. If an investigator holds write tools, the boundary is the tool grant, and the coverage map should say what access it actually had.

## Loading references

Load references through the runtime's own skill lookup (`skill://why/references/<file>` in OMP, `skill_view` in Hermes). Do not hard-code a checkout path. Sibling skills (`how`, `unslop`) are referenced by name and resolved the same way.
