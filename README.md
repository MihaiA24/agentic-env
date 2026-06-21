# Agentic environment scripts

This folder provisions and updates a local multi-agent tooling stack.

Docs:
- [Project memory stack](docs/project-memory-stack.md) – guide and one-repo template for `lean-ctx`, `codebase-memory-mcp`, `agentmemory`, `CONTEXT.md`, and ADR usage.

- `install-agents.py`
  - Installs/reinstalls:
    - Hermes Agent (`hermes`)
    - OMP / Oh My Pi (`omp`)
    - OpenAI Codex CLI (`codex`)
    - Claude Code (`claude`)
- `install-skills-mcps.py`
  - Installs:
    - mattpocock skills pack (global)
    - `codebase-memory-mcp` (UI install supported)
    - `lean-ctx`
    - `agentmemory` (CLI + Hermes MCP + OMP extension config)
- `configure-agent-mcps.py`
  - Adds selected project-memory MCP servers to Hermes and OMP global config when missing:
    - `lean-ctx`
    - `codebase-memory-mcp`
    - `agentmemory`
  - Adds matching global skills for Hermes and OMP when missing.
- `update-agentic-stack.py`
  - Updates installed components:
    - `hermes`, `omp`, `codex`, `claude`, `skills`, `codebase-memory-mcp`, `lean-ctx`, `agentmemory`

## Quick usage (from this folder)
```bash
cd /path/to/your/dotfiles/agentic-env
uv run ./install-agents.py
uv run ./install-skills-mcps.py
uv run ./configure-agent-mcps.py
uv run ./update-agentic-stack.py
```

Equivalent shorthand:
- `uv run ./install-agents.py`
- `uv run ./install-skills-mcps.py`
- `uv run ./configure-agent-mcps.py`
- `uv run ./update-agentic-stack.py`

## Fresh environment in Docker (smoke-test enabled)

Files:
- `Dockerfile.agentic` – minimal container base and runtime dependencies
- `docker-compose.yml` – build + run contract
- `docker-smoke-test.sh` – verification script (fails non-zero if checks fail)
- `.dockerignore` – trims compose build context for faster local/CI builds



### CI contract
- `.github/workflows/agentic-env-smoke-test.yml` runs the full fresh-install smoke test on:
  - `push` / `pull_request` when files under `agentic-env/` change
  - `workflow_dispatch` for on-demand checks from Actions
  - Manual run:
    - GitHub UI: **Actions → Agentic env smoke test → Run workflow** (select branch, optional).
  - Command: `docker compose up --build --exit-code-from fresh-install`
  - Any failing check exits non-zero and fails the workflow.

### CI badge / workflow links
- Workflow page: https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml
- Badge (SVG): https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg
  - Markdown:
    - `[![Agentic env smoke test](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg)](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml)`

### Run full fresh install test
```bash
cd /path/to/your/dotfiles/agentic-env
docker compose up --build --exit-code-from fresh-install
```

### Run checks only (skip installs)
```bash
cd /path/to/your/dotfiles/agentic-env
SKIP_INSTALL=1 docker compose up --build --exit-code-from fresh-install
```

You can also run the script directly:
```bash
docker run --rm -v "$PWD":/workspace agentic-env-fresh-install /bin/sh ./docker-smoke-test.sh
```

### Current smoke contract
The run is successful only if all checks pass:
1. `install-agents.py --all --yes` succeeds.
2. `install-skills-mcps.py --all-mcps --yes` succeeds.
3. `configure-agent-mcps.py --yes` succeeds.
4. Binary checks pass for:
   - `hermes`, `omp`, `codex`, `claude`, `lean-ctx`, `codebase-memory-mcp`, `agentmemory`
5. Hermes and OMP config checks pass:
   - `~/.hermes/config.yaml` contains `lean-ctx`, `codebase-memory-mcp`, and `agentmemory` MCP entries
   - `~/.pi/agent/settings.json` includes the `agentmemory` extension
   - `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` contain the selected MCP entries
   - global skill files exist under Hermes and OMP skill roots

## Design and tradeoffs
- **Chosen base image:** `node:20-bullseye-slim`
- **Measured image size:** about **329MB** for `agentic-env-fresh-install`.
- `.dockerignore` in `agentic-env/` trims compose build context for faster local/CI builds.
- `node:20-bullseye-slim` is the minimum tested image that keeps Hermes/OMP installers compatible in non-interactive fresh installs.
- `alpine` images were rejected due installer/runtime incompatibilities (`omp`/Hermes path).
- `bookworm`/other slim tags were tested but were larger with no reliability gain.
## Dependencies
- `rich` is required and is installed automatically via uv script metadata.
