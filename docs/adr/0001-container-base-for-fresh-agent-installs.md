# ADR 0001: Container base image for fresh agent-stack install

## Status
Accepted

## Context
A fresh environment must install all agent CLIs and MCP tooling in a clean container and pass a smoke test. The image should be small, but correctness and installer compatibility come first.

## Decision
Use `node:20-bullseye-slim` as the base image in `Dockerfile.agentic` and add only these packages:
- `ca-certificates`
- `curl`
- `git`

Install `uv` with `https://astral.sh/uv/install.sh`. Add `agentic-env/.dockerignore` to keep the compose build context small for local and CI image rebuilds.
## Alternatives considered

1. **`node:22-bullseye-slim`**
   - Rejected: larger than `node:20-bullseye-slim` in this environment, with no compatibility gain.

2. **`node:20-bullseye-slim` (selected)**
   - Accepted: passes the full fresh-install smoke test at ~329MB.

3. **`node:20-alpine`/`node:22-alpine`**
   - Rejected: Hermes and OMP hit installer and runtime incompatibilities in fresh-environment checks.

4. **`node:20-slim` / `node:20-bookworm-slim`**
   - Rejected: larger for this stack in current measurements, with no reliability gain over bullseye-slim.

## Rationale
- The `hermes` and `omp` install flows depend on installer behavior and shared runtime expectations that were unstable on musl-based images.
- Removing `ca-certificates` breaks the HTTPS bootstrap for `uv`.
- The image is only as small as the tested compatibility floor above allows. It is larger than the Alpine images.

- Fresh installs pass end-to-end smoke checks in non-interactive mode.
- `agentic-env/.dockerignore` keeps the compose build context small, so rebuilds are faster.
- Before changing base tags, re-run `docker-smoke-test.sh` and compare image size.
