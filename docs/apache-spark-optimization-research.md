# Apache Spark skills: research and design

## Deliverable and review status

The implementation has two independent, single-file skills: [`apache-spark-static`](../agentic_env/skills/apache-spark-static/SKILL.md) reviews existing code/initial plans with known, estimated, or unknown input volume; [`apache-spark-runtime`](../agentic_env/skills/apache-spark-runtime/SKILL.md) diagnoses live or completed cluster executions and verifies targeted optimizations. This document keeps detailed findings and citations for maintainers; neither skill loads a reference bundle or requires the other as a first step. No representative user Spark job or benchmark was supplied or executed.

## Design decisions

- **Evidence before tuning:** static findings are code/plan facts and conditional risks, not measured bottlenecks. Runtime findings use attempt-aware live observations or completed action-specific plans/metrics; live plans, populations, latency, and projected cost remain provisional. Missing history requires a safe collection procedure, not invented measurements.
- **Optimize the objective:** critical-path end-to-end latency and allocated/billed resources are distinct from summed task time, fewer exchanges, or zero spill.
- **Correctness is a gate:** retain duplicate/null/numeric/window and sink/layout semantics; use distributed multiset comparison for supported deterministic outputs, with contract-specific alternatives otherwise.
- **Small causal experiments:** reduce data/work first, then justified plan/config/resource changes; exact runtime and deployment scope control applicability. No universal partition, broadcast, heap, or file-size prescriptions.
- **Portable baseline:** no vendor engine, new dependency, log parser, automatic production rerun, or fabricated cost model. Existing UI/History Server/REST evidence is sufficient for the skill's workflow.
- **Streaming boundary:** detect state/checkpoint/offset semantics before applying batch recipes; require an isolated connector-aware replay plan.
- **Packaging:** two first-party packages in the opt-in `agentic-env` pack at `agentic_env/skills`; the unsplit package is removed with no alias or router. Existing default/minimal/agentic-only profiles remain unchanged. Python-only copying includes both packages; wheel artifacts include them.
- **Invocation:** both model-invoked on distinct evidence triggers. Original unsplit probes scored 6/36 without the process and 31/36 with it; those scores are historical, not an evaluation of the split. The current cost is two narrow always-loaded descriptions.
- **Fingerprint status:** both reviewed packages are recorded in `skill-fingerprints.json`. Source-only checks use `--pack agentic-env --no-installed`; upstream comparisons are automatically skipped because this first-party pack has no third-party upstream.

## Research method and evidence limits

Two independent primary-source passes investigated execution interventions and completed-run diagnostics/verification. Official Apache documentation and tagged source were inspected across 3.5.x, 4.0.1, and selected 4.1.3 Python behavior. The pinned versions below are evidence anchors, not upgrade recommendations or claims about the newest release. Apply the actual job's matching documentation.

The sections retain their fact/recommendation distinction and full source ledgers. Code/REST examples are source-checked templates, not executed deployment requests. Synthetic fixture numbers only exercise reasoning and do not establish a real performance gain.

## Pre-split implementation smoke evidence

- Affected existing suites: `tests/test_copy_skills.py`, `tests/test_install_skills_mcps.py`, `tests/test_stack_metadata.py`, and `tests/test_skill_drift.py` pass with the package installed through the Python-only copier, the native custom-directory route, and an offline-built wheel.
- Source-only first-party drift inspection reported `source: new` until the content review recorded the baseline.
- These are package and skill-decision checks, not real Spark execution, endpoint connectivity, harness auto-discovery, correctness proof for a user job, or performance measurements.

## Original single-file reference ablation

Before the static/runtime split, the first version shipped three reference files (diagnostics, optimization, verification; ~4,400 words). Stateless model runs compared no skill, the main file only, the full package, and a minimal main file with four sharpened rules and no references.

| Variant | Words loaded | Open-request process score |
|---|---:|---:|
| No skill | 0 | 6/36 |
| Main file only | 788 | 28/36 |
| Full package with references | 5,219 | 31/36 |
| Minimal single file (pre-split) | ~790 | 31/36 |

The score covers six behaviors on two open optimization requests (three runs each): runtime evidence before fixes, no unanchored configuration values, one change per experiment, output-equivalence checks, comparable before/after measurement, and flagging result-changing changes. On eight prompts that named a specific Spark trap (metric units, Arrow configuration scope, window salting, multiset comparison, checkpoint safety, AQE skew, final versus initial plan, missing telemetry), the base model passed all 16 runs without the skill: the reference facts were already default knowledge. The minimal file also passed the missing-telemetry, streaming and window-skew safety cases.

The four sharpened rules: event logs cannot be recovered retroactively; each independent change, including dead-work removal, is its own experiment; every configuration value derives from a named measurement; reference pointers removed. Limits: one model, two or three runs per variant, a low-cost grader. Directional evidence, not proof across models or harnesses.

## Content review probes

The reviewed revision added `alternative` to the Deliverable findings row to match step 2's gate, turned step 3's experiment and configuration rules into bullets, folded table-layout authorization into the step 3 gate, cut the description to symptoms, and moved example invocations to the README. Stateless runs compared the shipped and revised files on four hypothetical requests: driver-dominated wall time, a regressed EMR run without exports, a lagging stateful stream, and an authorized multi-symptom optimization.

| Check | Shipped | Revised |
|---|---:|---:|
| Findings carry an alternative explanation | 8/12 | 12/12 |
| One experiment per independent change | 3/3 | 3/3 |
| Output multiset/schema equivalence | 3/3 | 3/3 |
| Repeated comparable before/after runs | 3/3 | 3/3 |
| Unanchored configuration or size value | 1/3 | 1/3 |

On the revised file, analysis-only requests stopped at the plan with ranked findings and a next action (6/6), and every code/config experiment stated a predicted plan or metric change (manual reading; one resource-scaling fallback lacked one).

Rejected as no-ops, because the shipped file already passed 3/3: checking platform-retained history (EMR persistent UI, History Server, `/var/log/spark/apps`) before declaring telemetry lost; quantifying wall time outside jobs; replaying fixed offsets into a fresh checkpoint and staging sink. Extending the measurement rule to "size targets" left a 128–512 MB file-size heuristic at 1/6 in both variants, so it was not adopted.

Limits: one model, three to six runs per variant, a low-cost grader with every flagged result checked by hand. These probes did not test description discovery or harness loading; the later OMP smoke below does.

## Pre-split evidence-safety addition and harness smoke (2026-10-15)

The intake now explicitly covers artifact authorization, private raw logs, and redaction before model ingestion or external sharing.

- **Actual harness:** OMP 18.11.0 with `openai-codex/gpt-6.1-sol`, a temporary workspace containing the copied original package under `.claude/skills`, no saved session, extensions/rules disabled, and only the read tool enabled. Managed host skill roots were unchanged; the temporary workspace was removed.
- **Discovery and behavior:** a synthetic natural-language request about a slow, spilling PySpark job did not name the skill. OMP loaded the original package. The response required sanitized derivatives instead of raw sensitive exports, distinguished the initial plan from completed-run evidence, marked performance unverified, and kept reruns outside analysis-only authorization.
- **Limits:** one OMP run demonstrates discovery/loading and those decisions, not reliability across models/harnesses, real endpoint access, output equivalence, or Spark performance.

## Static/runtime split and harness smoke (2026-10-15)

Two fresh invocations used the same isolated OMP setup above, with both new packages copied into a temporary workspace. Neither request named a skill:

- **Static review:** an existing PySpark job with unknown rows, bytes, files, join sizes, and key distribution selected only `apache-spark-static`. It delivered code-level findings without executing the workload, preserved duplicate/null/dimension multiplicity, treated driver collection as a return-contract decision, and proposed no invented sizing values or speedup.
- **Live diagnosis:** an unfinished application with a nonfinal AQE plan, 124 successful tasks, and four active byte-heavy tasks selected only `apache-spark-runtime`. It separated observed imbalance from unproven key skew, kept successful-task statistics and elapsed time provisional, and requested read-only follow-up observations rather than changing configuration or rerunning.
- **Packaging:** the actual Python-only copier selected both packages; the retired selection failed without creating its destination. An offline-built wheel contained both complete skills, matching source bytes, and no unsplit package.
- **Limits:** one run per route, one model/harness, synthetic inputs, and read-only tools. This demonstrates the split's discovery and decisions, not cross-model reliability, actual cluster connectivity, output equivalence, or real performance.

### Conditional-example smoke (2026-10-15)

The static skill adds three compact examples with risks, conditions, and validation, not a tuning catalogue. One additional isolated OMP invocation supplied unknown volume and three unsafe proposals: plain `length` for a UTF-8-byte-count/null-to-zero UDF, removal of a required complete-list return, and deduplication of intentionally repeated join keys. It selected the static skill and rejected all three as stated, without external access or workload execution; alternatives remained contract-dependent and performance unverified.

The existing copy/drift suites passed (26 tests, seven subtests), and source-only fingerprint checks reported no drift for either package. This is one model's reasoning smoke, not executed Spark correctness or performance proof.

### Runtime conditional-example smoke (2026-10-15)

The runtime skill adds three compact examples covering slow-task diagnosis, memory domains, and intermediate versus end-to-end metrics. Three additional isolated OMP invocations had both Spark skills discoverable and selected only the runtime skill:

- **Slow tasks:** similar work volumes, high fetch wait, and one shared host did not establish key skew or justify salting. The response ranked fetch-path hypotheses and kept live populations/plans provisional.
- **Memory:** a driver JVM heap failure during required list collection was distinguished from a successful spilling sort. The response retained the list contract, rejected unmeasured executor-heap doubling, and requested domain/working-set evidence.
- **Completed comparison:** repeated synthetic candidate runs had less spill and a faster stage but worse completed action latency and allocated executor-seconds. The response rejected the candidate against the stated objective, reported variability, and left billed cost unknown.

The existing copy/drift suites passed again (26 tests, seven subtests); both source fingerprints reported no drift. These are read-only, single-model reasoning probes with synthetic evidence, not real Spark executions, measured performance, or proof that the examples outperform the prior instructions.

## Open questions for a real job

The probes and OMP smoke cover hypothetical decisions. Real-job validation still needs a representative job, sanitized completed-run artifacts, immutable inputs, an output contract, and authorization for isolated repeated baseline/candidate executions of the actual action/sink. None was supplied; no measured performance claim follows. Remaining workload questions:

1. Does the intake accept the artifacts the user's deployment actually exposes: History Server, event logs, UI exports, and session configuration?
2. Do the common jobs need additional connector/table-format-specific branches beyond the portable SQL/DataFrame/RDD baseline?
3. Which Spark facts do real sessions miss? Add each as one line in the affected skill's `SKILL.md`, not as a new reference file.

## Spark batch execution optimization research

### Scope and interpretation

Primary sources inspected: Apache Spark **3.5.7**, **4.0.1**, and selected **4.1.3** docs/source. These are pinned evidence versions, not claims about the newest release. Match the job's exact Spark patch version, cluster manager, deployment mode, data-source implementation, and Python/Java dependencies before applying advice. The 3.5.7 and 4.0.1 SQL tuning pages establish the common SQL/AQE behavior; 4.1.3 is used only for explicitly identified Python changes. [S1][S2][S3][S4]

**Verified fact** means behavior explicitly described in the linked documentation or implementation. **Recommendation/hypothesis** means a candidate experiment inferred from those facts; it is not a promised speedup. This research section records source inspection only; no Spark job or benchmark was executed. Examples are illustrative, not measured results.

### Highest-value operating rules

