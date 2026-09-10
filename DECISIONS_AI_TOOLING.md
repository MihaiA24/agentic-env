# Agent Stack — Decisions

> Sole operative doc. 2026-08-19: absorbed `AGENT_STACK.md` + `TOOLS_RESEARCH.md` (deleted); the frozen evidence ledger `AI_CONTEXT_TOOLING_COMPARISON.md` was deleted the same day — full evidence, grades, and methods live in its git history. Binding ADRs: `agentic-env/docs/adr/0006`–`0009`.
>
> Layout (2026-09-02): the summary table, the measured rules every layer cites, then one section per layer — **Decided → Why → Rejected → Revisit → Wiring** — so a reader can follow each decision from evidence to config line. Cross-cutting contract in "Live wiring", pre-registered triggers in "Upstream watch". Vocabulary: `docs/CONTEXT.md`.

## The stack

| Layer | Decided | Why | Alternatives | Revisit when |
|---|---|---|---|---|
| Harness | OMP | Best model + LSP + edit anchors | Hermes, Claude Code, opencode, Codex | Never unless OMP fails |
| Context I/O | OMP native only | Cache-stable, anchor-safe; compressors break edits | lean-ctx (removed, ADR-0009), Headroom, rtk | Native tools visibly fail |
| Compaction | handoff @ 150K, idle on, save-to-disk | −43–50% tokens, quality held | 120K threshold | End-green < 88% → revert |
| Memory | Mnemopi + retention-canary hook | Recall good, keyless, zero infra; canary covers silent-loss defect | Hindsight (sole challenger), mem0, agentmemory, Letta, Zep | Cross-project memory sharing needed → Hindsight |
| Code graph | codebase-memory-mcp gated off | Costs quality, 10× tokens | GitNexus, GraphRAG, Serena, etc. | Litmus fires weekly |
| Skills | Fit-curated roster (see Skills section): Pocock spine + Ponytail forced + Caveman/Graphify on demand + 4 pstack picks | Fit-judged by user; audits prune | Full Pocock 25 + pstack 44 stores | Fit audit flags stale |
| Hooks | verification-recorder, retention-canary | Pass-rate read-outs; silent-memory-loss tripwire | cadence-governor (rejected 08-19), external monitoring | Recorder DB unread by next read-out; canary false-warns |

```mermaid
flowchart LR
  OMP[OMP 18.1.14 — primary harness] --> IO[Context I/O: native read/grep/glob/edit + LSP + scouts]
  OMP --> CMP[Compaction: handoff @150K, idle, save-to-disk]
  OMP --> MEM[Memory: Mnemopi, polyphonicRecall off]
  OMP --> HK[Hooks: verification-recorder, retention-canary]
  OMP -.gated off.-> CG[codebase-memory-mcp]
  OMP -.disabled.-> NR[node_repl builtin]
  OMP -.excluded.-> AM[agentmemory, lean-ctx]
  SK[Skill store ~/.agents/skills] -->|symlink| CS[~/.claude/skills → OMP root]
  SK -->|symlink| HS[~/.hermes/skills]
  SK -->|direct| CX[Codex]
```

Agents around the stack: **OMP** is the primary harness (its wiring is the mandatory contract). **Hermes** is a supported agent (installed + configured; doctor warns). **Claude Code** and **Codex** are installed agents (pinned CLI + skills, nothing managed). Detail under Harness.

## Rules (measured; violations cost real money)

1. Judge by success-adjusted billed cost, never token reduction (correlation r=0.15).
2. Cache reads ≈ 68.6% of bill — a tool that can't touch cached re-reads can't move it.
3. No lossy compressor on the read→edit path (anchor corruption: patch success 27/40 → 15/40).
4. One semantic-memory owner per agent. OMP LSP owns live symbol truth.
5. Wiring routes tools; prose doesn't (3×-repeated prompt mandate → 15.6% adherence; cadence-governor nudges 16.4% ≈ chance).
6. Vendor claims measure at 1/8–1/3 of advertised, or negative — adopt only on locally measured, pre-registered endpoints.
7. Decisions live in committed docs; memory is convenience.
8. Skills are adopted on workflow fit (user judgment); usage audits are diagnostic — they flag stale or duplicate skills for re-review, never gate adoption. Rule 6 governs tools only. Usage units are canonical in `docs/CONTEXT.md`: user-invoked ≠ model-invoked ≠ string-scan.

