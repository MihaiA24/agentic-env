---
name: verify-agentic-env
description: Verify agentic-env CLI changes through checkout-isolated user commands, persisted-file evidence, and the maintained feature map. Use for copier, installer/picker, MCP/ACP configuration, bootstrap/update, or doctor/drift behavior proof.
---

# Verify agentic-env

Read [the feature index](features/README.md), then the affected maps. Ordinary changes prove every affected entry point and enabled flag variant; explicit `/maintain-verification-skill` exercises every mapped feature, repairs only the verifier/map, and reports product regressions. Read `DECISIONS_AI_TOOLING.md` §6 when selection or discovery semantics change.

## Launch

From this checkout's root, with Python 3.12+ and uv already available:

```sh
V=.agents/skills/verify-agentic-env/verifier/control.py
python3 "$V" launch
python3 "$V" doctor
```

`launch` runs `uv sync --frozen`, including the existing pytest dependency, in its own workspace environment. Ready means exit 0 and doctor JSON with `ready: true`, `build: "current"`, matching `fingerprint`/`built_fingerprint`, and this checkout's canonical path. It is not merely a successful dependency download. Finish source, test and verifier edits before launching: their contents and executable modes contribute to freshness. An old successful run is not evidence for a changed checkout; relaunch and repeat the user path.

These are short-lived Python CLIs, not a service. There is no server, login, declared TCP port, fixed readiness sleep, or process to attach to. Each drive waits for exit with a bounded deadline (default 180 seconds). A real prompt or process exit is the synchronization point. To change the deadline, put the global option first, for example `python3 "$V" --timeout 300 launch`.

Doctor prints the authoritative paths:

- Profile: `agentic-env-` plus the first 12 SHA256 characters of the canonical checkout path. This is an isolation identity, **not** a skill-pack profile.
- Mutable data: `.verifier/<reported-profile>/workspace`, including `home`, `skills` and `venv`.
- Retained proof: `.verifier/<reported-profile>/evidence` (a sibling of `workspace`).

Use these reported paths, never a guessed profile or another checkout's workspace. The helper supplies sandbox HOME/XDG/npm/uv paths, removes inherited credentials/configuration environment, and serializes mutable commands in this checkout. Do not drive one checkout concurrently. Different checkout paths have different profiles. Foreign ownership records, symlinks and a busy lock require investigation, not bypassing the guard.

## Doctor

```sh
python3 "$V" doctor
```

Run before **and after** each proof group, and first whenever behavior looks wrong. Require matching checkout/profile/data directory and a current build both times; retain both reports with the outer terminal/tool transcript. A stale/not-launched build exits 1. Source changes during a drive invalidate that run even if its application exit was expected.

The optional `doctor --port` accepts only an actually relevant, already observed port. It reports `lsof` PID/command/UID/cwd and refuses readiness for **any** listener: this verifier starts none and owns none. No port is applicable to the baseline. Never stop an unrelated listener or invent a port to make doctor look complete.

`drive stack-doctor` is the **product's** installed-stack diagnosis, not this freshness/ownership doctor. Its failure in an unprovisioned sandbox does not make the verifier stale.

## Drive

Use the implemented helper rather than writing another driver:

```sh
python3 "$V" drive copy --entry script --skill writing-for-agents
python3 "$V" drive inspect
python3 "$V" drive bootstrap --entry module --mode plan --format json
python3 "$V" drive configure --agent omp --server codebase-memory-mcp --dry-run
python3 "$V" drive configure-acp --entry console --client pycharm --client t3code --mode export --dry-run
python3 "$V" drive drift --pack mattpocock --pack pstack --format json
python3 "$V" drive help install-skills --entry console
```

Copier `script` uses isolated Python (`-I -S`); `module` exercises `python -m agentic_env.copy_skills`. Other commands use `uv run --frozen` with either their module or the checkout environment's installed `agentic-*` console entry. `drive install-skills` really uses the native skills CLI for a locally packaged custom-directory install; it additionally needs existing npm/Git/network access. It is not the Python-only copier.

The helper deliberately exposes a bounded safe subset. It has no generic shell/eval, managed provisioning, update, arbitrary target directory, or live picker passthrough. Maps identify the remaining public paths and their isolated acceptance prerequisites. Do not imply they were proved through this subset. The existing prompt-driven Unix PTY harness is reused by `drive tests --suite pickers`; its mocked installer boundary proves picker behavior, **not native installation**. Tests supplement, never replace, live user-path evidence.

**One copier feature, end to end.** Start with this checkout's fresh owned workspace. If it already contains data, inspect it, then use the cleanup procedure first. Run the following commands individually: the second copy is an intentional exit-1 collision, so do not chain the sequence with `&&` or stop at that expected failure.

```sh
V=.agents/skills/verify-agentic-env/verifier/control.py
python3 "$V" launch
python3 "$V" doctor
python3 "$V" drive copy --entry script --skill writing-for-agents
python3 "$V" drive inspect
shasum -a 256 agentic_env/vendored/mattpocock/skills/writing-for-agents/SKILL.md agentic_env/vendored/mattpocock/skills/writing-for-agents/SKILL-MECHANICS.md agentic_env/vendored/mattpocock/skills/writing-for-agents/agents/openai.yaml
python3 "$V" doctor
python3 "$V" drive copy --entry module --skill writing-for-agents
python3 "$V" drive inspect
python3 "$V" doctor
python3 "$V" cleanup --dry-run
python3 "$V" cleanup
python3 "$V" logs
python3 "$V" doctor
```