1. **Recommendation:** begin with completed production-like executions and the actual terminal action, not a stylistic review of code. Link SQL execution IDs to stages/tasks, inspect scan/join/aggregate/write metrics, compare task distributions, and distinguish a hot partition from uniformly slow work. SQL UI exposes operator rows, scan/metadata time, exchange sizes and broadcast collection/build time; stage UI exposes shuffle/fetch/GC/task distributions. [S5][S6]
2. **Verified:** AQE re-optimizes from runtime statistics and has been enabled by default since 3.2. An initial `AdaptiveSparkPlan isFinalPlan=false` is not the executed final plan. In 4.0.1 source, finalization sets `isFinalPlan=true`, updates the SQL UI, and renders initial/final plans when they differ. **Recommendation:** inspect the completed SQL execution's final plan, actual coalesced/split readers and actual join operator before claiming a configuration changed the plan. [S1][S2][S7]
3. **Recommendation:** an action on a related DataFrame is not necessarily the action you are optimizing. `count()` only asks for row count; use the actual write/aggregation/other terminal action to benchmark, with representative inputs and a separate destination. A count can be useful for explicit cache materialization, but do not call its plan the write's final plan or treat row-count equality as full correctness. [S8][S9][S5]
   **Verified supporting mechanism:** the 4.0.1 optimizer runs scan/schema/partition pruning and re-runs column pruning around Python evaluation; therefore the benchmark must request the transformed columns whose computation matters. Inspect the action's plan rather than assuming all expressions in a DataFrame variable ran. [S38]
4. **Recommendation:** keep the output contract explicit: schema/types/nullability where applicable, row multiset including duplicates, join/null semantics, aggregate precision/tolerance, ordering/tie rules, generated identifiers, destination/partition layout, writer format/options and save/overwrite behavior. A shuffle can change order-sensitive `first`, and `monotonically_increasing_id` depends on partition IDs. These are correctness hazards for otherwise row-preserving repartitioning. [S10][S11][S12][S13]
5. **Recommendation:** test one causal candidate at a time, rerun under controlled allocation/concurrency/input/cache conditions, and report end-to-end elapsed time plus consumed resources and bottleneck metrics. A plan improvement, fewer files, or fewer spill bytes alone is not proof of a faster or cheaper complete job. Spark's UI/event logs provide the required execution evidence; event logging must be configured before application startup for postmortem UI history. [S5][S6]

### Compact symptom → evidence → candidate → risk → verification matrix

Every candidate below is a **hypothesis**, except correcting a demonstrably wrong/ineffective configuration. Numbers must be selected from observed data and capacity, not copied as universal targets.

| Symptom | Required evidence | Candidate change | Semantic/resource risk | Verification |
|---|---|---|---|---|
| Large scans despite selective query | Actual files/partitions and bytes read; `PartitionFilters`, `PushedFilters`, `ReadSchema`; scan vs metadata/listing time | Expose equivalent partition predicates and required columns; use supported source filters; preserve table root/`basePath` | Moving filters across an outer join changes unmatched rows; narrow paths can drop inferred partition columns; schema-merging changes can hide columns | Same output multiset/schema; fewer scanned files/bytes; compare full terminal action. [S14][S15][S16][S12] |
| Poor join/order choice | `EXPLAIN COST` estimates vs runtime rows/bytes; `DESCRIBE EXTENDED`; final join and exchange metrics | Refresh relevant table/column stats; consider CBO/join reordering only where stats and multi-join plan justify it | `NOSCAN` provides size only, not row/column stats; ANALYZE has execution cost; changing association exposes precision/order-sensitive behavior | Catalog stats updated; final plan actually changes; join cardinality preserved; rerun time and resources. [S2][S17][S3] |
| Large-side shuffle joined to genuinely small relation | Filtered/projected build-side row count and actual broadcast relation size; driver/executor headroom; final operator | Let stats select broadcast first; test explicit broadcast only for a bounded build relation | Hint can exceed automatic threshold; non-equi join may become broadcast nested-loop; driver must collect/build relation; executor memory competes with other tasks/broadcasts | Actual build side/operator, relation size, collect/build/broadcast time, peak memory/GC, duplicate/null join equality. [S1][S2][S18] |
| Many tiny post-shuffle tasks | Final adaptive readers and partition count/size; scheduler delay vs useful task work; active slots | AQE coalescing; vary initial shuffle count/advisory target and `parallelismFirst` only against observed overhead | Lower count can reduce useful parallelism or enlarge per-task working sets | Final partition-size distribution, elapsed/CPU/GC/spill; no output changes. [S1][S2][S5] |
| A few join stragglers | Per-task shuffle bytes/rows and duration; median vs tail; hot-key counts; final skew-join handling | AQE supported skew splitting first; selective hot-key salting only if AQE insufficient and replication is bounded | Many-to-many cardinality may be real output explosion; wrong salting loses/duplicates matches; replication adds shuffle/memory | Same row multiset including duplicate matches; final split tasks, lower tail duration, total bytes/resource cost. [S1][S2][S12] |
| Slow window/hot grouped Python operation | Window partition keys/order/frame; largest group; final clustered/global distribution; Python memory | Prune rows/columns first; equivalent preaggregation or narrower logical grouping only if mathematically valid; 4.1+ grouped iterator API where algorithm can stream | More shuffle partitions cannot divide one logical window group; salting changes rank/lag/frame; iterator does not make a non-streamable full-group algorithm streamable | Exact window values/ties/order; largest group/process RSS; full action time. [S19][S20][S21] |
| Input stages under/overpartitioned | Source split sizes/counts; file count and open/listing cost; storage bandwidth and slots | File-source partition byte/open-cost/min/max settings for scans; RDD input/operation partition arguments for RDDs | Scan knobs are not shuffle/output knobs; `maxPartitionNum` is suggested, not guaranteed | Scan task count/bytes distribution and elapsed time; no missing files or schema changes. [S1][S2][S22] |
| Too many small output files or serial tail | Actual write partitions, directories/buckets, data file sizes/counts, commit time and downstream read workload | Late `coalesce` for already balanced reductions; `repartition`/AQE `REBALANCE` if balancing is necessary | `coalesce(1)` can serialize upstream work; repartition adds a shuffle; directory contract, ordering and generated IDs may change | Count committed data files per output directory, sizes, write+commit and downstream read time; same contract. [S23][S24][S25][S26] |
| Same expensive lineage executed repeatedly | Jobs/stages showing repeat reads/transforms across actions; cache storage/materialization/eviction metrics | Persist reusable narrowed expensive intermediate at an intentional reuse boundary; unpersist at last use | Materialization cost, memory competition, spills/eviction/recompute; stateful/nondeterministic functions may not preserve observed behavior | Include first fill and all consumers in total time; verify InMemoryTableScan/cache partitions and no semantic drift. [S1][S2][S9][S22][S27] |
| Python evaluation dominates | Actual Python evaluation nodes/time; projected payload; CPU vs transfer; dependency/type compatibility | Equivalent built-in expression first; vectorized pandas UDF/iterator for truly vectorizable Python; `useArrow=True` for serialization bottleneck | Built-ins have different null/overflow/Unicode rules; Arrow row UDF remains row-wise; coercion/timezone changes; pandas loops may not vectorize | Compare types/nulls/edge-case outputs; Python-boundary operator/payload and full output action performance. [S20][S28][S29] |
| Spill / GC / executor loss | Spill memory and disk separately; per-task sizes, execution peaks, JVM GC, container/Python RSS and failure logs | Reduce per-task payload/working set, cache pressure or concurrency; adjust relevant heap/overhead only after identifying process limit | Spill metrics are not heap occupancy or a direct OOM diagnosis; Python/native OOM is not fixed by JVM heap alone | No failures/retries; process-specific memory/GC; task tails and end-to-end time, not zero-spill target. [S5][S6][S3][S30] |
| RDD `groupByKey` materializes values only to aggregate | Combine function, key distribution, shuffled rows/bytes, per-key working set | `reduceByKey` / `aggregateByKey` / `combineByKey` when reduction is valid; consider serializer only if serialization dominates | Reducer must be associative/commutative; map-side combining changes operation order; grouping all values may be semantically necessary | Same keyed aggregates with declared numerical tolerance; lower shuffle/working set, no new serialization failures. [S22][S31][S30] |

### Version gates and defaults: facts, not tuning values

| Behavior/configuration | Verified version-sensitive fact | Practical consequence |
|---|---|---|
| AQE and skew/coalescing | AQE default enabled since 3.2; coalescing and skew handling are enabled by their documented controls in 3.5.7/4.0.1. | Check effective session values and final plan rather than recommending “enable AQE” by reflex. [S1][S2] |
| AQE advisory sizing | `parallelismFirst=true` in both examined versions ignores the advisory target during coalescing in favor of minimum-size/parallelism considerations. 3.5 docs recommend false generally; 4.0.1 docs qualify false for a busy cluster. | A changed advisory size may not have the assumed effect. Busy-cluster efficiency vs available parallelism remains an experiment. [S1][S2] |
| File-scan partition cap | `spark.sql.files.maxPartitionNum` exists since 3.5.0 and is a **suggested**, not guaranteed, maximum for file-source splits. | Do not use on older versions or claim an exact cap/output count. [S1][S2] |
| Single-partition planning | 4.0 changes `spark.sql.maxSinglePartitionBytes` from `Long.MaxValue` to `128m`; planner may introduce shuffle to improve parallelism. | This is distinct from scan `files.maxPartitionBytes` and AQE advisory sizing; an upgrade can change exchanges without job-code changes. [S13][S3] |
| Static vs adaptive broadcast | Adaptive threshold inherits static automatic broadcast threshold unless set separately; hints can override automatic eligibility. | Disabling the static threshold is not a safety policy when adaptive threshold or hints permit broadcast. Inspect both plus final plan. [S1][S2] |
| Arrow pandas conversion | `spark.sql.execution.arrow.pyspark.enabled` is documented disabled by default in 3.5.7 and 4.0.1; it controls pandas conversion, not every Python API. | Do not treat it as an umbrella UDF optimization or driver-memory fix. [S20][S32] |
| Ordinary Arrow Python UDF | `udf(..., useArrow=...)` exists in 3.5.7; `None` consults `spark.sql.execution.pythonUDF.arrow.enabled`. Pinned 4.0.1 and **4.1.3** configurations both list that config default **false**. | Never copy a search-generated claim that 4.1 enables it by default; query the actual release/runtime. Arrow transport still executes ordinary Python UDFs row by row. [S28][S3][S4][S20] |
| 4.1 Python boundaries | 4.1 adds iterator `GroupedData.applyInPandas`; removes unnecessary pandas conversion for Arrow ordinary UDFs, changing coercion when output disagrees with declared schema; safe Arrow conversion becomes default true. Minimum pandas/PyArrow versions rise to 2.2.0/15.0.0. | Version-gate iterator advice; compare return schema/types/overflow and installed dependencies, rather than changing legacy flags to suppress errors. [S21][S29] |
| Arrow collection API | `DataFrame.toArrow()` / createDataFrame from PyArrow Table are introduced in 4.0. | `toArrow`, like `toPandas`, collects all records to the driver; it is not distributed export. [S20] |
| SQL semantics | 4.0 enables ANSI by default and changes ORC compression default from snappy to zstd; some JDBC read/write type mappings and timestamp behavior also change. | An engine upgrade must not be smuggled into a tuning experiment; preserve runtime/configs or explicitly approve and validate output differences. [S13] |
| Config renames/removals | 4.0 deprecates `spark.shuffle.unsafe.file.output.buffer` in favor of `spark.shuffle.localDisk.file.output.buffer`; removes legacy-prefixed datetime rebasing SQL configs; removes Mesos manager support. Old Arrow conversion aliases are deprecated in the config docs. | Consult the exact-version config/migration docs; do not reuse legacy blog bundles or assert that arbitrary SparkConf keys are effective. [S33][S13][S3] |
| Executor overhead | Configurable driver/executor **minimum** overhead settings arrive in 4.0; 3.5.7 documents a fixed minimum in the overhead calculation. Overhead-factor defaults also depend on Kubernetes non-JVM vs other jobs. | Memory recipes are deployment-sensitive, and minimum/factor are irrelevant when explicit overhead overrides them. [S34][S3] |
| Storage Partition Join | Compatible V2 source feature; several additional transform/subset/one-sided-shuffle options arrive in 4.0; `pushPartValues.enabled` default changes in 4.0. | Optional source-specific investigation, not a blanket tuning setting; prove Exchange removal and supported source/layout. [S2][S13] |

The older 3.5.7 SQL tuning page contains narrow/stale wording suggesting broadcast statistics are only supported for analyzed Hive Metastore tables. Do **not** turn that sentence into a universal Spark limitation: 4.0.1 explicitly describes data-source, catalog, and runtime statistics, and the task must inspect actual estimates/runtime metrics in its exact version. [S1][S2]

### Branch notes and non-obvious traps

