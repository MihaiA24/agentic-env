---
name: apache-spark-runtime
description: Diagnoses existing Apache Spark jobs using live cluster metrics or completed-run artifacts. Use for observed latency, cost, skew, spill, memory pressure, or small-file problems when execution evidence is available.
---

# Apache Spark: runtime diagnosis and optimization

Diagnose an implemented SQL, DataFrame, or RDD job from live or completed executions. Rank work by the user's latency, throughput, or cost objective; a faster stage is not necessarily a faster or cheaper application.

## 1. Establish the baseline

Read available code, job configuration, and execution artifacts before requesting missing evidence. Collect only authorized artifacts; keep raw logs private and redact credentials, query literals, and personal data before model ingestion or external sharing. Record:

- Exact Spark/runtime version, language/API, batch versus streaming, deployment mode, relevant connectors/table formats, and code revision.
- Entry point and production action/sink; input snapshot, bytes/rows, file layout, join-key distribution, output contract, and resource constraints.
- A representative application ID/attempt, running/completed status, observation timestamps, SQL execution IDs when applicable, elapsed intervals, effective configuration, executor allocation, and available UI/history/event logs.
- The objective and acceptable correctness, latency, and cost boundaries. Separate queue/startup time from execution, without excluding them from an end-to-end objective.

Event logs exist only if enabled before the run; enabling them now cannot recover a past run. **Gate:** identify the representative execution and evidence gaps. Without accessible live or completed-run evidence, route code/plan review to `apache-spark-static` and supply an authorized collection procedure; do not claim a measured bottleneck or gain.

## 2. Locate the critical path

Trace the production action through SQL execution → jobs → stages → task attempts. For RDD jobs, start from the action and stage DAG. Account for overlapping jobs, retries, speculation, executor loss, and changing allocation.

For live jobs, use timestamped stage/task/executor snapshots and available progress, stating the observation window and incomplete task populations. Treat current plans, elapsed duration, and projected cost as provisional; final-plan and end-to-end conclusions require completion of the actual action. For streaming, use query/run IDs, offsets/lag, progress, state/watermark, and sink evidence; preserve production checkpoints and require a connector-aware replay/recovery plan.

For each expensive critical-path stage/operator, relate task-duration distribution to input/shuffle bytes, records, spill, GC, fetch wait, and available concurrency. Inspect scan pruning, exchanges, join build side, sorts/windows, Python boundaries, and repeated computation. For completed actions, compare initial and final AQE plans from the same execution; a live current or pre-action EXPLAIN is not proof of the completed plan.

**Gate:** each ranked bottleneck has a run/stage/operator locator, supporting measurements, an alternative explanation, and confidence. Distinguish observed facts from hypotheses; aggregate task time is not application wall time.

### Conditional examples

| Observation | Risk of misdiagnosis | Supported next step | Proof needed |
|---|---|---|---|
| A few slow tasks | A long tail alone does not prove key skew or justify salting. | Compare bytes/records and executor placement with fetch stalls, contention, and recovery; confirm key/partition imbalance before choosing a skew remedy. | Timestamped, attempt-aware distributions, complete after the action finishes; compare processing time against work, not duration alone. |
| Spill, GC, or OOM | These signals do not identify the same failure or memory domain. | Locate the operator and affected driver, executor JVM, Python, or native memory domain; reduce its working set or derive configuration from measurements. | Failure details, heap/process limits, relevant spill/GC/operator metrics, and an isolated rerun of the actual action. |
| Less spill or a faster stage | Intermediate metrics can improve while sink commit, end-to-end latency, or cost worsens. | Keep the change only if correctness and repeated completed action/sink measurements meet the objective and resource boundaries. | End-to-end latency including commit, allocated/billed resources, variability, and output equivalence; explicitly accept any tradeoff. |

## 3. Choose the smallest supported intervention

Prefer reducing unnecessary data and work before hints, configuration, or more hardware. Check the existing physical plan first: Catalyst or AQE may already perform the proposed optimization. Use the exact runtime's Apache documentation, and provider documentation for provider-specific features.

For each candidate, specify the code/config delta and its scope, causal hypothesis, expected plan/metric change, semantic risk, resource/cost tradeoff, and rollback. Then:

- Make each independent change its own experiment with its own predicted metric, including dead-work removal; queue the rest instead of bundling them.
- Derive every configuration value from a named measurement (partition bytes, built relation size, failed memory domain); when that measurement is missing, name it instead of proposing a number.
- Set deployment settings at submission/startup and SQL settings in the relevant session.

**Gate:** provide a ranked experiment plan; implement the leading candidate only when the request authorizes edits. An analysis-only request stops at the plan. Access to production does not authorize expensive reruns, catalog or table-layout changes, compaction, destructive writes, or cluster-wide changes.

## 4. Prove correctness and improvement

Run the actual action/sink in an authorized isolated destination; a lazy transformation or substituted count does not prove the production path improved.

Check schema/types and row multiset equivalence, including duplicate and null behavior; test relevant join, aggregation, window, ordering, floating-point, and nondeterministic edge cases. Preserve sink mode, partition layout, checkpoint/state, and downstream contracts. Keep correctness-check execution outside timed runs.

Compare repeat runs on the same input snapshot, runtime, resources, relevant configuration, and cache policy. Report variability and both end-to-end time and resource/cost evidence. Verify the predicted physical-plan/metric change, not just elapsed time. Reject regressions or explain an explicitly accepted tradeoff; keep the prior revision/config as rollback.

**Gate:** mark the result `measured improvement`, `no improvement`, `regression`, or `unverified`. Live diagnosis does not prove improvement. Without a real comparable rerun, deliver the reachable analysis/change and name the missing prerequisite; never invent speedup or savings.

## Deliverable

1. **Baseline:** job/run locator, status/observation window, objective, input/resources/runtime, and evidence coverage.
2. **Findings:** ranked `locator | observation | hypothesis | alternative | confidence` rows.
3. **Change:** exact delta, expected effect, semantic/resource risks, and rollback.
4. **Proof:** `metric | baseline | candidate | variability`; output checks and artifacts, or the exact missing evidence and next command/action.
5. **Decision:** keep/reject the candidate against the objective; identify the next experiment only if evidence warrants one.