Require the first copy's `Copied 1 vendored skills` and exit 0; inspect must contain exactly the package's three files under `skills/writing-for-agents`, with the same SHA256s as the read-only source hash command. Require the second copy's `already exists`/`Skill copy failed` and exit 1, identical persisted hashes, and no new package. Doctor stays current before cleanup. Cleanup names evidence as preserved; `logs` after cleanup must still read the retained observation. Final doctor exits 1 with `build: "not-launched"` and `ready: false`. This collision proves the module error route, not module success: the [copier map](features/copier.md) adds a fresh-workspace module success when affected.

This recipe defines the proof; it is not a claim that a particular checkout passed. Report the actual observed run paths and results.

## Evidence

Each executed helper drive prints its evidence directory. `result.json` records the exact command/cwd, checkout/profile, source fingerprint, application exit, timestamps, before/after file hashes and `source_unchanged`; `stdout.txt` and `stderr.txt` retain output. `inspect` instead writes observation-only `state.json`, including doctor and persisted hashes. Inspect/eval is read-only **after** the user action; it may check files/configuration, never call internal setters or fabricate a successful path.

Test drives are labeled `kind: "regression-test"`; ordinary application drives are `user-path`, launch is `setup`, and inspect is `observation-only`. Preserve those distinctions in the report.

A proof contains:

1. Feature IDs, each exercised public entry point/mode/flag selection, and both doctor reports.
2. The action/prompt transcript, stdout/stderr and actual exit code, including expected cancellation/error outcomes.
3. A second read-only view of the resulting files, complete package hashes and relevant links/backups; compare before/after for cancellation, errors and dry runs as well as success.
4. Exact evidence paths and the outcome after cleanup. Retain the outer terminal/tool transcript (including source-hash output) alongside the proof report; helper logs alone do not record outer doctor commands.

`valid_evidence` means the source stayed current and the process did not time out/cancel; it does not mean application success or complete feature coverage. Exit 1 can prove an expected rejection. A timeout/interrupt is an incomplete run, not a successful app cancellation proof. Launch is setup evidence; `drive copy --dry-run` and `drive install-skills --dry-run` only print wrapper plans (`executed: false`, `evidence: false`). Configurator/bootstrap dry runs are actual **application** paths, but prove only their advertised skips after before/after observation. Filesystem hashes do not establish absence of network/browser activity: record those observations separately where the path can use them. No screenshot/browser/TCP proof applies to these terminal-only commands.

Missing seed state or unavailable native tools is a **blocked path**, with attempted command and exact prerequisite, not a pass or a silent skip. Use N/A only with a feature-specific reason (for example, a noninteractive copier has no confirmation prompt). Full provisioning/updating requires explicit authority and the existing `clean-acceptance.sh` runner in an isolated container or a fresh non-real HOME; see [bootstrap/update](features/bootstrap-update.md). Offline sandbox plans, mocked boundaries and preinstalled host tools do not prove clean-host acceptance. Stand-in/container evidence must name OS/architecture and setup steps absent from the real target; those target steps remain unverified.

## Cleanup

```sh
python3 "$V" cleanup --dry-run
python3 "$V" cleanup
python3 "$V" logs
python3 "$V" doctor
```

Review exact removals first. Cleanup removes only this owned workspace/cache, not evidence, owner record, checkout sources, host HOME/configuration or foreign processes. After any failed iteration, inspect its logs and clean up its owned scratch state too; if ownership checks refuse, resolve that conflict rather than deleting a directory blindly. Children are synchronous; on timeout/interrupt the helper terminates only the process group it started. Never kill by executable name.

`logs` reads the latest retained run/observation; `logs --run` accepts the exact basename printed by a prior drive. Keep evidence directories and any separately captured acceptance transcripts after workspace/container teardown. No uninstall or cleanup of the user's stack is part of verification.

## Helpers

The shipped executable is `.agents/skills/verify-agentic-env/verifier/control.py`; examples invoke it with Python explicitly. Discover the full implemented interface with:

```sh
python3 "$V" --help
python3 "$V" drive --help
python3 "$V" drive copy --help
python3 "$V" drive tests --suite verifier
```

Available existing test suites: `all`, `copy`, `pickers`, `configure`, `bootstrap`, `drift`, `doctor`, `verifier`. Run only suites relevant to the authorized verification task; no second test framework or invented PTY script is needed.

OMP discovers project skills under `.agents/skills/`. If the current session's registry returns `Unknown skill`, read `.agents/skills/verify-agentic-env/SKILL.md` explicitly and retry named discovery in a fresh project session. For Hermes without existing human-approved project trust, use `skill_view` with that explicit file (and feature `file_path`s when needed); automatic discovery requires the human to run `hermes skills trust` for this directory. Never grant trust or edit global runtime configuration for them. Use `/maintain-verification-skill` when entry points, prompts, flags or observable behavior change.