#### Scans, pruning, and statistics

- **Verified:** file-source plans display `PartitionFilters`, `PushedFilters`, and `ReadSchema`; source partition discovery derives columns from paths. Reading a narrower partition path can remove a partition column from discovery unless the proper `basePath` is supplied. Recursive file lookup disables partition inference. **Recommendation:** preserve schema and root/path options when narrowing input; use actual file/byte metrics to confirm reduced I/O. A displayed pushed predicate alone is not a measured speedup. [S15][S14][S16][S5]
- **Verified:** Parquet filter pushdown and vectorized readers are separate mechanisms. Native record-level filtering only takes effect with pushed filters **and the vectorized reader unused**; disabling vectorization merely to enable record-level filtering is not automatically faster. Parquet aggregate pushdown requires footer statistics and can throw if they are missing. **Recommendation:** choose based on the actual reader/operator and representative reruns, not blanket “enable all pushdowns.” [S14]
- **Verified:** catalog `ANALYZE ... NOSCAN` collects only size; plain COMPUTE STATISTICS adds row count; FOR COLUMNS adds column/table stats. CBO/join-reorder controls are separately documented and default false in the inspected 4.0.1 configuration. **Recommendation:** inspect estimate errors and affected keys before paying for broader ANALYZE or enabling multi-join reorder. Existing source stats/AQE can already be sufficient. [S17][S3][S2]
- **Recommendation:** early projection/filtering is useful when the executed scan/shuffle still carries avoidable columns/rows; Spark may already perform it. Moving a filter from after an outer join into an input, replacing a predicate with a UDF, changing timestamp boundaries, or eliminating schema merging needs a semantic proof—not a “less data is better” justification. [S12][S13][S14][S15]

#### Join strategy, broadcast safety, and skew

- **Verified:** broadcast hints are prioritized above merge/hash hints and can override automatic size thresholds; they are not guaranteed for unsupported join types. Without equi-join keys, broadcast may mean nested-loop rather than hash join. AQE can convert sort-merge to broadcast after runtime sizes arrive, but upstream shuffle work may already have happened. **Recommendation:** first improve reliable build-side estimates/projection; force a broadcast only with bounded actual relation size and headroom, and prove the final operator. [S1][S2]
- **Verified (4.0.1 source):** `BroadcastExchangeExec` collects rows to the driver, constructs the broadcast relation, records its built size, enforces row limits and a hard **8 GiB** relation-size bound, then broadcasts it. **Recommendation:** compressed source-file bytes and a table's threshold eligibility are not driver/executor-memory safety proofs. Measure built relation size, concurrent broadcasts and active task memory; hard limits are failure guards, not safe tuning targets. Increasing timeout only changes how long to wait, not relation size or available memory. [S18][S3][S30]
- **Verified:** AQE's documented skew-join test requires both the factor-over-median condition and the absolute byte threshold; it splits and may replicate supported join partitions. **Recommendation:** investigate hot-key distributions and the final join rather than assuming any long tail triggers skew optimization or tuning thresholds below normal partitions. Increasing total partitions does not remove a single same-key hotspot. [S1][S2][S19][S31]
- **Recommendation / mathematical derivation from join semantics:** selective salting is a last-mile rewrite, not a generic knob. Give each hot fact row exactly one salt in `[0, B)`; replicate each matching hot dimension row across all `B` salts; keep non-hot rows at salt zero on both sides; join on **original key plus salt**, then remove salt. Every original matching pair is produced once. Hashing the hot key itself does not distribute rows because the key is identical; use a stable row identifier or another varying input, and inspect balance. Existing dimension duplicates must remain duplicates unless the business contract independently permits deduplication. [S12][S24]
- **Recommendation / derivation:** independently random-salting both sides loses matches; replicating both sides can multiply them. Generic full/right outer rewrites can duplicate unmatched replicated rows; outer/semi/anti/null-safe joins need a join-specific proof. Preserve `=` vs `<=>` null behavior. Do not convert keys to strings, fill nulls with a sentinel, use concat delimiters, or drop duplicates merely to make a salt recipe work. A genuine many-to-many join can be intrinsically large; salting redistributes that work, not its required output. [S12][S10]
- **Recommendation / algebra:** salted aggregation requires a valid merge state, not merely removing the salt and reaggregating arbitrary answers. SUM/COUNT/MIN/MAX are decomposable with their original null/type rules; AVG needs sum and count of **non-null** values, not average-of-averages. Distinct counts, medians/quantiles, order-sensitive first/last, ranking and arbitrary group UDFs cannot be merged with a generic second SUM. Partial aggregation can change floating-point association or decimal/intermediate-overflow behavior; require declared numerical tolerance or exact arithmetic proof. RDD reductions explicitly require associative/commutative functions. [S10][S11][S31][S13]

#### Windows are not skew joins

**Verified (3.5.7 and 4.0.1 source):** window execution requires all rows in one physical partition when no partition specification exists; otherwise it requires clustering by the logical window partition keys and ordering by those keys plus window order. **Recommendation:** more executors or shuffle partitions cannot parallelize one hot logical window partition under the same semantics. Salting the window partition changes rank, lag/lead, running frames and peer groups. Narrowing the window group, dropping rows, or replacing a full window by an aggregate/join is permissible only with an equivalence proof, including tie/null/frame behavior. Do not sell AQE's skew-join rule as a general window-skew fix. [S19][S35][S1][S2]

#### Partition sizes and output files

- **Verified:** file-scan sizing controls only supported file sources. SQL shuffle initial counts, AQE post-shuffle sizes, RDD partition arguments and writer directory partitioning address different boundaries. `coalesce` is a narrow reduction and cannot increase partition count; drastic coalescing can execute upstream work on very few nodes. `repartition` adds redistribution; with columns it hash-partitions. **Recommendation:** choose the boundary implicated by evidence, and avoid preemptively repartitioning before an operation that already supplies its own exchange. [S1][S2][S23][S24][S22]
- **Verified:** AQE `REBALANCE` is best effort and ignored when AQE is off. A writer's `partitionBy` is a filesystem directory layout, not the same thing as execution `repartition`. The writer can emit multiple files per task because of output directories/buckets and `maxRecordsPerFile`; that setting limits rows per file, not bytes. Empty partitions and writer/source-specific behavior also complicate exact counts. **Recommendation:** do not promise “N partitions = N final files”; count actual committed data files per directory and preserve required partitioning/bucketing/format/codec/schema. [S25][S26][S3][S36]
- **Recommendation:** remove an unnecessary single-file funnel only if the downstream contract does not require it. If the contract genuinely requires one data file, make that trade-off visible rather than silently replacing it with a directory of many files. Changing compression, partition columns, buckets, ordering or overwrite scope is an output-contract decision, not free physical tuning. [S23][S26][S13][S14]

#### Reuse, caching, and RDDs

**Verified:** transformations are lazy; transformed RDDs may recompute per action; persistence fills only when computed and lost partitions can recompute. DataFrame persistence in 3.5.7 defaults to MEMORY_AND_DISK_DESER, unlike the RDD default MEMORY_ONLY; Python RDD objects are already pickled and JVM serialized storage advice is not a Python-unpickled-storage toggle. SQL cache is columnar and scans required columns. Unified storage and execution memory compete. [S22][S9][S1][S2][S30]

**Recommendation:** cache only a repeatedly used, expensive, bounded intermediate—usually after justified narrowing—and inspect executed cache reuse rather than assuming a named variable or CTE is materialized. Include cache-fill time and all relevant consumers; avoid judging on warmed second-consumer latency alone. Unpersist after last use. Avoid caching a large one-pass stage to “use Spark's memory”; recomputation can be cheaper than cache I/O/eviction/GC. [S22][S27][S30]

**Recommendation:** for RDD aggregation, replace `groupByKey` with combining only when the consumer truly needs a reducible aggregate, not the ordered/raw collection of all values. Kryo is a JVM/RDD serialization candidate when serialization/transfer is measured as expensive; do not present `spark.serializer=KryoSerializer` as a cure for SQL internal rows or Python UDF/RDD pickle boundaries. The official guide's “2–3 tasks per core,” “200 ms tasks,” serialization speedup estimates and raw-to-object expansion estimates are starting hypotheses, not capacities or performance guarantees. [S22][S31][S30]

#### Python and Arrow boundaries

- **Verified:** ordinary Python UDFs are deterministic by default, may be invoked fewer/more times due to optimization, and do not support SQL boolean short circuiting; failure guards must live inside the UDF. **Recommendation:** audit existing UDF null/exception/state/nondeterminism behavior before swapping implementation or caching it; do not move side effects into a new execution pattern. [S28]
- **Verified:** pandas UDFs use Arrow transfer and can apply vectorized pandas operations; ordinary Arrow UDFs still evaluate rows individually. Conversion flag `arrow.pyspark.enabled`, UDF flag `pythonUDF.arrow.enabled`, explicit `useArrow`, pandas UDFs and grouped APIs are distinct. **Recommendation:** built-ins are the first candidate when semantically equivalent, then genuinely vectorized/iterator APIs if Python is necessary, then ordinary Arrow UDF for measured serialization overhead. A pandas function containing a Python loop is not automatically a vectorized computation. [S20][S28][S32]
- **Verified:** in 3.5.7/4.0.1 whole-group `applyInPandas` loads the group into memory, and `maxRecordsPerBatch` does not cap that group; grouped aggregate pandas UDFs also load group/window data and do not support partial aggregation. 4.1 introduces grouped iterators, but their code still needs bounded state to gain memory benefit. **Recommendation:** measure largest groups and Python RSS, not just Arrow batch size. A smaller batch is a candidate for wide ordinary batch payloads, not a universal hot-group OOM fix. [S32][S20][S21]
- **Verified:** Arrow conversion can change coercion when declared output and Python return values disagree; timestamp exchange includes session timezone localization and microsecond truncation of nanoseconds. `toPandas` and `toArrow` still collect to the driver. **Recommendation:** validate null/NaN, nullable integers, decimals/overflow, nested data, Unicode/binary, timestamp/timezone and output schema against the original job; retain distributed output instead of collecting large data to “use Arrow.” [S20][S29]

#### Memory diagnosis and configuration lifetime

- **Verified:** stage spill-memory is the deserialized representation and spill-disk the serialized representation. Task `peakExecutionMemory` only covers particular Spark execution structures (SQL tracking is unsafe operators/ExternalSort), not all JVM/Python/native/container memory; process-tree metrics are separately exposed when enabled. **Recommendation:** do not interpret spill-memory bytes as heap requirement or add spill-memory and spill-disk as independent data volumes. Spilling is an observed mechanism; prove that its I/O/GC cost is on the critical path before prioritizing it. Executor loss can come from JVM heap, native/Python overhead, disk, container limit or another failure; inspect error evidence first. [S5][S6]
- **Verified:** execution/storage share unified memory; increasing cached storage or changing memory fractions affects execution headroom. Python workers/native buffers consume memory outside executor JVM heap; without explicit `spark.executor.pyspark.memory`, Python shares overhead with other non-JVM processes. YARN/Kubernetes container resource formulas include the documented heap/overhead/off-heap/Python components. `spark.python.worker.memory` concerns Python **aggregation spilling**, not a general cap on every Python UDF's RSS. **Recommendation:** reduce avoidable task payload/cache/concurrency before blindly raising fractions, and resize the identified memory domain only with container/node capacity and cost evidence. [S30][S34][S3]
- **Verified:** deployment properties such as driver memory/executor instances may not respond to programmatic changes after launch; in client mode driver memory must be set before its JVM starts. Runtime SQL configs are per-session mutable; static SQL configs are immutable after creation. The Environment tab primarily shows explicitly set SparkConf values, not an exhaustive account of all SQL session changes/defaults. **Recommendation:** deploy resource/JVM/serializer changes through the launch configuration and restart where needed; set mutable SQL candidates before constructing/executing the tested query; record effective values via the appropriate SparkConf/session getter and restore temporary session overrides. Merely accepting/storing a key does not prove that the running components used it. [S34][S3]
- **Verified:** driver `maxResultSize` protects against excessive serialized action results; raising it can cause driver OOM. Broadcast build, `collect`, `toPandas` and `toArrow` are driver-sensitive boundaries. **Recommendation:** do not disable this guard or collect full results just to bypass it; use bounded diagnostics and distributed comparisons/output. [S3][S20][S18]

