# MCP and matching skill configuration

Add missing OMP/Hermes MCP definitions and optional matching descriptors, seed fresh OMP settings, and report drift without repairing user-owned definitions/settings.

## Sub-features

- `config-target`: OMP (`~/.omp/agent`, `~/.pi/agent`) and Hermes targets; each server or all, including OMP exclusions/default gates and Hermes memory-provider wiring.
- `config-write`: missing entries/descriptors and fresh OMP settings persist; repeat runs converge without needless edits.
- `config-preview`: application dry run and `--no-skills` establish their actual no-write/descriptor skip behavior.
- `config-preserve`: existing unrelated content, notify-only drift, malformed data, backups, symlink targets and refused dangling links.
- `config-prompt`: server/agent pickers, descriptor confirmation, empty choices and cancellation.

## How to get to it (user POV)

- `agentic-configure-agent-mcps` or `uv run --frozen python -m agentic_env.configure_agent_mcps`.
- `--agent omp`, `--agent hermes`, `--agent all`; `--server codebase-memory-mcp`, `--server agentmemory`, `--server all`. Flags are repeatable; unlike bootstrap, these selectors do not accept comma-separated values.
- `--yes` chooses defaults without prompting; `--no-skills` skips descriptor writes; `--dry-run` prints actions without writing; `--verbose` expands output; `--help` describes options. No agent binaries/MCP executables are installed by this command.

## Driving it with the verifier CLI

Preconditions: [baseline](README.md#baseline-preconditions), including checkout hooks used for fresh OMP settings. Missing MCP executables may warn; configuration is not a live MCP server/startup test. Each independent variant starts fresh unless explicitly testing repeat convergence.

- **Preview (`config-preview`)**: `python3 "$V" drive configure --entry module --agent all --server all --dry-run`, then `python3 "$V" drive inspect`. Require exit 0 and `dry-run: would write` actions, with identical before/after HOME file inventories and no descriptors/backups. This is the app's real dry-run path, not the wrapper's plan-only switch.
- **Fresh write (`config-target`, `config-write`)**: `python3 "$V" drive configure --entry module --agent omp --server codebase-memory-mcp`; inspect. Require exit 0, MCP config files in both OMP roots, stack-contract `config.yml` under `.omp/agent`, and matching descriptors. Read the files after the action: the requested server and required disabled-server policy must actually persist, and hook paths must identify this checkout.
- **Convergence (`config-write`)**: rerun that exact command and inspect. Require exit 0, already-configured/contract-matches messages and unchanged existing content hashes. Any backup is justified by a real changed preexisting file, not by an idempotent repeat.
- **Other targets/servers (`config-target`)**: independently run `python3 "$V" drive configure --agent hermes --server agentmemory`, `python3 "$V" drive configure --agent omp --server agentmemory`, and `python3 "$V" drive configure --agent all --server all`. Inspect chosen roots only, Hermes `memory.provider: agentmemory` when applicable, and OMP exclusion/gating rather than falsely expecting every requested server enabled. Cover both individual servers, each target and `all` when affected.
- **Skip descriptors (`config-preview`)**: fresh `python3 "$V" drive configure --entry console --agent all --server all --no-skills`; inspect. Require real config writes, `global skills: skipped` and no skill-descriptor files. Repeat with `--dry-run` when that combination changes. Distinguish descriptors from optional curated installer profiles.
- **Entry points/help**: repeat affected write/preview behavior with `--entry console`; `python3 "$V" drive help configure --entry module` and `python3 "$V" drive help configure --entry console` must exit 0. Module success does not prove installed-console wiring.
- **Drift/no repair (`config-preserve`)**: after a successful user configuration, use a normal text editor on the reported **sandbox** file to change an existing server command/arguments or an OMP contract setting; retain the pre-action edited-file hashes. Rerun the same configure command. Require exit 1, a concrete drift/manual-correction message and the conflicting file unchanged; other independently missing entries may still be added, so compare each file rather than assuming transaction rollback. A conflicting Hermes memory provider also fails. Never edit real HOME or call internal convergence/setter functions to create evidence.
- **Malformed/symlink/backup (`config-preserve`)**: changes to these paths require owned disposable user-config fixtures: malformed JSON/YAML or wrong root/block type; valid symlink to a user config; dangling/looping link; preexisting file needing a missing entry. Exercise the public configurator and inspect. The wrapper refuses managed-config symlinks: run link fixtures directly in the separately owned acceptance environment. Require errors with preserved malformed/dangling files; valid links survive with the resolved target updated atomically and `.agentic-env.bak` beside it; unrelated content persists. An unavailable fixture/permission boundary is a blocked path, not silently omitted.
- **Regression supplement**: `python3 "$V" drive tests --suite configure` covers contract and filesystem edge cases but does not replace the live action/file proof.

Live prompts/repeated-selector/verbosity paths are outside the bounded helper. With explicit authority, run these **inside** the owned clean-acceptance environment described in [bootstrap/update](bootstrap-update.md), never the daily host:

- `agentic-configure-agent-mcps`: wait for `Select MCP servers`, then `Select agents`, then `Add matching global skills if missing`. Confirm an actual selection and compare the written state with its replayable flag-driven equivalent. Independently Ctrl-C at each picker and record actual exit/no-write result; decline matching descriptors and require no descriptors, while selected configs may still be written.
- Clear both server and agent pickers: require successful no-write. Clear agents only: no target writes. Clear servers but select OMP: inspect the actual settings/gating behavior; an empty server selection is **not** a blanket promise of no writes to the selected OMP target.
- `agentic-configure-agent-mcps --yes --agent omp --agent hermes --server codebase-memory-mcp --server agentmemory --no-skills --verbose`: require both selected targets/servers with the same exclusion policy and verbose transcript. Invalid `--agent codex` or `--server not-a-server` must exit 2/no writes.

## Gotchas

- Configurator exit 1 on Hermes drift is intentional; product doctor treats secondary Hermes findings as warnings. Existing OMP settings are notify-only, never automatically repaired. A missing settings file is seeded only when checkout hooks are found.
- Required policy may remove/gate excluded OMP entries; preserving existing definitions does not mean preserving explicitly excluded entries. Read persisted files and the policy in Decisions before declaring an unrelated edit.
- A no-write dry-run claim requires before/after files, not the flag name. Config generation does not start servers or validate their external service/network/auth behavior: those paths are N/A here, with binary warnings retained.
- YAML rewrites can drop formatting/comments; symlink preservation and backups concern the resolved target. Permissions/partial failure are not rollback guarantees.
- Doctor before/after establishes build freshness; `drive inspect` is a second read-only view after the user action. Retain evidence and clean the owned sandbox even after a failed write.
