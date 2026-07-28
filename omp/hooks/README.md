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
omp config set extensions '["/Users/mihai/.dotfiles/omp/hooks/verification-recorder.ts"]'
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