### Three representative experiments

#### 1. SQL scan/join: expose an existing date restriction and correct estimates

Assume `fact_events.event_date` is an existing partition column, the required result is the complete July 2026 event rows joined to active accounts, and the baseline already applies exactly these restrictions. This is a candidate rewrite **only if the executed baseline plan fails to prune/project them**; spelling CTEs differently is not itself an optimization.

```sql
-- Use only if catalog statistics are missing/stale and ANALYZE is supported for this table.
ANALYZE TABLE dim_accounts COMPUTE STATISTICS;
ANALYZE TABLE dim_accounts COMPUTE STATISTICS FOR COLUMNS account_id;

EXPLAIN COST
WITH events AS (
  SELECT event_id, account_id, amount
  FROM fact_events
  WHERE event_date >= DATE '2026-07-01'
    AND event_date < DATE '2026-08-01'
), accounts AS (
  SELECT account_id, segment
  FROM dim_accounts
  WHERE active = true
)
SELECT e.event_id, e.account_id, e.amount, a.segment
FROM events e INNER JOIN accounts a ON e.account_id = a.account_id;
```

Inspect completed scan bytes/files, partition filters/read schema, estimate-vs-runtime rows and final join operator. Do **not** add BROADCAST unless the filtered/projected accounts relation is measured safe, and do not add DISTINCT to make it smaller: duplicates are part of inner-join multiplicity. Baseline and candidate must use identical data snapshots and terminal writes/options. ANALYZE cost belongs to the operational proposal and should not be hidden. [S14][S15][S17][S2][S12][S18]

#### 2. Python boundary: replace a null-safe string-length UDF with a built-in

Assume input `name` is StringType and the existing UDF's complete contract is `None -> None`, otherwise Python string character count, with integer output. Candidate:

```python
from pyspark.sql import functions as F

candidate = input_df.withColumn("name_length", F.length("name"))
```

Spark `length` counts string characters including trailing spaces, and binary bytes for binary inputs; it is available in both target families. Validate schema/nulls/empty/trailing-space/Unicode edge cases against the existing UDF before adopting; do not replace grapheme-count or byte-count logic with this expression. Inspect the executed plan for removal of that Python evaluation boundary and benchmark the actual output write, not `candidate.count()` that does not request `name_length`. If the Python algorithm has no equivalent built-in, choose a vectorized pandas/iterator candidate for vectorizable computation, or explicit `udf(..., useArrow=True)` for measured transfer/serialization overhead; validate Arrow return coercion/dependencies for the runtime version. [S37][S28][S20][S29][S8]

#### 3. Selective salting of an inner equi-join after observed AQE limits

Assume `fact` columns `(row_id, key, value)`, `dimension` columns `(key, label)`, a non-null string `hot_key` identified from completed task/key-distribution evidence, and positive integer `buckets` selected experimentally. `row_id` is a stable varying field, not a newly partition-dependent ID. `key` equality is ordinary SQL `=`, not null-safe. Existing dimension duplicates are intentionally retained.

```python
from pyspark.sql import functions as F

fact_salted = fact.withColumn(
    "_salt",
    F.when(
        F.col("key") == F.lit(hot_key),
        F.pmod(F.xxhash64("row_id"), F.lit(buckets)),
    ).otherwise(F.lit(0)),
)
dimension_salted = dimension.withColumn(
    "_salts",
    F.when(
        F.col("key") == F.lit(hot_key),
        F.sequence(F.lit(0), F.lit(buckets - 1)),
    ).otherwise(F.array(F.lit(0))),
).withColumn("_salt", F.explode("_salts")).drop("_salts")

candidate = fact_salted.alias("f").join(
    dimension_salted.alias("d"), ["key", "_salt"], "inner"
).select("f.row_id", "key", "f.value", "d.label")
```

The salting operators are upstream APIs available in the targeted 3.5/4.x families: `xxhash64` returns a long hash, `pmod` provides a nonnegative remainder for a positive divisor, `sequence` includes both endpoints, and `explode` emits one row per array element. Bucket count remains empirical; these APIs do not establish uniform distribution. [S39][S40][S41][S42]

**Derivation:** every fact row is assigned one salt; every matching hot dimension row is present at that salt, so each original pair appears once, including duplicate dimension pairs. All non-hot rows match on salt zero. Null keys still do not match under ordinary equality. This does not generalize automatically to full/right outer/null-safe/grouped/window operations. Hashing `key` instead of `row_id` would send all hot rows to one salt. Test the hypothesis only if replication fits and final AQE handling was inadequate; compare distributed row **multisets**, per-salt/task skew, total shuffle bytes, runtime and memory. A weak `row_id` distribution or real many-to-many explosion can eliminate the expected gain. The correctness proof derives from Spark's join/null semantics and hash-partitioned execution; Spark does not endorse a universal bucket count or promise a speedup. [S12][S10][S24][S1][S2]

### Heuristics that must stay hypotheses

- A target scan/shuffle partition byte size, task duration, partitions-per-core, or file size/count is **not universal**: compression, row width, hot keys, decoding, memory per concurrent task, slots, storage latency and downstream reads differ. Defaults are reference behavior, not targets. [S1][S2][S30]
- More partitions reduces per-task working sets only when work can be spread; it cannot split required same-key window/group semantics and can add overhead/files. Fewer partitions can reduce scheduling cost but create stragglers/OOM or underuse the cluster. [S23][S24][S19][S20][S30]
- Cache can save recomputation or worsen total time through fill/GC/eviction; a second-use benchmark alone is biased. [S22][S27][S30]
- Broadcast can avoid shuffle or cause driver/executor pressure/nested-loop explosion. File size is not built hash-relation size. [S18][S2]
- Arrow/pandas/Kryo can reduce a relevant serialization boundary or merely move the bottleneck; ordinary Arrow UDFs remain row-wise and pandas vectorization is algorithm-dependent. [S20][S30]
- “Zero spills,” “all cores busy,” “no shuffle,” “one output file,” “AQE enabled,” and “larger executor” are not optimization goals by themselves. Favor measured complete-job elapsed time/resource cost with preserved output and acceptable reliability. [S5][S6][S23][S30]

### Optional, explicitly non-portable acceleration

**Recommendation:** keep cloud/vendor engines, proprietary cache/indexes, GPU/native plugins, vendor-only configuration keys and connector-specific layout optimizations out of the portable baseline. Use them only when the existing environment provides them and their own version/support documentation is available; report a separate environment-specific experiment, output-compatibility check and cost comparison. Upstream Spark exposes plugins/resources and source-specific V2 storage partition joins, but support/benefit depends on the plugin, cluster manager, source and storage layout. Do not present a vendor feature as an Apache Spark guarantee or require a platform migration to complete an execution-tuning task. [S3][S2][S33]

### Primary sources inspected

[S1]: https://spark.apache.org/docs/3.5.7/sql-performance-tuning.html
[S2]: https://spark.apache.org/docs/4.0.1/sql-performance-tuning.html
[S3]: https://spark.apache.org/docs/4.0.1/configuration.html
[S4]: https://spark.apache.org/docs/4.1.3/configuration.html
[S5]: https://spark.apache.org/docs/4.0.1/web-ui.html
[S6]: https://spark.apache.org/docs/4.0.1/monitoring.html
[S7]: https://github.com/apache/spark/blob/v4.0.1/sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/AdaptiveSparkPlanExec.scala
[S8]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.count.html
[S9]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.persist.html
[S10]: https://spark.apache.org/docs/4.0.1/sql-ref-null-semantics.html
[S11]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.first.html
[S12]: https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-select-join.html
[S13]: https://spark.apache.org/docs/4.0.1/sql-migration-guide.html
[S14]: https://spark.apache.org/docs/4.0.1/sql-data-sources-parquet.html
[S15]: https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-select-hints.html
[S16]: https://spark.apache.org/docs/4.0.1/sql-data-sources-generic-options.html
[S17]: https://spark.apache.org/docs/4.0.1/sql-ref-syntax-aux-analyze-table.html
[S18]: https://github.com/apache/spark/blob/v4.0.1/sql/core/src/main/scala/org/apache/spark/sql/execution/exchange/BroadcastExchangeExec.scala
[S19]: https://github.com/apache/spark/blob/v4.0.1/sql/core/src/main/scala/org/apache/spark/sql/execution/window/WindowExecBase.scala
[S20]: https://spark.apache.org/docs/4.0.1/api/python/tutorial/sql/arrow_pandas.html
[S21]: https://spark.apache.org/docs/4.1.3/api/python/reference/pyspark.sql/api/pyspark.sql.GroupedData.applyInPandas.html
[S22]: https://spark.apache.org/docs/4.0.1/rdd-programming-guide.html
[S23]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.coalesce.html
[S24]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.repartition.html
[S25]: https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-select-hints.html#partitioning-hints
[S26]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.partitionBy.html
[S27]: https://spark.apache.org/docs/4.0.1/web-ui.html#storage-tab
[S28]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.functions.udf.html
[S29]: https://spark.apache.org/docs/4.1.3/api/python/migration_guide/pyspark_upgrade.html
[S30]: https://spark.apache.org/docs/4.0.1/tuning.html
[S31]: https://spark.apache.org/docs/4.0.1/api/python/reference/api/pyspark.RDD.reduceByKey.html
[S32]: https://spark.apache.org/docs/3.5.7/api/python/user_guide/sql/arrow_pandas.html
[S33]: https://spark.apache.org/docs/4.0.1/core-migration-guide.html
[S34]: https://spark.apache.org/docs/3.5.7/configuration.html
[S35]: https://github.com/apache/spark/blob/v3.5.7/sql/core/src/main/scala/org/apache/spark/sql/execution/window/WindowExecBase.scala
[S36]: https://github.com/apache/spark/blob/v4.0.1/sql/core/src/main/scala/org/apache/spark/sql/execution/datasources/FileFormatDataWriter.scala
[S37]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.length.html
[S38]: https://github.com/apache/spark/blob/v4.0.1/sql/core/src/main/scala/org/apache/spark/sql/execution/SparkOptimizer.scala
[S39]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.xxhash64.html
[S40]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.pmod.html
[S41]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.sequence.html
[S42]: https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.functions.explode.html


## Apache Spark completed-run diagnostics and verification research

### Scope, evidence status, and version gate

This is research for a skill that optimizes **already implemented batch jobs**, not a Spark tuning prescription or a record of a real benchmark. Upstream pages/source listed below were inspected. No Spark application, REST server, benchmark, or correctness test was executed. Commands below are source-checked templates with stated prerequisites, not observed working requests against a deployment.

**Verified facts** are marked **Fact** or carry an upstream citation. **Recommendations** are the proposed skill behavior and are labeled as such. Hypothetical examples are not measured results.

**Recommendation — first gate:** identify the exact application Spark version, distribution/patches, language/API, cluster manager and deploy mode; separately identify the History Server version. Select the matching version's docs and source tag before interpreting APIs, defaults, AQE eligibility, or streaming recovery constraints. `/api/v1/version` reports the version of the serving Spark installation, so do not use a differently versioned History Server's answer as sole evidence of the application's version. The source returns `org.apache.spark.SPARK_VERSION`; application attempt information also includes `appSparkVersion`. [API-root source][AR35] [REST model source][AM35]

The API shapes below were verified in **Spark 3.5.7** and compared with **4.0.1** official monitoring docs. Both document the relevant application/job/stage/task/SQL/environment paths. This is not a claim that an endpoint or newer query option exists in every older release. `/docs/latest` is a moving target; do not silently select it for an older job. `/api/v1` has a documented additive compatibility policy, but new endpoints/fields may be added, so readers should tolerate extra fields and explicitly distinguish unavailable/missing metrics from zero. [3.5.7 REST][M35] [4.0.1 REST][M40]

### 1. Source-linked post-run intake checklist

**Recommendation:** collect a minimal, authorized evidence bundle for a specific completed application attempt and actual terminal action. Avoid dumping whole environments or sensitive query text into chat.