What the rules bought: every rejection below names the pre-registered threshold it missed (lean-ctx 1 semantic call < 5; agentmemory 0 calls in 934 sessions; node_repl 0 calls; cadence-governor 16.4% adherence ≈ chance). The stack doctor enforces exactly what those verdicts left standing. Round 2 full-market sweep (17 tools, 08-11): 0 adoptions — no candidate ships 3P agent-on-repo evidence.

## Decisions by layer

### 1. Harness — OMP

- **Decided:** OMP, pinned `18.1.14` (`stack_metadata.OMP_VERSION`; release assets and contract settings reviewed at `v18.1.14`; installer hash unchanged).
- **Why:** best model access + LSP + edit anchors. The alternatives lost on tooling, not on model.
- **Rejected as primary:** Hermes, Claude Code, opencode, Codex. A paired OMP/Hermes benchmark is parked — only if OMP-primary ever needs to be definitive.
- **Revisit:** never unless OMP fails. OMP major bump → re-verify converge keys against `packages/coding-agent/src/config/settings-schema.ts` at the new tag, re-pin, re-run the docker smoke.
- **Wiring:** contract keys verified at the pinned tag: `memory.backend`, `compaction.{thresholdTokens,idleEnabled,handoffSaveToDisk,methodOrder}`, `skills.{enableClaudeUser,enableAgentsUser}`, `extensions`; drift check is block-scoped (`OMP_AGENT_CONFIG_CONTRACT`), not substring. `node_repl` built-in disabled on both OMP roots (0 calls; `OMP_GATED_BUILTINS`, doctor-enforced). MCP + skill roster bind at instance start: after any `mcp.json` edit → `/mcp reload` or restart live omp instances.

#### Agent tiers (2026-09-02)

- **Primary harness — OMP.** Installer-enforced, smoke-verified, doctor failure.
- **Supported agent — Hermes.** CLI, skills, MCP config, and health checks managed; doctor warns only (`TODO secondary`). Keeps `codebase-memory-mcp` + `agentmemory` entries (behaviour unmeasured).
- **Installed agent — Claude Code, Codex.** Pinned CLI + curated skills via the skill store; no MCP config written or diagnosed; doctor warns only when the binary is missing.

#### Secondary agents TODO (closed 2026-09-02)

1. Hermes install correctness — **closed by `chore/agentic-env-bump-pins`**: pin moved to release v2026.8.31 (`0.21.0`, `29112bef`); `_install_hermes` converges to `HERMES_COMMIT` on fresh or behind checkouts and leaves a checkout ahead of the pin alone (the installer refuses rollbacks without `--force-commit`; drift above the pin is tolerated, doctor warns).
2. `agentmemory` + `codebase-memory-mcp` wiring on Claude/Codex — **not pursued**: Claude Code and Codex are installed agents; measured need for managed wiring is zero (agentmemory 0 calls in 934 sessions, codebase-memory litmus 0×). Hermes keeps its entries; the `@agentmemory/mcp` shim is pinned to `AGENTMEMORY_VERSION`.
3. Codex per-tool approval filters — **not pursued**: no managed Codex MCP config exists to filter.
4. Claude/Codex pin refresh — **closed by `chore/agentic-env-bump-pins`**: Codex 0.152.1, Claude 2.1.258, agentmemory 0.9.29; installer script checksums re-verified unchanged.

### 2. Context I/O — OMP native only

- **Decided:** OMP-native `read`/`grep`/`glob`/`edit` + LSP + scout subagents. Nothing sits on the read→edit path.
- **Why:** Rule 2 — cache reads are 68.6% of the bill and a compressor can't touch cached re-reads. Rule 3 — lossy compression corrupts edit anchors (patch success 27/40 → 15/40). Native is cache-stable and anchor-safe.
- **Rejected:**
  - lean-ctx — by its own pre-registered threshold (1 semantic call < 5; ADR-0008 fallback); removed stack-wide 2026-09-02 after containment failed twice (ADR-0009). Reinstall pointer ≥ 3.10.0 (never 3.9.x, lossy read-path default) in `stack_metadata.py`.
  - Headroom (+48.4% cost), rtk (wash), LLMLingua (degrades on code agents) — 3P evidence.
  - Context Mode, mcp-compressor, OmniRoute, pxpipe — duplicate native, unproven, or unneeded. aider repomap, Repomix — not pursued.
