# ADR 0001: Container base image for fresh agent-stack install

## Status
Superseded on 2026-09-30 by the current decision below. Original measurements are historical, not acceptance evidence for the current stack.

## Current decision

Use `node:24-bookworm-slim` with the prerequisites in [`Dockerfile.agentic`](../../Dockerfile.agentic). Keep glibc compatibility, Python 3.12 through uv, build tools, archive utilities and non-root execution; the original three-package list no longer supports the stack.

Node 20 reached end of life on 2026-04-30; Node 24 is supported through 2028-04-30 ([official release schedule](https://github.com/nodejs/Release/blob/main/schedule.json)). Native macOS acceptance uses Node 24 too; Arch follows its rolling Node package. Prefer supported runtimes and successful provisioning over obsolete image-size comparisons. The Node compatibility floor remains 20, not a recommendation to deploy it.

Validate fresh installation, explicit isolated update and non-updating checks in the same acceptance HOME. The [runbook](../../README.md#clean-platform-acceptance) records verification scope; historical results below do not prove this runtime change.

## Historical context
A fresh environment must install all agent CLIs and MCP tooling in a clean container and pass a smoke test. The image should be small, but correctness and installer compatibility come first.

## Original decision
Use `node:20-bullseye-slim` as the base image in `Dockerfile.agentic` and add only these packages:
- `ca-certificates`
- `curl`
- `git`

Install `uv` with `https://astral.sh/uv/install.sh`. Add `.dockerignore` to keep the compose build context small for local and CI image rebuilds.
## Historical alternatives considered

1. **`node:22-bullseye-slim`**
   - Rejected: larger than `node:20-bullseye-slim` in this environment, with no compatibility gain.

2. **`node:20-bullseye-slim` (selected)**
   - Accepted: passes the full fresh-install smoke test at ~329MB.

3. **`node:20-alpine`/`node:22-alpine`**
   - Rejected: Hermes and OMP hit installer and runtime incompatibilities in fresh-environment checks.

4. **`node:20-slim` / `node:20-bookworm-slim`**
   - Rejected: larger for this stack in current measurements, with no reliability gain over bullseye-slim.

## Original rationale
- The `hermes` and `omp` install flows depend on installer behavior and shared runtime expectations that were unstable on musl-based images.
- Removing `ca-certificates` breaks the HTTPS bootstrap for `uv`.
- The image is only as small as the tested compatibility floor above allows. It is larger than the Alpine images.

- Fresh installs pass end-to-end smoke checks in non-interactive mode.
- `.dockerignore` keeps the compose build context small, so rebuilds are faster.
- Before changing base tags, re-run `docker-smoke-test.sh` and compare image size.