- [ ] **Identity and code:** application ID; application attempt ID if present; start/end timestamps, outcome, exact Spark/runtime/distribution versions; cluster manager/deploy mode; baseline code revision/build artifact and dependency versions; exact submitted entry point/arguments. Preserve the mapping from this run to the existing job. History Server can show failed/incomplete attempts as well as the successful final attempt; an application can be listed incomplete after a crash despite no longer running. [Monitoring][M35]
- [ ] **Workload and output contract:** immutable input snapshot/file manifest/table snapshot/source offsets; input schema and approximate size; filters/date range; output schema and ordering/multiplicity/null/numeric rules; sink, save mode, partition columns and intended side effects. Record whether this is batch or streaming before proceeding. File save modes can overwrite/delete or append data; their documented generic behavior is not an atomic transaction guarantee. [Save modes][SAVE35] [Streaming identification/recovery][SS35]
- [ ] **End-to-end observation:** externally measured start-to-successful-output-commit latency and its boundaries; SQL execution duration; relevant job/stage intervals; application startup/teardown/queue time separately if available. Record cluster allocation/cost evidence separately, not merely task time. UI SQL duration, task timing, and commit metrics have different scopes. [Web UI][UI35] [Task metrics][M35]
- [ ] **Completed execution evidence:** authorized History Server/UI links or selected REST JSON; SQL execution IDs and final/current plans; linked job IDs, stage IDs and stage attempt IDs; task distributions and slow-tail task details; all-executor timeline including removed executors; relevant driver/executor failure snippets. A live UI normally disappears with the application; post-run replay requires persisted event logs. [Monitoring][M35] [Web UI][UI35]
- [ ] **Effective configuration at the relevant execution:** redacted Environment page/REST response for explicitly set Spark properties; submit configuration and resource settings; execution-specific/session SQL settings (AQE, broadcast, shuffle/scan partitions, ANSI/timezone and other semantics settings), including any code that changes them during execution. The Environment page shows explicitly configured properties, not a materialized table of all defaults; SparkConf values have precedence over submit flags, which have precedence over `spark-defaults.conf`. Deployment settings might not take effect when changed late in code. Resolve missing defaults against the exact runtime version. [Configuration][CONF35]
- [ ] **Session-specific config caveat:** when present, inspect the SQL execution's recorded modified configs, not only SparkContext configuration. In v3.5.7 `SQLExecution` records a redacted execution-time session config delta, excluding certain driver/executor/global-equal entries; this is not a complete config snapshot. [SQL execution source][SE35]
- [ ] **Resources and cache state:** actual executor count/cores/memory/resource profiles over time; dynamic allocation settings and allocation timeline; concurrent workloads; materialized persisted datasets/storage levels; warm/cold application/JVM/OS/remote-storage/metadata caches, to the extent observable. Spark persistence is materialized by actions, and dynamic allocation can change resources during the same job. [Storage UI][UI35] [Scheduling][SCHED35]
- [ ] **Evidence completeness and provenance:** whether event logging was enabled before execution; log location, permission/retention/rolling/compaction; export method/time; missing stages/tasks/SQL executions; removed-executor retention; event-log metrics options. UI/status retention caps exist for jobs, stages, tasks, dead executors and SQL executions. History replay retention can hide recorded entries; rolling-log compaction is lossy and can remove completed-job/SQL/executor events. [Monitoring][M35] [UI/config retention][CONF35]
- [ ] **Privacy/safe rerun authorization:** approved local artifact location, redaction, authorized access route and output destination; permission for any new cluster run or external write. Neither a public-looking UI URL nor task evidence authorizes accessing someone else's job or rerunning production writes. See section 3.

#### Boundary when telemetry does not exist

**Fact:** enable `spark.eventLog.enabled=true` **before starting the application** to persist the UI's event evidence; History Server reconstruction requires those event logs. In 3.5.7 event logging defaults to false. Enabling it after a completed execution does not produce that execution's missing history. [Monitoring][M35] [Configuration][CONF35]

**Recommendation:** first distinguish (a) logging was never enabled, (b) logs exist but permission/location/History Server ingestion is wrong, (c) logs were deleted or compacted, (d) UI/API retention hides events, and (e) independent telemetry or saved UI/REST exports exist. A single 404 is not proof there were no logs; verify application attempt, endpoint/version, access and retention before concluding absence. Keep captured external metrics/logs as partial evidence, clearly scoped.

If no execution telemetry survives, return **“bottleneck unproven; performance improvement unverified.”** Static code/EXPLAIN can support limited semantics review and a labeled hypothesis, not a task-skew, GC, I/O, network, or AQE-runtime diagnosis. Finish reachable work: define the workload/output contract and a safe evidence-capturing baseline plan. If rerunning is unavailable or unapproved, stop performance claims rather than inventing history.

For an approved **future** run, the minimum Spark configuration is `spark.eventLog.enabled=true` plus `spark.eventLog.dir` pointing at an existing writable, protected filesystem location readable by the authorized History Server. Its `spark.history.fs.logDirectory` must point at the corresponding logs. `spark.eventLog.logStageExecutorMetrics=true` is an optional evidence choice for per-stage executor peaks (3.0+), **not** retroactive recovery and not a blanket tuning setting. Block-update logging is separate and documented to considerably enlarge event logs; do not enable every logging option by default. [Monitoring][M35] [Config][CONF35]

### 2. Trace the completed action rather than a plausible plan

#### Verified execution linkage

- SQL/DataFrame execution details show associated jobs and physical/logical plans; job details show associated SQL and stages; stage details show associated jobs and task attempts. Whole-stage codegen IDs can help cross-reference stage DAG scopes with SQL operators, but a codegen ID is not a stage ID and does not establish one operator per task/stage. [Web UI][UI35]
- v3.5.7 `SQLExecution` sets the job local property **`spark.sql.execution.id`** and tracks a root execution ID for nested/subqueries. `SQLAppStatusListener.onJobStart` uses that property to connect job ID, stage IDs and the SQL execution. Jobs without it are not recorded by this listener as SQL jobs. [Execution source][SE35] [SQL listener][SL35]
- The REST job model includes `stageIds`; stage identity includes `stageId` plus `attemptId`. Task data includes `taskId`, `index`, `partitionId`, `attempt`, executor/host, status, locality and `speculative`. Treat **application attempt**, **stage attempt**, and **task attempt** as different identifiers; never use one interchangeably in a URL or aggregate. [REST models][AM35]

**Recommendation — lineage key:** `(application ID, application attempt, SQL/root execution ID if applicable, job ID, stage ID, stage attempt, task ID/index/partition ID, task attempt, executor)`. Use UI associations or recorded IDs; do not infer ownership from neighboring timestamps alone. Account for shared/reused/skipped stages and overlapping jobs rather than summing every linked stage as unique sequential work. For a pure RDD action, use jobs → stages → attempts/tasks and RDD dependency lineage; SQL/AQE evidence is not required and AQE should not be claimed to tune arbitrary RDD execution.

#### Initial EXPLAIN versus executed/final AQE plan

**Facts:** `EXPLAIN FORMATTED` gives the physical outline and node details; `EXPLAIN EXTENDED` includes parsed/analyzed/optimized logical and physical plans; `EXPLAIN COST` includes logical statistics **if available**. Neither “cost” nor a pre-run physical plan is an observed runtime duration. The PySpark API accepts `df.explain(mode="formatted")` and `df.explain(mode="cost")` in the pinned version. [SQL EXPLAIN][EX35] [DataFrame EXPLAIN][DFEX35]

AQE uses runtime statistics and can coalesce post-shuffle partitions, change join strategy, and handle eligible skewed joins. AQE is enabled by default since 3.2.0, but effective settings and applicability still need checking. Its skew-join split conditions and scope are specific; arbitrary aggregation skew is not equivalent to an AQE skew-join case. [AQE docs][AQE35]

v3.5.7 adaptive-plan source keeps `initialPlan`, a current physical plan, and `isFinalPlan`; tree output labels final/current versus initial plans when changed. AQE publishes `SparkListenerSQLAdaptiveExecutionUpdate`, and SQL UI/status listener replaces the stored physical plan description on these updates. Thus a post-run SQL UI/REST execution is stronger evidence than re-explaining a newly reconstructed DataFrame. Do not assume the single REST `planDescription` preserves every earlier AQE snapshot; inspect recorded event updates if intermediate plans are required. [Adaptive source][AP35] [SQL listener][SL35]

**Recommendations:**

1. Anchor to the **actual terminal action**, including its sink/write. `count()`, `show()`, a sampled/limited query and the production write are different actions and may execute different plans; a count-only experiment does not establish write/commit performance or that all expensive output expressions were exercised.
2. Keep the pre-execution plan as context, but prefer completed SQL execution metrics and the executed adaptive plan. If `isFinalPlan=false`, an initial-only plan, truncated description, failure, or missing event history prevents final-plan evidence, state that limitation rather than assuming the join type/partition count.
3. Compare initial versus final join types, coalesced/skew-split partitioning, broadcasts, reused exchanges, runtime row/data sizes and actual task count. Initial `Exchange(...,200)` does not prove 200 reducer tasks ran. A late AQE join conversion may also have already incurred upstream shuffle work; a final BroadcastHashJoin is not proof there was no shuffle. [AQE docs][AQE35]
4. Capture plans without casually running another production action. EXPLAIN produces plans, but planning can access metadata or user extensions; it is not a permission-free promise of zero external interactions.

### 3. Privacy, secure collection, and write-side safety

**Verified security facts:** Spark security is not enabled by default. UI authentication requires an appropriate servlet authentication filter; Spark does not supply a built-in authentication filter in the pinned release. UI authorization ACLs require authenticated identity, and History Server authorization uses its own `spark.history.ui.acls.enable` configuration. RPC `spark.authenticate` is not a substitute for UI authentication. Spark documents separate UI/History Server TLS settings and event-log filesystem permissions. [Security][SEC35]

App-specific `/api/v1` source checks UI view permission using the request's authenticated remote user. However, the v3.5.7 application-list handler itself does not perform this app-specific check; do not assume app ACLs hide all listing metadata or replace securing the server/proxy. `/logs` also checks view permission, but exports sensitive raw event logs. [REST root/security gate][AR35] [Application-list source][AL35] [Application resource][OA35]

**Redaction facts:** `spark.redaction.regex` redacts matched configuration/environment keys or values from the environment UI and various logs; its default pattern targets secret/password/token/access.key. `spark.redaction.string.regex` and the SQL redaction regex options govern string/options redaction, including explain output. Pattern-based built-in redaction is not a guarantee that every literal, URI, credential, SQL statement, stack trace, hostname, business identifier, or row sample is safe. The environment REST handler explicitly invokes Spark redaction on property sets, not on every possible artifact field. [Config][CONF35] [Environment REST implementation][OA35]

**Recommendations:**

- Use only the user-approved HTTPS/authenticated proxy or an approved protected local access path. Do not publish 4040/18080 to the internet, disable ACLs/TLS/certificate validation, forge identity headers, bypass 401/403, or add a wildcard ACL to make collection convenient. Request existing access through the deployment's normal mechanism.
- Collect the narrowest useful evidence: app/attempt IDs and timings, selected stage/task metrics and sanitized plan/operator descriptions, selected failure messages and required config values. Prefer operator metrics to row samples. Raw environment/config/log exports stay in a private approved location; inspect/redact before sharing externally or in a model prompt.
- Exclude passwords, auth headers, cookies, keytabs, cloud keys, signed URLs/query parameters, JDBC credentials, PII/query literals and data contents. Preserve consistent anonymous task/executor/input labels and useful metric magnitudes. Mark what was removed; if redaction hides the needed causal evidence, identify the missing prerequisite rather than reconstructing secrets.
- Do not modify raw event-log syntax in place or upload logs to a third-party analyzer without approval. Preserve an authorized original privately when allowed; share a sanitized derived report. Respect filesystem ACLs/object-store IAM and retention. A log zip is not a public diagnostic artifact.
- A “rerun” is an application execution with its actual side effects. Inspect `overwrite`, append/insert/upsert/merge, JDBC/custom sinks, `foreach`/`foreachPartition`, external calls and source-cleaning before launching. Choose isolated per-run output/table namespace and deny production mutation, while maintaining a representative sink/commit path where necessary. If isolation changes storage semantics/cost, record that benchmark limitation.
- Never delete/overwrite a user's output or checkpoint to clear a benchmark, change a committer to obtain a speedup without correctness validation, append a candidate into production, or use `mode("ignore")` and time a no-op. Generic save modes are documented as non-atomic, and overwrite can delete existing data before producing new output. Transactional connectors require their own verified guarantees. [Save modes][SAVE35]