- **Revisit:** grep+LSP+scouts visibly fail on a real task → context I/O re-shop (Parked). Semantic search visibly missing → reinstall lean-ctx ≥ 3.10.0 with an OMP-native gated entry (ADR-0009), never the claude-import path.
- **Wiring:** read-interception prose has zero tolerance in any config OMP loads, including `~/.claude.json` `mcpServers.*.instructions` (doctor greps `ctx_` / `shadow mode` / `auto-route`). `lean-ctx` is purged **and** disabled on both OMP roots (`OMP_EXCLUDED_SERVERS`), must be absent from `~/.claude.json` (mandatory), and a stale Hermes entry warns.

### 3. Compaction — handoff @ 150K, idle on, save-to-disk

- **Decided:** `handoff` at 150K tokens, idle compaction on, handoff saved to disk.
- **Why:** −43–50% tokens with quality held.
- **Rejected:** 120K threshold (same quality, less headroom). The `handoff-as-deliberate-habit` skill — compaction covers fragmentation mechanically; "remember to invoke at seams" is prose, and prose doesn't route (Rule 5).
- **Revisit:** end-green < 88% → revert.
- **Wiring:** `compaction.{thresholdTokens,idleEnabled,handoffSaveToDisk,methodOrder}` in `~/.omp/agent/config.yml` (bak `config.yml.bak-tuning`).

### 4. Memory — Mnemopi + retention canary (settled 2026-08-19)

- **Decided:** Mnemopi stays default (user, 2026-08-11); the retention-canary hook covers its one defect.
- **Why:** recall good, keyless, zero infra. Stage 1 (08-11): zero-LLM Hindsight won the registered endpoint (decision-recall 1/4 @1,024 tok vs 0/4; cross-project isolation 4/4 PASS). Forensics (08-12): Mnemopi's 0/4 was a **silent retention gap**, not recall — zero retains 07-13→08-11 despite correct wiring. Stage 1b replay on the populated bank ≈ parity (1 PASS + 3 PARTIAL; reflect works keyless). Gap differential (08-17) ruled out version, cadence, config, drift, and hooks. Residual defects are opposite: Mnemopi = silent retention loss → **retention canary wired 08-18**; Hindsight = recall budget (config). Full data: `docs/memory-backend-research.md`.
- **Rejected:**
  - agentmemory on OMP — 0 calls in 934 sessions; ADR-0006 single memory owner. Stays on Hermes.
  - Hindsight — sole challenger; the one thing Mnemopi structurally cannot do is cross-project sharing.
  - mem0, MemPalace, Letta, Zep — unproven claims, wrong lane, or paid-only.
  - Stage 2 bake-off — skipped (user, 2026-08-19): was blocked on an OpenAI-compatible key; Stage 1b parity + the canary cover the residual risk. Unblock paths stay in the research doc if reopened.
- **Revisit:** related-project memory sharing becomes a live need → Hindsight (vs mem0 bake-off). Upstream https://github.com/can1357/oh-my-pi/issues/8940 (filed 2026-08-19: silent retention gap + differential; asks for retain-attempt telemetry) ships → retire the canary.
- **Wiring:** `memory.backend: mnemopi`; `mnemopi.polyphonicRecall: false` — the key lives under `mnemopi.`, not `memory.` (same in 17.0.5; template, host config, and drift check fixed 2026-09-02). `agentmemory` purged and disabled on both OMP roots and absent from `~/.claude.json`. Hermes: `mcp_servers.agentmemory` (`npx -y @agentmemory/mcp@<AGENTMEMORY_VERSION>`) + `memory.provider: agentmemory`.

### 5. Code graph — codebase-memory-mcp, wired but gated off

- **Decided:** installed and registered on both OMP roots, disabled by default; enabled per session only when the litmus fires.
- **Why:** costs quality and 10× tokens on ordinary tasks.
- **Litmus:** the task needs >10 native calls, crosses repo boundaries, or aggregates the whole graph → `/mcp enable` + `fast` reindex. Fired 0× since 08-05. Promotion: fires ~weekly in a project → default-on there.
- **Rejected:** GitNexus, GraphRAG, cognee, Graphiti, Semantica, Serena — no coding evidence, license, or paid.
- **Revisit:** litmus 0× by **2026-10-01** → remove `codebase-memory-mcp` from the OMP roots (keep installed for per-project on-demand mounting). Upstream 0.10.8 available vs pin 0.9.0; bump only on promotion.
- **Wiring:** `mcpServers: {codebase-memory-mcp}` gated by `disabledServers: [agentmemory, node_repl, codebase-memory-mcp, lean-ctx]` on `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` (`OMP_GATED_SERVERS`; bak `mcp.json.bak-leanctx-drop`, `.bak-gate`). Hermes wired too (unmeasured).

### 6. Skills — fit-curated roster (settled 2026-08-22)

