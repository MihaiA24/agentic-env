# Native opt-in OMP isolation

This is Linux kernel/provider acceptance, not the helper's HOME-only isolation. Use the [deployment and grants runbook](../../../../guides/omp-isolation.md).

## Sub-features

- `isolation-init`: new instance, verified nono and snapshotted OMP; enforced version launch; collisions preserve existing state.
- `isolation-run`: console/module OMP launch, project working directory and dedicated runtime; no ordinary-startup changes.
- `isolation-security`: real filesystem, secret-environment, pathname-socket, network/proxy and canonical-command probes.
- `isolation-provider`: operator-authorized fresh OAuth, streamed provider response and successful project tool with independently checked output.
- `isolation-reject`: unsupported host/enforcement, changed or incomplete manifests, redirected control paths and initialization failure never launch unsandboxed.

## How to get to it (user POV)

Use `agentic-omp-isolated` or `uv run --frozen python -m agentic_env.isolated_omp`. Global `--instance PATH` precedes `init`, `run` or `check`. `init` requires `--project PATH`, optionally `--omp NAME_OR_PATH`; `run --` forwards OMP arguments. Defaults and complete native commands are in the runbook.

## Driving it with the verifier CLI

There is **no bounded helper drive** for this command. Do not invent one or claim helper freshness/doctor evidence. Exercise the real entry points in a separately owned disposable native Linux project/instance, with launcher sources outside both. Host prerequisites and supported devices are in the runbook. Missing kernel features or provider authorization are blocked paths, not skips or passes.

1. Finish source edits; record OS, architecture, Landlock ABI and source/policy/executable digests. Create only owned disposable state; retain non-secret stdout/stderr, commands and exit codes outside it.
2. Initialize via the console, using default OMP discovery. Independently inspect the generated policy and manifest. Require enforced version output and dedicated state. Rerun initialization against that same instance: require nonzero, identical trusted files and no overwritten state. Exercise explicit `--omp` on a separate fresh instance when executable selection changes.
3. Run `check` via the console; require all 14 named scenarios and exit 0. Repeat through the module when its routing changes. The probe creates its own fresh canaries, symlink and host socket, verifies output/outside content, then removes them.
4. Run the module entry's `run -- --version`; require the same snapshotted version and project/runtime grants. Execute ordinary host `omp --version` only to establish its normal entry remains callable, not to prove personal settings or provider health.
5. Obtain explicit authority for a new dedicated provider login and quota use. Run the documented device OAuth flow; the operator completes browser authorization. Never copy host auth, use personal API-key environment, or expose callback/host ports to avoid a login failure.
6. Create a nonce input in the owned project. Run a fresh JSON-mode session with only read/Bash tools, bounded time/cost and a request to read the input and copy it to another project file. Require streamed text deltas, successful actual tool events and exit 0. Independently compare output bytes to input. Preserve selected non-secret events, not tokens or database contents.
7. Regression supplement: `uv run --frozen pytest -q tests/test_isolated_omp.py` covers integrity refusal, incomplete manifests, redirected/overlapping controls, host prerequisites, environment exclusion and rollback/collision preservation. These tests are not the native security or provider proof. Rejection fixtures belong only in disposable state.
8. Preserve evidence, stop only owned processes and remove only disposable runtime/control files. Dedicated OAuth refresh tokens must not remain in verification scratch state; provider-side revocation is a separate operator action. Record exact cleanup and local-gate outcome.

## Gotchas

- Direct dedicated OAuth credentials are visible to sandbox tools; the selected scope and broker tradeoff are explicit in the runbook. No personal broker is connected.
- `login openai-codex` reports a misleading busy callback port under the restrictive policy; use the registered device flow instead of widening networking.
- Project files/extensions are untrusted workload input. All content under a project/runtime grant is available to the agent. Metadata hiding, resource limits, a complete toolchain, ACP clients and an interactive TUI require separate acceptance.
- `check` depends on live allowed HTTPS and installed Python/curl/admin binaries. Failures need diagnosis; an unrelated timeout or missing command is not evidence of denial.
- The branch-local gate tests committed HEAD and needs Docker/Bun. Native targeted proof does not substitute for its attestation.