### 4. Official REST shapes and safe bounded templates

**Verified in the pinned 3.5.7/4.0.1 monitoring docs:** the monitoring JSON root is **`/api/v1`**, ordinarily on the live application UI or History Server. It is **not** the standalone REST submission service on port 6066, nor a `/history/...` UI URL. With a reverse proxy, retain its verified external path prefix. App IDs are required even for a live single-app UI. For YARN cluster-mode attempts, the documented `[app-id]` placeholder becomes `[base-app-id]/[attempt-id]`; do not add a made-up `/attempts/` component or invent attempt `0`. Use IDs returned by the actual listing/attempt metadata. [REST docs][M35] [REST docs 4.0.1][M40] [Security service distinction][SEC35]

Let `ROOT` be the approved server/proxy root **including `/api/v1`**, and `APP` be `ROOT/applications/<app-id>` or `ROOT/applications/<base-app-id>/<app-attempt-id>` when appropriate. URL-encode each identifier path segment if necessary; preserve the separator between application and attempt.

| Request suffix | Correct purpose and important caveat |
|---|---|
| `ROOT/version` | Serving installation's version, not sole proof of the logged application's version. |
| `ROOT/applications?status=completed&limit=20` | Bounded completed-application listing; returned entries contain application attempts. |
| `APP/sql?details=false&planDescription=false&offset=0&length=20` | Bounded SQL execution listing; follow the correct actual action. |
| `APP/sql/<execution-id>?details=true&planDescription=true` | Plan/operator metrics and linked execution details. |
| `APP/jobs` and `APP/jobs/<job-id>` | Jobs and job stage associations. |
| `APP/stages?details=false` | Stage-attempt overview, avoiding whole-app embedded task data. |
| `APP/stages/<stage-id>?details=false` | **All attempts** for that stage; choose the relevant attempt explicitly. |
| `APP/stages/<stage-id>/<stage-attempt-id>?details=false` | One stage attempt. |
| `APP/stages/<stage-id>/<stage-attempt-id>/taskSummary?quantiles=0,0.5,0.95,1` | Metric distributions; not a success-only partition distribution. |
| `APP/stages/<stage-id>/<stage-attempt-id>/taskList?offset=0&length=50&sortBy=-runtime` | Slowest task attempts first, all statuses unless filtered; paginate for full population. `runtime` is ascending; `-runtime` is descending. |
| `APP/allexecutors` | Active **and dead** executors; `/executors` alone lists active executors. |
| `APP/environment` | Redacted recorded environment/property sets; can still contain sensitive information and does not enumerate all default settings. |
| `ROOT/applications/<base-app-id>/logs` | History Server event logs for all application attempts as ZIP; not executor stdout/stderr. |
| `ROOT/applications/<base-app-id>/<attempt-id>/logs` | History Server event logs for one app attempt as ZIP. |

REST `/executors/<id>/threads` is for an **active** executor and is unavailable through History Server. `/streaming/statistics`, `/streaming/receivers` and `/streaming/batches` describe the DStream streaming context; do not present them as generic Structured Streaming progress APIs. The separate Structured Streaming UI/programmatic progress APIs are described below. [REST docs][M35] [Web UI tabs][UI35]

**Template prerequisites:** authorized access is already established; `curl` is installed; use the approved route/auth mechanism (not a invented Spark bearer-token API); `SPARK_API_ROOT` includes `/api/v1`; `SPARK_APP_PATH`, `SPARK_STAGE_ID` and `SPARK_STAGE_ATTEMPT_ID` come from actual metadata; `SPARK_DIAG_DIR` is an existing private approved directory; raw responses must be reviewed/redacted before model ingestion. If authentication requires additional curl configuration, use the deployment's already-approved method without putting secrets into command text. These are correct URL/parameter templates, not commands executed during this research.

```sh
: "${SPARK_API_ROOT:?Set the authorized monitoring root including /api/v1}"
: "${SPARK_APP_PATH:?Set app ID or app ID/app-attempt ID from metadata}"
: "${SPARK_STAGE_ID:?Select stage ID from the linked job}"
: "${SPARK_STAGE_ATTEMPT_ID:?Select the actual stage attempt ID}"
: "${SPARK_DIAG_DIR:?Set an existing private approved directory}"
umask 077

curl --fail --silent --show-error --get \
  --data-urlencode 'status=completed' --data-urlencode 'limit=20' \
  --output "$SPARK_DIAG_DIR/applications.json" \
  "${SPARK_API_ROOT%/}/applications"

curl --fail --silent --show-error \
  --output "$SPARK_DIAG_DIR/stage-attempts.json" \
  "${SPARK_API_ROOT%/}/applications/$SPARK_APP_PATH/stages/$SPARK_STAGE_ID?details=false"

curl --fail --silent --show-error --get \
  --data-urlencode 'quantiles=0,0.5,0.95,1' \
  --output "$SPARK_DIAG_DIR/task-summary.json" \
  "${SPARK_API_ROOT%/}/applications/$SPARK_APP_PATH/stages/$SPARK_STAGE_ID/$SPARK_STAGE_ATTEMPT_ID/taskSummary"

curl --fail --silent --show-error --get \
  --data-urlencode 'offset=0' --data-urlencode 'length=50' \
  --data-urlencode 'sortBy=-runtime' \
  --output "$SPARK_DIAG_DIR/slow-task-attempts.json" \
  "${SPARK_API_ROOT%/}/applications/$SPARK_APP_PATH/stages/$SPARK_STAGE_ID/$SPARK_STAGE_ATTEMPT_ID/taskList"
```

**Recommendation:** `umask` affects newly created files, not pre-existing permissive exports; choose a new per-run artifact directory/filenames. Fetching the first 50 slow tasks is enough for tail inspection, not for an unbiased full-population distribution. Use summaries plus complete paginated data if recomputing status-filtered/partition-deduplicated quantiles. A 404 from `taskSummary` can mean no retained tasks reported metrics, not that duration/spill were zero. v3.5.7 source returns NotFound in that case. [Stage REST source][ST35]

### 5. Evidence-driven diagnostic workflow

**Recommendation — order of work:**

1. Verify identity, semantics, privacy, completion and telemetry completeness.
2. Locate the slow **end-to-end interval**, then linked SQL/job/stage attempts on the critical path. Account for overlaps, startup/metadata/commit work, failed retries and resource-allocation gaps.
3. Compare task **duration/executor-run distributions** (count, median, p95/max, with population stated), bytes/records, spill, GC, fetch wait, executor/host and launch times. Distinguish same-launch tail behavior from many waves of uniform tasks.
4. Form 2–3 ranked, falsifiable hypotheses from the evidence. For each name supporting measurements, alternative explanations/missing evidence, the smallest semantics-preserving candidate and its predicted metric change. Do not label correlation as proof of a root cause.
5. Run only an approved controlled baseline/candidate experiment. Accept only if the original bottleneck and end-to-end objective improve within observed variability, output checks pass, and resource/cost/failure regressions are disclosed.

The following table is **recommendation/diagnostic inference**, not an upstream guarantee. Metric meanings are grounded in the cited monitoring/UI/source definitions.

| Candidate cause | Supporting completed-run evidence | Confounders / disconfirming evidence / next discriminating probe |
|---|---|---|
| **Data/key/partition skew** | A few successful partitions have much larger input/shuffle records/bytes and duration than the median; the long tail remains after most tasks complete. | Duration skew alone may be host degradation, GC, variable UDF work, fetching, retries, or late task launches. Correlate task duration with bytes/records and key/cardinality distribution; compare executor concentration and repeated runs. Establish the affected operator and whether AQE skew-join rules apply before salting or threshold changes. |
| **Underparallelism / oversized uniform partitions** | Few runnable tasks compared with actual available task slots throughout a long stage; similarly large/slow partitions; most allocated capacity idle; final AQE coalescing or explicit coalesce creates the low task count. | Low task count can be intentional/required (global aggregation, ordered/single-output operation, unsplittable source) or observed capacity may not actually be usable. Check `spark.task.cpus`, resource profiles/GPUs, dependency readiness, available executors and final partitioning. Merely adding executors cannot split a fixed handful of tasks. |
| **Too many tiny tasks / launch overhead** | Many very short tasks in waves, tiny bytes per task, significant launch/deserialization/result overhead; long overall stage despite little useful work per attempt. | Apparent scheduler delay is a residual metric, not the whole stage's pending queue. Check timeline, metadata/file counts and scheduler/driver evidence. Coalescing/reducing partitions can worsen tail/spill or correctness-dependent output layout; benchmark a targeted change. |
| **CPU / expensive per-record work** | High executor-task CPU relative to its runtime (convert ns versus ms), sufficiently sized tasks, low GC/spill/fetch wait; operator/Python/UDF evidence identifies work. | Task CPU is current JVM task-thread measurement in v3.5.7, not whole-host utilization or complete Python/native-worker CPU. Low JVM CPU cannot clear Python UDF work. Obtain relevant worker/process/system profiling only if authorized; preserve code semantics. [Executor source][E35] |
| **GC / memory pressure** | High GC intervals coupled to slow task/executor behavior, spill, memory/GC logs, OOM or executor/container limits. | GC is JVM-wide and can be counted by concurrent task windows; SQL peak execution memory is not full executor/Python/off-heap/container memory. Check actual failure reason, process/container evidence, concurrency and partition sizes before adding heap. [Executor/source metrics][E35] [Metrics][M35] |
| **Spill / oversized working set** | Sort/aggregate/join operator spill and task disk spill correlated with a critical long stage; large per-task inputs or execution-memory structures. | Nonzero spill is not necessarily the dominant cost; memory spill and disk spill are different representations, not additive bytes. Check the slow-task time, disk evidence and concurrent working sets. More parallel partitions can lower per-task pressure but add shuffle/scheduler cost; more tasks per executor may increase pressure. [UI definitions][UI35] |
| **Input/output or metadata I/O** | Scan/metadata time, file counts, task read/output bytes and durations, write/task/job commit metrics; matching filesystem/object-store/client errors/latency. | Bytes prove volume, not the limiting device/service. A low CPU/run ratio also includes waiting/GC/Python effects. Distinguish list/open/scan/read, shuffle, actual output writes and commit. Changing file layout or output file count has downstream semantics/operational costs. [SQL metrics][UI35] |
| **Shuffle blocking / fetch failures** | Significant blocking fetch wait in the actual slow tasks; large remote shuffle; matching failure messages, removed executor events or shuffle-service/storage/network evidence. | `fetchWaitTime` measures blocking on remote data, not all network transfer and not proof the network is slow. Producer storage, service load, lost blocks/executors, GC or topology can be causal. Correlate source executor/host and failure/retry chronology before changing timeout/retry/connection knobs. [Metrics][M35] |
| **Scheduler/resource contention** | Long stage-to-launch gaps, pending waves, allocation ramp-up, concurrent jobs/pools, locality/resource restrictions or driver evidence; execution is not keeping available slots busy. | UI per-task “scheduler delay” is a clamped residual after launch and does not directly measure how long an unlaunched task sat pending. Show stage/executor/task timeline and actual resources; do not equate one residual with cluster queue wait. [Delay source][ASU35] [Scheduling][SCHED35] |
| **Retries, speculation, executor losses** | Failed/killed attempt counts, duplicate task indices/partitions, `speculative=true`, stage attempt changes, executor removals and correlated errors. | Slow-host duplicates are not necessarily data skew; failed attempts can distort distributions and multiply input/shuffle work. First separate recovery overhead from successful useful execution. Report all attempts for cost/failure analysis and a defined successful population for partition-shape analysis. [Config speculation][CONF35] [REST model][AM35] |

#### Metrics caveats the skill should enforce