- **Decided:** Pocock spine + Ponytail forced-injected + Caveman/Graphify on demand + 4 pstack picks. Criterion: workflow fit, judged by the user (Rule 8).
- **Why:** measured — Ponytail −10.3% cost (must force-inject), Caveman −8.5% (on demand); Graphify on demand. The 2026-08-20 fit audits (`docs/pocock-skills-fit-report.html`, `docs/pstack-skills-audit.html`) are diagnostic input, committed with adjudication addenda.
- **Audit adjudication (08-22, raw DBs):** both reports honest, units systematically mixed. 567 OMP "sessions" = 226 main + 341 subagent. grill-with-docs: 74 OMP session files / 215 Hermes sessions user-invoked (413 = registry loads). tdd/code-review: 0 user-invoked vs 108/320 model-invoked — the model reaches for them, the user never does; don't force slash commands. Only verification DBs reproduced exactly (OMP 527 @ 87.3% pass, Hermes 248): dedicated event tables beat string scans. Counting units: `docs/CONTEXT.md`.
- **Adopted 08-22 (vanilla first; adapt only after real friction):**
  - `resolving-merge-conflicts`, `diagnosing-bugs` (Pocock) — sat on measured pains (merge churn: 64+ merges with conflict fallout; repeat-diagnosis loops) while structurally unavailable in OMP (skill store only, `enableAgentsUser: false`). Their low use was availability, not misfit.
  - `create-verification-skill` (pstack) — the only genuine capability gap either audit found: verification is test/lint-centric; no user-journey checks on Paw app/portal/course sites.
  - `show-me-your-work` (pstack) — decision trails (Run Records, sealed proofs) are hand-rolled per repo today.
  - `reflect` (pstack) — the manual retrospective→skill-patch loop (137 patches on code-review), automated.
  - `recall` (pstack) — installed manual-only (ships `disable-model-invocation: true`). Forensic tool for canary-fires events; never wired (Rule 4, single memory owner).
- **Pruned from pack:** `to-spec`, `to-tickets` — 1 use each in 5 months; grill-with-docs + wayfinder already emit specs and tickets.
- **Rejected:**
  - pstack duplication cluster (poteto-mode, laziness-protocol, subtract-before-you-add, minimize-reader-load, no-comments) — duplicates benchmarked ponytail / caveman; double style injection = paid prompt weight; no-comments contradicts load-bearing `ponytail:` ceiling markers. Novel fragments fold into ponytail text, never a second skill.
  - pstack blast-radius, swarm — OMP-native subagent fan-out already covers both; a skill adds prompt weight over a proven native flow.
  - grill-me — grill-with-docs is a proven superset, including non-code decisions (this decision session ran on it).
  - handoff-as-deliberate-habit — covered mechanically by compaction (layer 3). Skill stays installed for on-demand use.
  - writing-for-agents — doc-drift pain is real but the skill is prose discipline, no mechanism; revisit if drift persists.
  - pstack recall-as-wired-hedge — Rule 4 violation; retention-canary covers detection; upstream #8940 telemetry would retire even the canary.
  - wait-what, to-questionnaire, ask-matt, wizard — no observed need in 5 months / 1,000+ sessions.
- **Revisit:** next fit audit, or when a pruned skill's pain resurfaces. pstack Tier 1 leftovers (why, automate-me, interrogate, arena, technical-writing) reopen only if an adopted pstack pick earns its keep. mattpocock `retro` ships → fit audit against pstack `reflect` (same job; keep one).
- **Wiring:** curated at install time via `skill-packs.json` (packs list their skills explicitly; the `default` profile is the roster the doctor checks under `~/.claude/skills`, the root OMP loads). Packs pinned to upstream tags in `source` (`mattpocock/skills#v1.2.3`; `JuliusBrussee/caveman#v2.3.1` — the benchmarked text, v2.4.0+ not taken; `DietrichGebert/ponytail#v4.9.0`); `cursor/plugins` (pstack) publishes no tags and floats on `main`. `skills.enableClaudeUser: true` + `skills.enableAgentsUser: false` — `~/.agents/skills` is the skill store: the canonical copy that `~/.claude/skills` and `~/.hermes/skills` symlink into, loaded once via the Claude root. `enableClaudeUser` must be set explicitly: it defaults to `false` in the inspected OMP 18.1.13 schema, which silently left the whole pack invisible to OMP (found 2026-09-07 via missing `grill-with-docs`; only plugin + `~/.omp/agent/skills` skills loaded). Local one-off skills (graphify) live in the agent skill roots directly, outside packs.

