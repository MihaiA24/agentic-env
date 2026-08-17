# OMP hooks

## verification-recorder

Records verification outcomes (test / lint / typecheck / build) from OMP sessions into
`~/.omp/agent/verification_evidence.db`.

### Why

Hermes keeps a quality feedback loop — `~/.hermes/verification_evidence.db` held 248 events at a
83.9% pass rate, plus structured per-patch outcomes giving a measurable 12.9% patch failure rate.
OMP records none of this: tool output spills to per-call logs (`*.bash.log`) with no outcome, so
across 152 sessions no pass rate, edit-failure rate, or regression signal can be computed.

That gap is not just a reporting inconvenience. It blocks the paired harness benchmark described in
`AI_CONTEXT_TOOLING_COMPARISON.md` under "Open for grilling": one arm would be measured and the
other unmeasurable. This hook is the prerequisite.

The schema deliberately mirrors Hermes' so the two harnesses are directly comparable.

### Install

```bash
omp config set extensions '["/Users/mihai/.dotfiles/omp/hooks/verification-recorder.ts","/Users/mihai/.dotfiles/omp/hooks/cadence-governor.ts","/Users/mihai/.dotfiles/omp/hooks/retention-canary.ts"]'
```

Verify:

```bash
omp config get extensions
```

Arrays replace rather than append — include every extension you want when setting this.

### Behaviour

- Listens on `tool_result` for `bash` and `eval`.
- Records only verification-shaped commands. `git status`, `ls`, `cat` and friends are ignored, so
  the store stays a quality signal rather than a shell log.
- Exit code comes from OMP's `Command exited with code N` line, falling back to the `isError` flag.
- Failures inside the hook are swallowed: instrumentation must never break a tool result.

### Query it

```bash
sqlite3 ~/.omp/agent/verification_evidence.db \
  "select kind, status, count(*) from verification_events group by 1,2 order by 3 desc;"

# Pass rate, comparable to Hermes' 83.9%
sqlite3 ~/.omp/agent/verification_evidence.db \
  "select round(100.0*sum(status='passed')/count(*),1) || '%' from verification_events;"
```

### Test

```bash
bun test omp/hooks/verification-recorder.test.ts
```

The test exercises the real `handleToolResult` path and the default-export hook registration against
the actual database, then deletes only the rows it wrote.

## retention-canary

Warns in-session when Mnemopi silently stops retaining for the current project.

### Why

The dotfiles bank took zero retains 07-19→08-10 while 11 sibling banks retained fine on the same
days and omp versions — project-local, no errors, self-healed (forensics in
`agentic-env/docs/memory-backend-research.md`). Nothing inside the pipeline reports retention
death, so external detection is the only defense (`DECISIONS_AI_TOOLING.md`, Memory bullets).

### Behaviour

- Runs once per session, on the first `tool_result` (no `session_start` event exists).
- Compares the project bank's newest row (`max(created_at)` over `working_memory ∪
  episodic_memory ∪ facts` — union because consolidation prunes working rows) against sibling
  session jsonl mtimes, current session excluded.
- Fires when the newest prior session is ≥7 days newer than the newest memory row AND ≥2
  sessions ran since. Replayed against the real gap it fires 07-26 instead of 08-11.
- Bank lookup is by slug (cwd basename, leading dots stripped) — the bank-id hash suffix is not
  derivable from the compiled omp binary. Basename collisions check every matching bank; a rare
  false warn on a sibling project is acceptable for a tripwire.
- Failures inside the hook are swallowed; it never breaks a tool result.

### Test

```bash
bun test omp/hooks/retention-canary.test.ts
```

Smoke-tested 08-18 against the live dotfiles bank (quiet) and the `agentic-env` bank stale since
06-29 (fires: "49 days before the latest session, 17 sessions ran since").