- **Wall clock versus summed task time:** tasks run concurrently; UI “total time across all tasks” and summed executorRunTime are worker-time totals, not stage/application elapsed time. Do not sum overlapping stages/SQL executions or claim a speedup from worker-time alone. [UI][UI35] [Metrics][M35]
- **Metric scope and units:** executorRunTime includes shuffle fetching; executorCpuTime is in **nanoseconds**, whereas executorRunTime/GC/fetch wait are **milliseconds**; shuffle write time is **nanoseconds**. Ratios require converting units and stating the task population. Fetch wait is included in executor runtime; adding it again double-counts. [Metrics][M35]
- **GC attribution:** v3.5.7 obtains total JVM GC time via garbage-collector MXBeans and subtracts a task's start reading from an end reading. Concurrent tasks on the same JVM can include the same GC interval. Sum of task GC durations is therefore not independent JVM wall-GC time, and high task GC is not proof that that task alone created the pressure. [Executor source][E35]
- **CPU attribution:** v3.5.7 uses `getCurrentThreadCpuTime` for the task thread; absent thread CPU support can produce zero. Treat whole-host/native/Python CPU as unavailable unless separately measured. [Executor source][E35]
- **Scheduler delay is a residual:** v3.5.7 computes `max(0, duration - executorRunTime - deserializeTime - serializeTime - gettingResultTime)` for a finished task with metrics. Its launch-based scope is not all pre-launch pending time or a causal scheduler profiler. [AppStatusUtils][ASU35]
- **Distribution population:** `taskSummary` is recorded task-attempt metrics for the stage attempt, not an automatically deduplicated successful partition sample. v3.5.7 counts retained tasks with valid executor runtime and has no status-filter parameter for this endpoint. Retained/incomplete/failed/killed/speculative attempts and missing metric-bearing tasks need checking; independently compute a success-only distribution when required. [Store source][STORE35] [Stage REST][ST35]
- **One metric cannot prove network bottleneck:** fetch wait excludes transfer that overlaps useful processing and is only blocking remote-shuffle time. Even a high value needs causal supporting evidence; low fetch wait does not prove no significant network traffic. [Monitoring][M35]
- **Spill/peak memory:** memoryBytesSpilled is in-memory/deserialized size and diskBytesSpilled is disk/serialized size; do not add them or infer a leak. Peak execution memory only covers tracked internal execution structures, not all JVM, storage, Python, native, or container memory. Executor peak metrics are sampled/heartbeat-based and event-log peak persistence is opt-in. Missing or zero recorded peaks do not prove absence of pressure. [UI][UI35] [Monitoring][M35] [Config][CONF35]
- **SQL operators versus stages:** whole-stage codegen fuses work; operator metrics have operator-specific aggregation and boundaries. One slow fused stage can contain multiple operators. Plans plus stage metrics identify hypotheses, not automatically accurate per-operator wall-time decomposition. [UI][UI35]
- **Incomplete evidence:** status UI/API retention, log loss, compaction, listener errors or incomplete completion evidence can create partial reports. Cite missing population/scope instead of interpreting absence as zero. [Monitoring][M35] [Config][CONF35]

### 6. Controlled reruns and benchmark acceptance

The following is **recommended experimental design**, not a universal Apache-provided benchmark recipe. It follows from Spark's lazy actions/materialized cache, adaptive runtime planning, changing allocations and different write/commit boundaries. [UI][UI35] [AQE][AQE35] [Scheduling][SCHED35]

1. **Freeze the workload:** same immutable input snapshot and schema/manifest, joins' lookup snapshots, predicate/date range, source options, dependency artifacts and external services where relevant. “Same pathname” is insufficient if files/tables changed. Compare the same actual terminal action and sink/commit behavior, not baseline write versus candidate count.
2. **Freeze unrelated treatment:** same Spark/distribution/JVM/Python/Scala versions, cluster type/region/hardware/storage path class, executor/task resources, scheduling/concurrency and relevant effective config. Record base code commit/build plus exact candidate patch/commit and config delta. For config-only experiments use the same code artifact/commit; for code changes the candidate revision necessarily differs, but all unrelated code/config must remain fixed. A simultaneous engine upgrade, bigger cluster, warmer cache and rewrite cannot isolate which change helped.
3. **Define cache regimes explicitly:** cold and warm are separate experiments. Match application/session lifetime, persisted-data materialization, JVM/JIT startup, metadata/OS/local-disk/object-store caching to the extent controllable. If a warmup is used, use the same warmup workload/count and exclude it consistently. Do not flush shared caches or delete user data without authorization. Disclose unobservable remote-cache differences.
4. **Use comparable actual resources:** record executor allocation over time, not just requested maxima. If dynamic allocation remains enabled, keep policy equal and report its differing allocation/cost as part of the outcome. Do not silently disable it in production merely to make a benchmark easier. [Scheduling][SCHED35]
5. **Repeat/interleave:** establish baseline repeatability first; then repeat both baseline and candidate, interleaving or randomizing order to reduce time-of-day/cache bias. A practical starting recommendation is at least three comparable runs each; more if variability is large. Report all samples, median and spread; do not claim meaningful p95 from a handful of reruns or cherry-pick the fastest candidate. Mark anomalies and investigate rather than deleting unfavorable runs without explanation.
6. **Measure distinct objectives:** end-to-end elapsed latency at defined boundaries; SQL/job/stage critical-path changes; spill/shuffle/tail/failure changes; resource usage/cost. For cost prefer actual billed/container allocation data, including driver/executor duration, memory/storage/network charges where relevant. A declared proxy such as allocated core-seconds is not dollars. Task runtime sum can describe work but is not equivalent to billed allocation time, idle capacity or end-to-end latency.
7. **Keep the timing region honest:** lazy transformation construction and EXPLAIN are not the job runtime; the terminal action must finish, including the representative output commit. Run correctness comparison outside the timing interval. Never let validation of an unmaterialized DataFrame inadvertently warm the cache for only one timed variant.
8. **Require semantics proof:** full-output equivalence/invariants and sink/partition contract checks, as described below; also failures/retries are not worse. Reduced row count/columns, changed null/duplicate handling, changed nondeterministic outputs or dropped bad/missing inputs are not valid optimizations unless explicitly authorized as changed semantics.
9. **Report and select:** state baseline/candidate IDs and version/code/config/resource deltas, sample runtimes, relative change `(baseline median - candidate median) / baseline median`, variation, cost/proxy, target metric changes, exact correctness coverage and remaining caveats. Improvement smaller than ordinary baseline variation is inconclusive. A latency gain with higher cost can be acceptable only under the user's objective, not as an unqualified efficiency claim.
10. **Promotion boundary:** an offline scenario test can validate the skill's choices/guardrails but cannot prove real Spark performance. A successful small fixture validates that fixture, not a petabyte job. Until representative controlled executions and semantics checks finish, label the candidate **proposed/unverified**, not optimized/proven.

### 7. Output-equivalence checks

#### Recommended contract-first checklist

- **Schema:** column names/order/types, decimal precision/scale, struct/array/map shape, nullability/metadata where contractual; partition column typing and timezone/ANSI semantics. Do not silently align/widen/cast away mismatches. Generic helpers may deliberately ignore parts of the schema.
- **Multiplicity:** compare multisets/bags, not just distinct sets or counts. A baseline `[a,a,b]` and candidate `[a,b,b]` have the same row count and distinct set but different results.
- **Nulls:** preserve null versus missing/empty and null-key join/filter/group semantics. Spark `=` with null is not a null-safe equality; set operators compare two null values as equal. [Null semantics][NULL35]
- **Numeric values:** integer/decimal exactness, overflow and rounding semantics; for floating outputs use exact comparison by default, or pre-agreed domain-specific `atol`/`rtol` only where changing reduction order legitimately permits numerical variation. Do not invent a tolerance after seeing a bad diff. Treat NaN, infinities, null and signed-zero/bit-level requirements explicitly. Spark SQL treats NaN as equal to NaN and as a normal join/group key; SQL equivalence is not an IEEE bit-payload comparison. [Datatype semantics][DT35]
- **Ordering/nondeterminism:** Spark DataFrame row order is not guaranteed without explicit sorting. Preserve any real ORDER BY/top-N/window tie-breaking contract; do not compare filesystem/partition traversal order if it was never contractual. `first` after shuffle and `monotonically_increasing_id` are documented nondeterministic/partition-dependent examples. Freeze allowable time/random/external inputs or use an approved semantic oracle; repartitioning is unsafe if externally consumed generated IDs or arbitrary-first choice are part of the expected output. Do not mask nondeterminism by deleting those columns from checks. [Testing API][TEST35] [First][FIRST35] [Generated ID][ID35]
- **Partitioned output:** read complete outputs with equivalent source options/schema and root/basePath so path-derived partition columns are present; verify logical rows plus partition coverage/values and contractually required physical layout. Parquet partition discovery can omit a parent partition column when only a partition subdirectory is read unless `basePath` is set. Byte checksums or exact `part-*` filenames are not general logical equality: partition/task ordering, file count or encoding may differ under a legitimate optimization. If consumers require file counts/naming/bucketing/sort order, explicitly test that physical contract as well. [Partition discovery][PQ35]
- **Write-side semantics:** ensure all intended writes/commits happened once and to the approved destination; compare output row counts and per-partition/key counts, duplicates/null counts and business invariants; account for JDBC/custom side effects. A content-equal DataFrame alone does not prove transactional sink behavior.

#### Source-checked distributed exact multiset comparator example

**Fact:** `DataFrame.exceptAll` preserves duplicates, is equivalent to SQL `EXCEPT ALL`, and matches columns **by position, not name**. It was introduced in 2.4.0. [API][EXCEPT35]

**Recommendation/example:** for existing **materialized bounded** `baseline_output` and `candidate_output` DataFrames, identical contract-approved schemas and types supported by set operations, use both directional differences. This triggers distributed comparison actions and should run outside benchmark timing. It does not collect complete output rows to the driver, does not check file-layout/side-effect contracts, and uses Spark SQL equality (not bitwise floating equality):

```python
## Pre-existing DataFrames loaded from the two isolated committed outputs.
if baseline_output.isStreaming or candidate_output.isStreaming:
    raise ValueError("Batch output comparison requires bounded materialized outputs")
if baseline_output.schema != candidate_output.schema:
    raise AssertionError("Output schemas differ; investigate without implicit casts")
if baseline_output.exceptAll(candidate_output).limit(1).count() != 0:
    raise AssertionError("Baseline contains rows/multiplicities absent from candidate")
if candidate_output.exceptAll(baseline_output).limit(1).count() != 0:
    raise AssertionError("Candidate contains rows/multiplicities absent from baseline")
```

Use an explicit separately documented comparator for unsupported types or domain-approved floating tolerance; do not serialize arbitrarily to JSON or deduplicate to make set operations pass. Approximate row matching must preserve duplicate multiplicities and null semantics; a keyed join is not enough if keys are nonunique. Counts/hashes/samples are useful preliminary checks, not exact equivalence proof (hashes can collide, counts omit values, and samples miss rare differences).

#### Small-fixture helper version caveats

`pyspark.testing.assertDataFrameEqual` exists since 3.5.0. In 3.5.7 its defaults are unordered rows plus `rtol=1e-5`, `atol=1e-8`; those defaults are **not exact equality**. Its source collects Spark DataFrames to Python lists, rejects streaming DataFrames, and schema comparison ignores nullable flags. Thus use it only for bounded small fixtures with deliberately specified tolerances/ordering and a separate strict schema-contract check when needed; never apply it casually to large production outputs or share its raw row diff. [3.5.7 testing API][TEST35] [Testing implementation][TESTSRC35]

4.0.1 adds options including `ignoreNullable` (default true), column order/name/type ignoring and diff limits. Do not copy 4.x arguments into a 3.5 skill example or weaken equality via ignore options for convenience. Explicitly test special floating cases using an independent expected-value policy; generic float tolerance helper behavior is not sufficient evidence for all NaN/infinity cases. [4.0.1 helper signature][TEST40]

### 8. Streaming guardrails (out-of-scope detection, not batch tuning)

**Recommendation:** when `isStreaming`, readStream/writeStream, checkpoint/state operators, query ID/run ID, or micro-batch history appears, **leave the batch optimization path**. Diagnose scope and explain which streaming-specific evidence/approval is needed. A bounded trigger such as AvailableNow is still a streaming query with offsets/checkpoint/sink semantics; a completed micro-batch is not an independent batch application whose state may be reset freely.

