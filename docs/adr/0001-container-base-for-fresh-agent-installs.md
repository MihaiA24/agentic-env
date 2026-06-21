# ADR 0001: Container base image for fresh agent-stack install

## Status
Accepted

## Context
Fresh environment setup must install all agent CLIs/MCP tooling from a clean container and exit with a passing smoke test. The image should be compact, but correctness and installer compatibility are mandatory.

## Decision
Use `node:20-bullseye-slim` as the base image in `Dockerfile.agentic`, with only these additional image packages:
- `ca-certificates`
- `curl`
- `git`
and install `uv` via `https://astral.sh/uv/install.sh`.
Add `agentic-env/.dockerignore` to keep compose build context lightweight during local and CI image rebuilds.
## Alternatives considered

1. **`node:22-bullseye-slim`**
   - Rejected: larger than `node:20-bullseye-slim` in this environment and not needed for compatibility gains.

2. **`node:20-bullseye-slim` (selected)**
   - Accepted: passes full fresh-install smoke test and keeps image size at ~329MB.

3. **`node:20-alpine`/`node:22-alpine`**
   - Rejected: installer/runtime incompatibilities for Hermes/OMP on fresh env checks.

4. **`node:20-slim` / `node:20-bookworm-slim`**
   - Rejected: materially larger for this stack in current measurements, with no reliability benefit over bullseye-slim.

## Rationale
- `hermes` and `omp` install flows depend on installer behavior and shared runtime expectations that were unstable on musl-based images.
- Removing `ca-certificates` breaks HTTPS bootstrap for `uv`.
- Keeping the image minimal is bounded by the tested compatibility floor above.

- Predictable bootstrap: fresh installs pass end-to-end smoke checks in non-interactive mode.
- Image size remains non-minimal relative to alpines, but remains small for the required compatibility.
- Build context is kept lightweight in compose by `agentic-env/.dockerignore` for faster rebuilds.
- Future upgrades should re-run `docker-smoke-test.sh` and compare image size before changing base tags.
