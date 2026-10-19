---
name: apache-spark-static
description: Reviews Apache Spark code and initial plans without execution evidence. Use for pre-run review or code-level correctness and performance risks, with known, estimated, or unknown input volume.
---

# Apache Spark: static review

Review an implemented SQL, DataFrame, or RDD job without executing the workload. Separate code/plan facts from scale-dependent hypotheses; static review cannot establish a runtime bottleneck or speedup. For diagnosis using live metrics or completed-run artifacts, use `apache-spark-runtime` instead.

## 1. Establish the contract and scale

Read available code, schemas, configuration, input metadata, and initial plans before requesting missing context. Use only authorized artifacts; keep raw logs private and redact credentials, query literals, and personal data before model ingestion or external sharing. Record:

- Entry point, production action/sink, code revision, exact Spark/runtime version, language/API, batch versus streaming, and connectors/table formats.
- Required schema/types, duplicate/null/numeric behavior, joins, ordering/windows, partition layout, nondeterminism, and external side effects.
- Input bytes/rows, file layout, row widths, key distribution, and projected join sizes when available. Label each scale fact measured, estimated, or unknown, with its source and assumptions.

**Gate:** unknown input volume does not block code-level review. Make scale-dependent findings conditional; do not launch scans, count/collect, statistics refreshes, or cluster jobs just to fill evidence gaps.

## 2. Trace the action and inspect the plan

Follow input → transformations → actual action/sink. Locate unnecessary reads/columns, ineffective pruning, exchanges, join build sides and cardinality, sorts/windows, Python boundaries, repeated computation, caching, driver collection, and execution partitioning versus writer layout. Check whether Catalyst or AQE already handles the proposed optimization; rewriting syntax alone is not a gain.

Separate definite correctness defects from performance risks. Preserve duplicate/null join behavior, window groups/ties, and state/checkpoint/sink contracts. An initial EXPLAIN is not the executed final AQE plan; source-file size is not built-relation size or a broadcast/memory safety proof. Use the exact runtime's Apache documentation and provider documentation for provider-specific behavior.

**Gate:** every finding has a code/plan locator, supporting fact, semantic or performance risk, scale condition, and confidence. Unknown cardinality or distribution stays unknown, not an invented skew diagnosis.

### Conditional examples

| Pattern | Risk | Safe candidate and condition | Validation |
|---|---|---|---|
| Python UDF with a native equivalent | Python evaluation boundary; a rewrite may change semantics. | Replace only when types, nulls, exceptions, and Unicode/numeric behavior match. | Bounded edge fixtures and the expected removal of the Python operator; runtime benefit remains unverified. |
| `collect()` on an unbounded result | Expanded output may exceed driver capacity. | Reduce or remove collection only if the return/side-effect contract permits it; a required full list retains the scale limit. | Check the return contract; require expanded-result and driver bounds before claiming collection is safe. |
| Deduplicating a join input to reduce work | Changed row multiplicity. | Retain duplicates unless the output contract permits deduplication and the resulting join multiplicity is verified. | Duplicate/null fixtures and row-multiset comparison, not distinct sets or row counts. |

## 3. Propose the smallest safe change

Rank findings against the user's objective. Prefer removing unnecessary data/work before hints, configuration, or hardware. State the exact delta, expected plan/work change, semantic/resource risk, and rollback. Do not prescribe broadcast, cache, memory, or partition values without relevant bounded evidence; estimates are assumptions, not safety proofs.

Implement only authorized edits; analysis-only requests stop at recommendations. Data access, cluster execution, catalog/table-layout changes, compaction, production writes, and checkpoint changes require separate authorization. For streaming, preserve offsets/state/watermarks and require a connector-aware replay/recovery plan before any experiment.

Validate authorized edits with existing isolated small-fixture checks when available, covering schema, row multiplicity, nulls, numeric policy, ordering/windows, and sink contracts. Otherwise state the missing correctness prerequisite. Specify runtime validation using the real action/sink, immutable inputs, isolated output, one change per experiment, comparable repeated runs, and output equivalence; do not claim improvement before that evidence exists.

**Gate:** deliver actionable static findings and a validation plan even when volume or cluster access is unavailable. Label performance effects unverified; runtime analysis is an evidence-driven next step, not a mandatory prerequisite to static review.

## Deliverable

1. **Scope:** job/action, objective, output contract, runtime, and measured/estimated/unknown scale facts.
2. **Findings:** ranked `locator | fact | risk | scale condition | confidence` rows.
3. **Change:** minimal proposed or authorized delta, semantic/resource risks, and rollback.
4. **Validation:** correctness checks performed or missing, predicted plan/work effect, and exact evidence needed for runtime verification. No measured speedup or savings claim.