**Verified facts:** Structured Streaming progress is available through `StreamingQuery.lastProgress`/`recentProgress` (Python properties; Scala/Java accessors) and asynchronous `StreamingQueryListener`; progress includes offsets, counts, rates, batch durations and state/watermark data. The Structured Streaming UI supports micro-batch queries and shows batch/operation durations, state rows/memory, watermark gaps and rows dropped by watermark. Metrics reporting through Dropwizard requires enabling `spark.sql.streaming.metricsEnabled` for subsequently started queries. Retain exported progress if needed after the query/app is gone; do not assume `lastProgress` is a complete historical archive. [Structured Streaming guide][SS35] [Structured Streaming UI][UI35]

Checkpoint recovery stores progress/offsets/state. The pinned guide restricts changing sources, sink type/path and stateful schemas across restart; `spark.sql.shuffle.partitions`, state store provider and multiple-watermark policy are documented as nonmodifiable with an existing checkpoint in the relevant stateful context. `foreachBatch` is at-least-once by default and requires implemented batch-ID deduplication/idempotency for stronger guarantees; it is not supported by continuous processing. [Recovery/additional information/foreachBatch][SS35]

**Recommendations:**

- Never discard, edit or reuse a production checkpoint for a tuning experiment; never alter watermark/state key/schema/output mode/offset consumption to obtain a faster number while claiming preserved semantics.
- Do not prescribe changing stateful shuffle partition count with the same checkpoint, or batch AQE/coalesce/salting advice without verifying that version's streaming support and state/sink requirements.
- Compare the same source offset ranges/replay, event-time distribution, trigger schedule, initial state, and approved isolated checkpoint/sink setup. “More processedRowsPerSecond” may reflect different batches or less work, not equivalent semantics or lower end-to-end latency.
- Measure backlog/lag, input and processing rates, trigger/batch durations, state size, watermark behavior/late-data drops, sink commit/duplicates, restart recovery and idempotency, not only a fast micro-batch. Slower watermark progression or extra dropped rows is a correctness risk.
- A copy of a checkpoint does not itself make replay and external sink effects safe; require a connector-aware replay/recovery plan. If production state cannot be reproduced safely, label performance validation incomplete and do not launch a competing writer.

### 9. Concrete dry-run decision cases

These are **hypothetical fixtures for testing skill decisions**, not real application evidence. Expected responses should preserve the uncertainty/action boundaries; the skill does not need a Spark cluster to demonstrate these decisions.

#### A. Missing event logs

Input: existing batch ETL, Spark 3.5.7, reported duration 27 minutes, completed yesterday; no saved UI/REST exports; event logging was false; user supplies only code and a new EXPLAIN showing SortMergeJoin. Production writer uses overwrite.

Expected: accept the 27-minute observation without rerunning merely to confirm it; state runtime bottleneck and gains unproven. Check if independent logs/metrics survive; derive only labeled code/plan hypotheses. Do **not** conclude skew, raise executor memory, broadcast based on an absent measured build size, “recover” history by enabling logging now, or rerun overwrite. Supply a safe future baseline plan (logging before launch, immutable inputs, isolated authorized output, real write/commit action, effective config capture, equivalence/repetitions). If rerun is unapproved, no performance proof is claimed. [Logging boundary][M35] [Write hazard][SAVE35]

#### B. Misleading initial plan

Input: `EXPLAIN FORMATTED` before action says `AdaptiveSparkPlan isFinalPlan=false`, SortMergeJoin, shuffle partitions 200. Completed execution for the actual output write has `isFinalPlan=true`, BroadcastHashJoin and 24 reducer tasks, with 80% of observed end-to-end time in metadata listing and output job commit, and no long reducer tail.

Expected: prefer the completed action's plan/metrics; reject “switch SortMergeJoin to broadcast” and “200 partitions are too many” as unsupported/obsolete diagnoses. Investigate metadata/file/sink commit evidence on the real critical path, explain that final broadcast does not erase earlier shuffle work, and propose no blanket tuning. [AQE][AQE35] [Plans][AP35] [SQL metrics][UI35]

#### C. Slow attempts do not establish skew

Input: stage 14 attempt 0 has 120 equal-sized partitions; executor e7 dies; a shuffle fetch failure occurs; stage 14 attempt 1 succeeds. Export includes both attempts and speculative/killed copies; slow attempts cluster on e7 and record high fetch wait.

Expected: separate app/stage/task attempts; use all attempts for recovery overhead/cost and a clearly defined successful population for partition distribution. Inspect executor failure and producer/service evidence; do not call byte-balanced partitions data skew solely because task runtimes differ or diagnose “network bandwidth” solely from fetch wait. Never increase retry/timeout settings as a substitute for explaining the failure. [Attempt IDs][AM35] [Fetch-wait meaning][M35]

#### D. Faster but not equivalent

Input: candidate median is 20% faster; both outputs have 1,000,000 rows; candidate drops one duplicated `(customer, NULL)` row and duplicates another row; file counts differ; author used `distinct`-based comparison and helper default float tolerance.

Expected: reject “equivalent”/promotion. Require schema plus two-way multiset comparison, null-safe treatment, approved numeric tolerance/special-value checks, and complete logical partitioned-output reading. Distinct/row-count equality is insufficient. File-count change is acceptable only if not a contractual physical requirement. [ExceptAll][EXCEPT35] [Nulls][NULL35] [Testing defaults][TEST35]

#### E. Streaming state trap

Input: a Spark 3.5.7 stateful Structured Streaming aggregation has an existing production checkpoint, `spark.sql.shuffle.partitions=200`, late-data watermark and `foreachBatch` JDBC output. A proposed “optimization” sets shuffle partitions to 32, deletes the checkpoint and reruns.

Expected: detect streaming, reject that batch path and destructive action. Preserve source offsets/state/watermark/sink guarantees; request a safe connector-aware isolated replay/recovery plan and progress metrics. Explain checkpoint/config restrictions and at-least-once `foreachBatch`, without promising exactly-once from merely having a checkpoint. [Structured Streaming][SS35]

### 10. Small hypothetical completed-run smoke fixture

Use this self-contained evidence payload to exercise the skill's hypothesis, safe experiment, and acceptance behavior without inventing a real Spark run:

```text
workload: existing PySpark batch left join, followed by Parquet partitioned write
runtime: Apache Spark 3.5.7; immutable input snapshot S42; commit base-a1
resources: fixed 8 executors x 4 cores; spark.task.cpus=1; no concurrent jobs
cache: cold application for every run; no persisted input; remote cache uncontrolled, disclosed
logging: enabled before run; complete History Server evidence; output isolated
semantics: all left rows preserved, including duplicates and NULL customer keys;
           exact integer/decimal output, no required global order;
           partition column business_date required; no part-file count/name contract
actual output execution: SQL execution 5 -> jobs 8,9 -> stages 20/0,21/0
initial plan: AQE isFinalPlan=false, SortMergeJoin
final plan: AQE isFinalPlan=true, SortMergeJoin; 128 reducer partitions
settings: spark.sql.adaptive.enabled=true; spark.sql.adaptive.skewJoin.enabled=false
stage 21/0: 128 successful tasks, 0 failed/killed/speculative attempts
            median 7s / 24MiB shuffle read; max 150s / 1.8GiB shuffle read
            4 long-tail tasks carry the largest shuffle partitions;
            max GC 0.5s; max blocking fetch wait 0.8s; no executor losses;
            shuffle keys are business join keys; measured top-key counts confirm concentration
end-to-end baseline seconds: [212, 207, 215]; sink commit about 9s in each
baseline allocation: fixed same resources throughout; cost has only allocated-core-seconds proxy
```

**Expected recommendation (not a proven fix):** dominant hypothesis is join partition/key skew, supported by bytes, duration, tail shape and top-key counts; underparallelism/GC/fetch-loss are weaker given this supplied evidence. Verify join eligibility and the exact AQE settings, then propose one controlled candidate enabling the version-supported skew-join optimization rather than blanket salting/broadcast/heap increase. Warn of split/replication and resource overhead; predict reduced worst-partition/tail duration, not necessarily fewer total shuffle bytes. The docs' skew decision requires a partition exceed **both** the configured median factor and byte threshold. For the pinned defaults (5× median, 256MB), 1.8GiB versus 24MiB satisfies both, but successful optimization still requires compatible plan/operator conditions. [AQE skew docs][AQE35]

**Acceptance branch supplied to scenario:** candidate fixed-resource cold-write samples `[148,151,149]`; no failures; slow-tail max 80s; full strict-schema, two-way `exceptAll`, null/duplicate and `business_date` partition checks pass. Expected response uses the actual samples: baseline median **212s**, candidate median **149s**, approximately **29.7% lower median latency**, calculated as `(212-149)/212`. It must not confuse task time with latency or call the allocated-core-seconds proxy currency. These synthetic numbers exercise reasoning only; no real gain has been measured.

**Rejection branch:** same timings but a NULL-key row is lost or numeric policy differs → reject promotion despite speed. **Inconclusive branch:** no candidate execution evidence or correctness artifact → report a proposed candidate plus required verification, not a measured improvement. **Cost-tradeoff branch:** candidate instead uses 16 executors → label changed-resource latency result and require cost/like-for-like comparison; do not attribute improvement solely to AQE.

### Upstream sources inspected

[URLs are pinned to inspected releases/tags; select the actual job's matching release when applying.]

[M35]: https://spark.apache.org/docs/3.5.7/monitoring.html
[M40]: https://spark.apache.org/docs/4.0.1/monitoring.html
[UI35]: https://spark.apache.org/docs/3.5.7/web-ui.html
[CONF35]: https://spark.apache.org/docs/3.5.7/configuration.html
[SEC35]: https://spark.apache.org/docs/3.5.7/security.html
[EX35]: https://spark.apache.org/docs/3.5.7/sql-ref-syntax-qry-explain.html
[DFEX35]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.explain.html
[AQE35]: https://spark.apache.org/docs/3.5.7/sql-performance-tuning.html#adaptive-query-execution
[SS35]: https://spark.apache.org/docs/3.5.7/structured-streaming-programming-guide.html
[SCHED35]: https://spark.apache.org/docs/3.5.7/job-scheduling.html
[SAVE35]: https://spark.apache.org/docs/3.5.7/sql-data-sources-load-save-functions.html#save-modes
[PQ35]: https://spark.apache.org/docs/3.5.7/sql-data-sources-parquet.html#partition-discovery
[NULL35]: https://spark.apache.org/docs/3.5.7/sql-ref-null-semantics.html
[DT35]: https://spark.apache.org/docs/3.5.7/sql-ref-datatypes.html#nan-semantics
[EXCEPT35]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.exceptAll.html
[TEST35]: https://spark.apache.org/docs/3.5.7/api/python/reference/api/pyspark.testing.assertDataFrameEqual.html
[TEST40]: https://spark.apache.org/docs/4.0.1/api/python/reference/api/pyspark.testing.assertDataFrameEqual.html
[TESTSRC35]: https://spark.apache.org/docs/3.5.7/api/python/_modules/pyspark/testing/utils.html
[FIRST35]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.functions.first.html
[ID35]: https://spark.apache.org/docs/3.5.7/api/python/reference/pyspark.sql/api/pyspark.sql.functions.monotonically_increasing_id.html
[AR35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/api/v1/ApiRootResource.scala
[AM35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/api/v1/api.scala
[AL35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/api/v1/ApplicationListResource.scala
[OA35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/api/v1/OneApplicationResource.scala
[ST35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/api/v1/StagesResource.scala
[STORE35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/AppStatusStore.scala
[ASU35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/status/AppStatusUtils.scala
[E35]: https://github.com/apache/spark/blob/v3.5.7/core/src/main/scala/org/apache/spark/executor/Executor.scala
[SE35]: https://github.com/apache/spark/blob/v3.5.7/sql/core/src/main/scala/org/apache/spark/sql/execution/SQLExecution.scala
[SL35]: https://github.com/apache/spark/blob/v3.5.7/sql/core/src/main/scala/org/apache/spark/sql/execution/ui/SQLAppStatusListener.scala
[AP35]: https://github.com/apache/spark/blob/v3.5.7/sql/core/src/main/scala/org/apache/spark/sql/execution/adaptive/AdaptiveSparkPlanExec.scala
