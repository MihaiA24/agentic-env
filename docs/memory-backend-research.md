# Memory backend for multi-project OMP — deep research

**Question:** One OMP install serves many projects. Related projects should share memory; unrelated ones must stay isolated. Which long-term memory backend fits, and what does real usage say?
**Date:** 2026-08-11. **Method:** two background librarian agents read primary sources (pinned commits, official docs, committed benchmark files) and field evidence (issue trackers, third-party reports). Snapshot: OMP `e5ebb2aee` (v17.2.14) · Hindsight `96bd69c` (0.9.0) · mem0 `c427a45` (2.0.17/18) · agentmemory `2973e4e` (0.9.28/29). Tags: **[1P]** vendor-owned, **[3P]** unaffiliated.

## TL;DR

1. **No independent benchmark exists for any candidate.** Every headline number is vendor-published or co-authored. A targeted search confirmed the absence. The only 3P academic result tests a *custom* Letta skill, not stock Letta ([arXiv:2604.12948](https://arxiv.org/abs/2604.12948)).
2. **Hindsight is the only candidate that can express the multi-project requirement today.** It has hard bank isolation plus tag unions (`tags=[A,B]`, `tags_match="any_strict"`) for a chosen related set, and it already has a **native OMP backend** (`memory.backend=hindsight`).
3. **Mnemopi cannot.** The name `per-project-tagged` is misleading, because no tag-filtered recall exists. The topology is the current-project bank plus one shared global bank, with nothing in between. `polyphonicRecall` fuses voices *within* one bank, never across banks.
4. **agentmemory's high claims don't survive the audit** (§Claims). Its shipped Pi integration recalls *globally*: it computes the project tag but never passes it on search. As shipped, it is not project-isolated.
5. **mem0 OSS is not a candidate for OMP-primary.** It has no native backend, its official MCP is hosted-platform-only, and the strongest production audit found **97.8% junk rows**.
6. **Bake-off arms: Hindsight vs Mnemopi.** No candidate earned adoption on paper. Production-trust tops out at *medium* (Hindsight).

## Multi-project scope matrix

| Backend | Isolate unrelated | Share a chosen related set | Global recall | Boundary reality |
|---|---|---|---|---|
| **Mnemopi** | yes — bank per cwd ([config.ts#L118-167](https://github.com/can1357/oh-my-pi/blob/e5ebb2aee0c3b9fe41c39a310c01398b62313c25/packages/coding-agent/src/mnemopi/config.ts#L118-L167)) | **no** — no tag-filtered recall; only current bank + one global bank ([config.ts#L111-167](https://github.com/can1357/oh-my-pi/blob/e5ebb2aee0c3b9fe41c39a310c01398b62313c25/packages/coding-agent/src/mnemopi/config.ts#L111-L167)) | one `global` bank | No "projects A+B but not C". Polyphonic recall is within-bank ([polyphonic-recall.ts#L174-221](https://github.com/can1357/oh-my-pi/blob/e5ebb2aee0c3b9fe41c39a310c01398b62313c25/packages/mnemopi/src/core/polyphonic-recall.ts#L174-L221)) |
| **Hindsight** | yes — banks are the recall boundary; strict tag modes exclude untagged ([recall.mdx#L175-242](https://github.com/vectorize-io/hindsight/blob/96bd69c7bd1ca76824faf9de388f9eac080155e7/hindsight-docs/docs/developer/api/recall.mdx#L175-L242)) | **yes** — retain with project tags, recall `tags=[A,B]` `any_strict`; stock OMP preset passes only the current tag, sibling unions need custom tag selection | omit tags in a shared bank | One recall call = one bank; cross-bank = client-side merge |
| **mem0 OSS** | collections; ids are filters not authz ([main.py#L1255-1306](https://github.com/mem0ai/mem0/blob/c427a453a89c5a3fee73cdb2e4c4df6a651e1692/mem0/memory/main.py#L1255-L1306)) | yes logically — metadata filters `in/AND/OR/NOT` | only within a required id scope | **No native OMP backend; official MCP = hosted platform, data in Mem0 account** ([mem0-mcp.mdx](https://github.com/mem0ai/mem0/blob/c427a453a89c5a3fee73cdb2e4c4df6a651e1692/docs/platform/mem0-mcp.mdx#L9-L34)) |
| **agentmemory** | only via separate `--data-dir` instances | search accepts one exact `project`, but **the Pi extension omits it — auto-recall is global, uncapped** ([pi/index.ts#L260-299](https://github.com/rohitg00/agentmemory/blob/2973e4ec4c40d323a08daa34220118010e73a2c3/integrations/pi/index.ts#L260-L299)) | yes (that's the problem) | `AGENT_SCOPE=isolated` isolates *agents*, not projects |

## Claims audit — advertised vs what it actually is

| Claim | Reality | Source |
|---|---|---|
| agentmemory "95.2% LongMemEval" | retrieval-only R@5, "not end-to-end QA" — their own caveat | [LONGMEMEVAL.md#L54-70](https://github.com/rohitg00/agentmemory/blob/2973e4ec4c40d323a08daa34220118010e73a2c3/benchmark/LONGMEMEVAL.md#L54-L70) [1P] |
| agentmemory "92% fewer tokens" | one example: 240 observations, 20 queries, 1,571 vs 19,462 *estimated* tokens | [REAL-EMBEDDINGS.md#L4-20](https://github.com/rohitg00/agentmemory/blob/2973e4ec4c40d323a08daa34220118010e73a2c3/benchmark/REAL-EMBEDDINGS.md#L4-L20) [1P] |
| agentmemory "$10/yr, $0 local" | vendor cost model; local embeddings NOT default (`EMBEDDING_PROVIDER=local` required) | [config.ts#L266-278](https://github.com/rohitg00/agentmemory/blob/2973e4ec4c40d323a08daa34220118010e73a2c3/src/config.ts#L266-L278) [1P] |
| mem0 "94.4% LongMemEval" | managed platform only, "proprietary optimizations not available in the open-source SDK" — verbatim README | [README#L45-61](https://github.com/mem0ai/mem0/blob/c427a453a89c5a3fee73cdb2e4c4df6a651e1692/README.md#L45-L61) [1P] |
| Hindsight "91.4%, independently reproduced" | co-authored paper, not 3P; current committed run 94.6% — at **avg 43,624 context tokens/query** | [results-manifest.json#L195-209](https://github.com/vectorize-io/agent-memory-benchmark/blob/62364d7ead2dc1a7225d6daf4ae23f303b925b40/results-manifest.json#L195-L209) [1P] |
| all | LongMemEval measures chat memory (extraction, multi-session, temporal, updates, abstention) — not coding-repo decision recall or project isolation | [LongMemEval README](https://github.com/xiaowu0162/LongMemEval) [3P] |

## Field evidence (real usage, mostly failure telemetry)

| Tool | production-trust | Strongest 3P reports |
|---|---|---|
| **Hindsight** | **medium** | RSS →1 GB/hr ([#996](https://github.com/vectorize-io/hindsight/issues/996)); `forget` 404s IDs that `get_memory` returns ([#2523](https://github.com/vectorize-io/hindsight/issues/2523)); integration deleted all stored turns on resume ([hermes#6602](https://github.com/NousResearch/hermes-agent/issues/6602)); silent no-memory when embedded dep missing ([hermes#7718](https://github.com/NousResearch/hermes-agent/issues/7718)). 0.09 open:closed, 42 h median response; integration pkg moved 0.0.5→0.2.1 in 4 days |
| **Mnemopi** | low | same-cwd sessions split across two banks by git-root drift ([omp#2412](https://github.com/can1357/oh-my-pi/issues/2412) — fixed: derivation now cwd-based + legacy rescue); macOS arm64 embeddings silently 0 ([omp#3054](https://github.com/can1357/oh-my-pi/issues/3054)); consolidation never ran, errors swallowed ([#2320](https://github.com/can1357/oh-my-pi/issues/2320)/[#2322](https://github.com/can1357/oh-my-pi/issues/2322)). ~3 min median maintainer response; no external reviews exist at all |
| **agentmemory** | low | Docker volume writes buffered in RAM, wiped on restart ([#301](https://github.com/rohitg00/agentmemory/issues/301)); cwd-dependent stores "vanish" ([#303](https://github.com/rohitg00/agentmemory/issues/303)); 3-node graph query returned 22,514 chars ([#1171](https://github.com/rohitg00/agentmemory/issues/1171)); Codex worktrees fragment projects ([#515](https://github.com/rohitg00/agentmemory/issues/515)). **0.91 open:closed** (233/255), single-owner (115 vs 9 commits). 26.9K stars ≠ deployments; competitor audit ([akitaonrails](https://github.com/akitaonrails/ai-memory/blob/main/docs/issues-agentmemory.md), 3P-competitor) catalogs 137 GB runaway log, 20-min allocation exhaustion |
| **mem0 OSS** | low | 32 days production, 10,134 rows → **97.8% junk** incl. hallucinated profiles + re-ingestion feedback loop ([#4573](https://github.com/mem0ai/mem0/issues/4573)); silent duplicate rows under concurrency ([#6515](https://github.com/mem0ai/mem0/issues/6515)); fork-to-deploy hygiene gaps ([#5339](https://github.com/mem0ai/mem0/issues/5339)) |
| Letta | medium | only genuine 3P academic result (custom skill: 73.7% vs 53.5%, [arXiv:2604.12948](https://arxiv.org/abs/2604.12948)) — but it's a full agent runtime, second-owner violation; compaction wiped history ([#3270](https://github.com/letta-ai/letta/issues/3270)) |
| Zep/Graphiti | low | 3-week **silent** ingest outage, all episodes unrecoverable ([graphiti#1751](https://github.com/getzep/graphiti/issues/1751)); 1.25 open:closed |

The only documented multi-project cases in the wild are **negative** (agentmemory worktree fragmentation #515, Mnemopi bank drift #2412). Nobody has published a working deployment of any of these that shares memory across related projects and isolates unrelated ones.

## OMP wiring facts (from source, pinned)

- `memory.backend`: `off | local | hindsight | mnemopi`. Hindsight is already first-class ([settings-schema.ts#L2628-2917](https://github.com/can1357/oh-my-pi/blob/e5ebb2aee0c3b9fe41c39a310c01398b62313c25/packages/coding-agent/src/config/settings-schema.ts#L2628-L2917)). The resolver selects exactly one backend, so the one-owner rule holds by construction.
- OMP's Hindsight wiring caps recall at **1,024 tokens**, overriding Hindsight's 4,096 default. It retains every 3 turns as a full-session upsert. Retain normally costs one LLM call per 3,000-char chunk. `retain_extraction_mode=chunks` with observations off is the documented zero-LLM mode.
- Mnemopi knobs that matter: `scoping` (`global|per-project|per-project-tagged`), `recallLimit=8`, `injectionTokenLimit≈5000`, first-turn-only auto-recall, `retainEveryNTurns=4`, `llmMode=smol`, `noEmbeddings`. The full table is in the scoping agent report.
- Infra: Mnemopi is in-process SQLite with zero services. Hindsight is one Docker container that holds an API, embedded PG/pgvector and embedding/reranker models, plus an LLM key or local model. agentmemory is a separate service with KV/indexes. mem0 OSS is SDK only, and its default providers are OpenAI.

## Local findings (this machine, 2026-08-11)

- The `dotfiles` bank has `memory_embeddings` populated, so **#3054 (arm64 zero-embeddings) is NOT our failure mode**. ~~The 4/4 failure stands as genuine recall quality~~ **Corrected by probe forensics (below): it is a retention gap, not a ranking failure.**
- 160+ `omp__*` benchmark-residue banks confirmed under `~/.omp/agent/memories/mnemopi/banks/` (the parked 458 MB sweep).

## Decision

**Bake-off arms narrowed to two: Hindsight (native backend, per-project banks + tag unions) vs Mnemopi (incumbent control).** mem0 OSS is eliminated (no OMP path, junk-corpus evidence). agentmemory is eliminated (shipped recall is not project-scoped, and its claims failed the audit).

Endpoints, registered before any trial data: replay the 4 failed decision-recall probes on both arms; run cross-project leakage probes, where an unrelated project must NOT surface and a tagged sibling MUST; measure billed cost per successful probe (Hindsight retain-LLM plus 1,024-token recalls vs Mnemopi zero-infra); and judge by a success-adjusted verdict, not token counts. Guard rails from field evidence: an end-to-end retain-to-recall health probe (silent no-memory modes are real), pinned core AND integration versions, and explicit stable bank/tag IDs, never inferred from cwd or git root.

## Bake-off Stage 1 executed (2026-08-11, local)

**Amendment before trial data:** this machine has no OpenAI-compatible API key, so the arms were staged cheapest-first. Stage 1 is Hindsight **zero-LLM mode**: `retain_extraction_mode: chunks`, observations and consolidation off, a dummy key to satisfy the boot check, and embeddings/reranker running locally in the container. Rationale: if zero-LLM passes at $0 retain cost, retain-LLM cannot beat it on billed cost per successful probe. If zero-LLM fails, Stage 2 (retain-LLM) needs a real key. Stage 2 NOT run.

**Setup (guard rails honored):** the image was pinned to `ghcr.io/vectorize-io/hindsight:0.9.0` (4.22 GB). Bank IDs were explicit (`bakeoff-dotfiles`/`bakeoff-shared`), never cwd-derived. The retain-to-recall canary was green before ingest. No silent no-memory mode appeared: the engine fails LOUD without a key, unlike the hermes#7718 class. The corpus was the 20 OMP `-.dotfiles` session transcripts (2026-06-17→08-11, 302K chars, user and assistant turns only), the same source material Mnemopi's bank was built from. Contamination controls excluded the current session and truncated the 08-10 probe session at the first probe call (16:00:38Z). Before running, we verified that each probe's ground truth was present in 5–6 corpus sessions. Ingest took 13.8 s for 20/20 docs and used **0 LLM tokens** (ledger: 3 errored calls, 0 tokens billed).

**Decision-recall probes** (the same 4 that failed 4/4 on Mnemopi, graded by the same standard: the decision itself must surface, not era-adjacent sludge):

| Probe | Mnemopi (08-10) | Hindsight @1,024 (OMP-wired cap) | Hindsight @4,096 |
|---|---|---|---|
| P1 lean-ctx decision | FAIL (teaching-workspace sludge) | **PASS** — gate+kill-threshold+read-out verbatim | PASS (6 results incl. executed drop) |
| P2 memory owner | FAIL (superseded June wiring) | FAIL — surfaces 07-28 pre-decision two-owner state | **PASS** — "deliberately set" backend + one-owner rule (assembled from 2 results) |
| P3 compaction settings | FAIL (nothing relevant) | FAIL — doc-edit meta-chatter | PARTIAL — all 3 knobs + timing surface as *proposal*; applied 150K value only adjacent |
| P4 reflect (combined) | FAIL | FAIL by construction — reflect requires LLM (500/401) | same |
| **Total** | **0/4** | **1/4** | **2/4 + 1 partial** |

**Cross-project leakage probes: 4/4 PASS.** The `any_strict` union `[alpha,beta]` returned both tagged projects and never the unrelated `gamma`, even for a query baited toward gamma. Single-tag recall stayed single-project. The bank boundary held, so the dotfiles corpus was invisible from the shared bank. The multi-project features that put Hindsight on the shortlist work as documented.

**Probe forensics (post-hoc, 2026-08-11, correcting the "recall quality" reading):** at probe time (08-10 16:00Z) the dotfiles bank held **7 working rows + 16 facts, ALL from 2026-06-19→07-13**. No retains landed during 07-13→08-11 (the 08-17 gap differential below narrows the edges), the exact window in which every probed decision was made and discussed in dotfiles sessions. The ground truth was verified present in the same transcripts Hindsight ingested. No sibling dotfiles bank exists (17 non-benchmark banks checked), which rules out drift #2412. The era is absent from the store. Mnemopi's 0/4 therefore measures **silent retention failure** (the #2320/#2322 class from the field evidence, reproduced locally), not recall ranking. P1's "teaching-workspace sludge" (a 07-08 row) and P2's "superseded June wiring" (06-19/21 agentmemory rows) were the nearest neighbors available. Hindsight's @1,024 failures have the opposite mechanism. The ground truth WAS stored as raw chunks, but the 1,024-token cap admits exactly one chunk, and discussion or proposal text outranks the single decision statement (P2's pre-decision two-owner chunk, P3's doc-edit meta-chatter). That is a budget and ranking limit, which 4,096 relieves. P4 fails by construction, because reflect needs the LLM. Verdict unchanged. The arms failed for different reasons: Mnemopi couldn't retain, and Hindsight couldn't fit.

**Stage 1b (2026-08-12): probes replayed on the now-populated Mnemopi bank** (same wording, same grading). Results: **P1 PASS** (drop, ADR-0008 and `mcp.json` state in the top 4); **P2 PARTIAL** ("stays Mnemopi" at rank 3, c:0.4, but the one-owner rationale is absent and rank 1 is the *challenger's* spec); **P3 PARTIAL** (applied 150K and read-out "kept" at rank 4; handoff/idle knobs absent); **P4 PARTIAL** (reflect runs with no external key, unlike the Hindsight zero-LLM arm, but answers only the lean-ctx half). **1 PASS + 3 PARTIAL, against 0/4 on the empty store, confirm the forensics: Stage 1's Mnemopi 0/4 measured retention, not recall.** Caveat: this is NOT corpus-controlled against Hindsight. The bank now contains explicit `retain` calls and bake-off meta-discussion, while Hindsight's arm had only raw pre-probe transcripts. Stage 1b measures the realistic operating pipeline (auto and explicit retention), not a head-to-head. Net: populated Mnemopi roughly matches Hindsight@4,096 on decision recall, with opposite residual defects. Mnemopi's is **silent retention loss**, which tuning cannot fix and which needs a canary. Hindsight's is **recall budget**, which config can fix.

**Gap differential (2026-08-17, all suspects ruled out):** Not the OMP version (11 other project banks retained continuously across the same days and versions, 17.1.5→17.3.5). Not retain cadence (the 07-28 session had 28 user turns, about 7 due cycles, and retained 0, while 1-turn sessions retained fine before the gap). Not config (a 07-29 mid-gap backup shows `backend: mnemopi` correctly wired). Not misrouting or bank drift (none of 276 banks has dotfiles-marker rows in the window). Not the repo hooks (created 07-28, after the 07-19/07-26 failures). The edges are sharp: retention works through 07-14, is dead 07-19→08-10, and works again from 08-11, with no memory-related change at either edge. **Proximate cause unknown; failure was project-local, silent, and self-healing.** Such a failure cannot be diagnosed after the fact or detected from inside. An external retention canary is the only defense.

**Endpoint (billed cost per successful probe):** Hindsight zero-LLM scored **$0.00 / 1 success** at the OMP-wired 1,024 cap. Mnemopi scored 0 successes at any cost. Hindsight wins the endpoint as registered. Limits: 1/4 in absolute terms is weak. The binding constraint is OMP's 1,024-token recall cap, which is about one 3,000-char chunk in chunks mode. Raising `hindsight.recallMaxTokens` to 4,096 doubles successes at zero LLM cost, but injects up to ~3K more tokens per recall into the prompt, where cache-read economics apply. Extraction quality (retain-LLM), reflect, and observations remain unmeasured. They are Stage 2 work, which needs a real key.

**Infra cost:** the container uses 1.4 GiB RAM idle, the image is 4.22 GB, and it adds one `docker` dependency. Mnemopi needs no infra. The container was stopped after the run. The image and the `hindsight-bakeoff` volume are kept for Stage 2, though re-ingest takes only 14 s.


*Full agent reports (session artifacts): `history://MemoryScopingLibrarian`, `history://MemoryFieldReviewsLibrarian`.*
