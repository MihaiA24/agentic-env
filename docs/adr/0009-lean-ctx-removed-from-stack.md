# ADR 0009: lean-ctx removed from the stack

## Status
Accepted 2026-09-02. Supersedes ADR-0008's "secondary agents are untouched" clause and closes parked Q-F(a): `lean-ctx` leaves the managed stack on every harness, not only OMP.

## Context
ADR-0008 dropped `lean-ctx` from OMP on 2026-08-11 but left it installed, pinned, checksummed, smoke-tested, and updated for the secondary agents. Containment failed twice on this host:
- 2026-08-11: the `mcpServers.lean-ctx` entry was removed from `~/.omp/agent/mcp.json`, but OMP's claude-import kept re-reading `~/.claude.json`, whose `lean-ctx` entry carries the "shadow mode: native file/search/shell calls auto-route to ctx_*" `instructions` prose. Adding the name to `disabledServers` stopped the mount but not the prose; the system prompt of a live OMP instance still carried the shadow-mode block on 2026-09-02 (Rule 5: wiring routes, prose doesn't — and here the prose routed the wrong way).
- The 3.9.x line ships lossy read mode as its default; ADR-0007/0008 measured lossy reads on the read→edit path at patch success 27/40 → 15/40. Reinstalling the pinned version would reintroduce the exact hazard the earlier ADRs removed.
Measured benefit on the secondary agents: none recorded — they are unmeasured harnesses, and the one capability without a native substitute (semantic search) fired once in two weeks on the primary.

## Decision
Remove `lean-ctx` from the stack: installer, pin/checksum table, update step, skill descriptor, smoke, and every host config (`~/.claude.json`, `~/.hermes/config.yaml`, `~/.codex/config.toml`, the three skill roots, the binary). Two things stay:
- `OMP_EXCLUDED_SERVERS` keeps the name so `agentic-configure-agent-mcps` purges any re-imported entry and keeps it in `disabledServers` on both OMP roots.
- A reinstall pointer in `stack_metadata.py`: if a need fires, reinstall at **3.10.0 or newer** (lossless-read default), never 3.9.x.

`agentic-stack-doctor` diagnoses the invariant: no `lean-ctx` in `mcpServers`, no read-interception prose in any config OMP loads (including `~/.claude.json`), no `lean-ctx` skill in an OMP-loaded skill root.

## Considered options
1. **Keep installed but unwired ("mark unused")** — rejected. Carries pin, checksum, archive matrix, smoke, and update code for zero measured benefit, and every re-import path stays live.
2. **Keep on secondaries, remove on OMP only (status quo)** — rejected; this is what failed twice. The secondaries are not measured, so "keep" is not a decision, it is drift.
3. **Remove now, reinstall pointer** — taken. Reinstall is one line; the pointer records the version floor so the lossy default cannot come back by accident.

## Consequences
- Secondary agents lose their context-routing layer. Accepted: they are documented under Harness → "Secondary agents TODO" in `DECISIONS_AI_TOOLING.md`, and Rule 5 says the routing they lose was prose-level anyway.
- The `<generic-rules>` shadow-mode block disappears from OMP system prompts once the host `~/.claude.json` entry is gone and instances restart.
- If semantic search is ever needed again, the reinstall is `lean-ctx >= 3.10.0` with an OMP-native gated entry per ADR-0008's server-side gate pattern — not the claude-import path.