### 7. Hooks — verification-recorder + retention-canary

- **Decided:** two hooks, `omp/hooks/verification-recorder.ts` and `omp/hooks/retention-canary.ts`.
- **Why:** pass-rate read-outs (OMP 527 verifications @ 87.3% pass; dedicated event tables beat string scans) and a silent-memory-loss tripwire (layer 4).
- **Rejected:**
  - cadence-governor (2026-08-19, measured non-adherence). Across 589 session logs: verification nudge 16.4% adherence within 10 calls, declining by fire number (17.5% → 10.6% → 8.7%) — at or below the ~22% chance rate of any 10-call window containing a verification command; overwrite-steer 15% immediate switch (n=20). The 08-11 read-out's sole positive signal (first-fire 59% verify ≤25 calls) came with 60% of all fired nudges being spam beyond N=75 — the 3-strike cap treated the symptom. Prose doesn't route (Rule 5). Reopen bar: a mechanism that routes (blocks/redirects) rather than nudges.
  - External monitoring — no mechanism inside the harness.
- **Revisit:** recorder DB unread by the next read-out; canary false-warns; canary fire-rate on 18.1.x read at the next read-out (zero fires and #8940 still open = keep); #8940 ships → retire the canary.
- **Observation (2026-09-09, unverified):** the retention canary reported an empty/never-retained bank while `recall` returned stored memories from that bank. Recall success does not establish what the canary measures or prove a false warning. Compare the observation with the canary's measurement at the next read-out; no hook change or investigation in this pass.
- **Wiring:** each hook registered exactly once in `extensions:` with its file present (doctor-enforced). Hook files are diagnosed, never written (machine-provisioning boundary); the installer finds them via `$AGENTIC_DOTFILES_ROOT`, then `~/.dotfiles`, then the cwd/package ancestors, and refuses to seed `config.yml` without them (a half-seeded config is three doctor failures later).

## Live wiring (this machine)

Mandatory contract = the OMP layer. Installer-enforced (`agentic-configure-agent-mcps`), smoke-verified (`docker-smoke-test.sh`), diagnosed by `agentic-stack-doctor` (read-only; exit 1 only on an OMP check; Hermes wiring and the Hermes/Claude/Codex binaries warn with a TODO tag). The doctor runs as the last phase of `agentic-bootstrap` and `agentic-update-stack`.

- Clean-host contract (2026-09-02): `uv tool install --force . && agentic-bootstrap` on a host with a `~/.dotfiles` checkout yields exactly this stack; version drift above the pins is tolerated, skill/MCP/hook drift is not.
- Fresh-machine reproducibility: `agentic-configure-agent-mcps` seeds `~/.omp/agent/config.yml` from this contract when absent and verifies it when present (`converge_omp_agent_config`; existing user YAML is never rewritten).
- The concrete settings are the **Wiring** line of each layer above: harness (pin, contract keys, `node_repl`), context I/O (excluded servers, prose ban), compaction (`compaction.*`), memory (`memory.backend`, `mnemopi.polyphonicRecall`), code graph (`mcp.json` gate), skills (`skill-packs.json`, `skills.enableClaudeUser`, `skills.enableAgentsUser`), hooks (`extensions`).

## Upstream watch

Pre-registered triggers; nothing here is acted on without the trigger firing. Each is also the **Revisit** line of its layer.

- oh-my-pi #8940 (retain-attempt telemetry) ships → retire the retention canary.
- OMP major bump → re-verify converge keys against `settings-schema.ts` at the new tag, re-pin, re-run the docker smoke.
- Canary fire-rate on 18.1.x → read at the next read-out; zero fires and #8940 still open = keep.
- codebase-memory litmus 0× by **2026-10-01** → remove `codebase-memory-mcp` from the OMP roots (keep installed for per-project on-demand mounting). Upstream 0.10.8 available vs pin 0.9.0; bump only on promotion.
- mattpocock `retro` ships → fit audit against pstack `reflect` (same job; keep one).
- lean-ctx need fires (semantic search visibly missing on a real task) → reinstall ≥ 3.10.0 per ADR-0009.
- Cross-project memory becomes a live need → Hindsight vs mem0 bake-off.
- Trendshift screening: **Retired** as a routine (0 adoptions across two sweeps); on-demand reruns only.

## Parked

- Paired OMP/Hermes benchmark — only if OMP-primary ever needs to be definitive.
- Context I/O re-shop — only when grep+LSP+scouts visibly fail on a real task.
