# Native OMP ACP configuration

Register OMP in PyCharm or T3 Code native settings, or export ready-to-copy JSON. This proves configuration files, not client discovery, UI behavior or an ACP session.

## Sub-features

- `acp-native`: selected native registrations, unrelated data and matching-entry extensions survive; matching repeats preserve bytes and backups.
- `acp-export`: rendered native JSON goes to the owned export folder; existing targets are never overwritten.
- `acp-preview`: real application preflight in both modes leaves settings, exports and backups unchanged.
- `acp-reject`: conflicts, malformed input and export collisions fail before any selected destination is written.

## How to get to it (user POV)

- `agentic-configure-acp` or `uv run --frozen python -m agentic_env.configure_acp`.
- Required repeatable `--client pycharm` / `--client t3code`; select both by repeating the flag, not with commas or `all`.
- Default native targets: `~/.jetbrains/acp.json` and `${T3CODE_HOME:-~/.t3}/userdata/settings.json`. Close T3 Code before changing its settings.
- `--output-dir PATH` exports `pycharm.json` / `t3code.json` into that exact directory. `--omp NAME_OR_PATH` resolves the executable; default is `omp`. `--dry-run` preflights without writes or backups. There are no prompts or `--yes`/`--all` flags.

## Driving it with the verifier CLI

Preconditions: [baseline](README.md#baseline-preconditions) and the real `omp` executable discoverable on host PATH. The helper resolves it with `shutil.which` and passes an absolute `--omp`; an unavailable executable blocks the path. It neither substitutes an executable nor starts OMP. HOME stays isolated and inherited `T3CODE_HOME` is removed.

The bounded drive accepts only `--entry module|console`, repeatable `--client pycharm|t3code`, `--mode native|export` and `--dry-run`. Native uses the reported workspace HOME; export maps to its `acp` folder. It exposes no arbitrary output/configuration/HOME path. Start independent successes with a fresh workspace; cleanup preserves prior evidence.

- **Preview (`acp-preview`)**: run `python3 "$V" drive configure-acp --entry module --client pycharm --client t3code --dry-run`, then `python3 "$V" drive inspect`. Repeat with `--mode export`, and with `--entry console` for both modes. Require exit 0, identical before/after file hashes and no native/export files or backups created from an empty workspace. A successful preview does not prove a write.
- **Native write (`acp-native`)**: `python3 "$V" drive configure-acp --entry module --client pycharm --client t3code`; inspect, then read the reported sandbox files. Require exit 0 and `home/.jetbrains/acp.json` plus `home/.t3/userdata/settings.json`. PyCharm's `agent_servers['Oh My Pi']` must contain the resolved OMP command and `args: ['acp']`. T3's `providerInstances.acpRegistry_omp` must have `driver: 'acpRegistry'`, `displayName: 'Oh My Pi'`, `enabled: true`, and local config with that command in `commandPath` and `commandArgs: ['acp']`.
- **Native repeat (`acp-native`)**: run the same selected clients with `--entry console`, then inspect. Require exit 0 and identical settings/backup bytes; no new backups. Repeat preview after success and require the same no-write result.
- **Export (`acp-export`)**: `python3 "$V" drive configure-acp --entry console --mode export --client pycharm --client t3code`; inspect and read `acp/pycharm.json` and `acp/t3code.json`. Require exit 0, both rendered native schemas above and recorded hashes for both exports. Native settings must remain unchanged. Repeat with `--entry module`: require exit 1 for the collisions, identical hashes and no backups. A colliding `--dry-run` must also fail without writes.
- **Entry/selection coverage**: repeat fresh native and export writes with the other entry point. Independently exercise each single client and the repeated-client pair; a single selection must leave the other client's destination absent/unchanged. Cover default native mode and explicit `--mode native`. `python3 "$V" drive help configure-acp --entry module` and its console variant must exit 0; help is not write evidence.
- **Preservation (`acp-native`)**: using a normal editor only on the reported sandbox files, add an unrelated setting/agent and an extra field in each matching OMP entry; retain edited-file hashes. Rerun native configuration and require all content and bytes unchanged. Separately start with valid unrelated settings but no OMP entry: require the missing registration added, unrelated values preserved and `.agentic-env.bak` containing the original bytes.
- **Native rejection (`acp-reject`)**: seed a conflicting OMP command/arguments or a required T3 field, malformed JSON, or wrong root/registration-container type in one selected sandbox destination while the other is missing. Retain fixture hashes; select both clients and run apply and preview. Require exit 1, the bad/conflicting file unchanged, the other destination still absent and no backups. Exercise the error in either client so preflight order cannot hide a partial write.
- **Export rejection (`acp-reject`)**: after a successful export, remove one owned export and retain the other's hash, then select both clients. Require exit 1, the existing file unchanged and the missing file still absent, including in preview. Existing files, directories and symlinks all collide; the wrapper refuses symlinks before execution, including dangling links.
- **Safety supplement**: `python3 "$V" drive tests --suite verifier` covers owned-root/symlink refusal, unavailable OMP, persisted native/export hashes and evidence surviving cleanup. It is regression evidence, not a live client configuration proof.

## Gotchas

- Inspect records native HOME files, exports and backups. Compare inventories for errors, repeats and previews; an exit code alone cannot establish preservation.
- The wrapper rejects links anywhere under `.jetbrains`, `.t3` and the export folder, including linked roots. Product symlink/collision fixtures beyond that guard require a separately owned isolated acceptance environment; do not bypass the guard or use host configuration.
- Every selected destination is preflighted before writes. Runtime I/O failure is not a multi-file transaction or rollback guarantee.
- A valid command path does not establish client support, authentication or an ACP conversation. Client UI/session proof is outside this file-only journey.
- Retain doctor reports and evidence paths before cleanup; `logs` must still read the proof afterward.
