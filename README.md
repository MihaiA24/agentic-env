# Agentic environment tools

This folder packages commands that provision and update a local multi-agent tooling stack.

Docs:
- [Project memory stack](docs/project-memory-stack.md) – guide and one-repo template for `lean-ctx`, `codebase-memory-mcp`, `agentmemory`, `CONTEXT.md`, and ADR usage.

- `agentic-install-agents`
  - Installs/reinstalls:
    - Hermes Agent (`hermes`)
    - OMP / Oh My Pi (`omp`)
    - OpenAI Codex CLI (`codex`)
    - Claude Code (`claude`)
- `agentic-install-skills-mcps`
  - Installs:
    - mattpocock skills pack (global)
    - ponytail skill bundle (global, agent-dispatch)
    - `codebase-memory-mcp` (UI install supported)
    - `lean-ctx`
    - `agentmemory` (CLI + Hermes MCP + OMP extension config)
  - Skill packs are driven by the bundled `agentic_env/skill-packs.json` default with:
    - `packs` entries that can define optional `skills` (array of specific skill names)
      to install only those from that pack by default.
    - `profiles` (named pack sets).
  - Supported options:
    - `--skill-pack` (comma-separated, repeated) to choose packs.
    - `--skill` (comma-separated, repeated; filters each selected pack).
    - `--skill-agent` (comma-separated, repeated; defaults to `hermes,claude,codex`).
    - `--skill-profile` (for example: `default`, `minimal`, `agentic-only`).
    - `--skill-config PATH` to use a custom skill-pack config.
    - `--all-skills` to install every configured pack.
  - Example:
    - `agentic-install-skills-mcps --all-skills --skill-agent hermes,claude,codex --yes`
  - Skill config JSON keeps the same shape as the bundled default.
    - Packs without `skills` install full pack contents by default.
    - When `skills` exists and you pass `--skill`, installs the intersection of both lists.
- `agentic-configure-agent-mcps`
  - Adds selected project-memory MCP servers to Hermes and OMP global config when missing:
    - `lean-ctx`
    - `codebase-memory-mcp`
    - `agentmemory`
  - Adds matching global skills for Hermes and OMP when missing.
- `agentic-bootstrap`
  - One-shot onboarding in phase order:
    - installs agent CLIs
    - installs MCP tooling and matching skills
    - configures MCP servers and global skills
  - defaults:
    - `--skill-profile default`
    - all install/configure targets
    - non-interactive execution with phase `--yes` flags
  - split execution with:
    - `--skip-install-agents`
    - `--skip-install-skills`
    - `--skip-configure`
    - `--configure-no-skills`
- `agentic-update-stack`
  - Converges installed components to the reviewed versions in `agentic_env/stack_metadata.py` without interactive prompts:
    - `hermes`, `omp`, `codex`, `claude`, `skills` CLI, `codebase-memory-mcp`, `lean-ctx`, `agentmemory` CLI
  - Does not self-update `agentic-env`; use `uv tool upgrade agentic-env`.
- Root `*.py` files remain `uv run --script` compatibility wrappers for development and smoke checks.
- `setup_helpers.sh`
  - Shared quiet/verbose `run_cmd` helper used by shell setup scripts and the Docker smoke test.

## Quick usage

Install the command set from this checkout:

```bash
cd /path/to/your/dotfiles/agentic-env
uv tool install --force .
agentic-bootstrap --yes
agentic-update-stack

# Split steps (legacy):
# agentic-install-agents --all --yes
# agentic-install-skills-mcps --all-mcps --yes
# agentic-configure-agent-mcps --yes
```

Development compatibility wrappers remain available from the checkout:

```bash
uv run --script bootstrap.py
uv run --script install-agents.py
uv run --script install-skills-mcps.py
uv run --script configure-agent-mcps.py
uv run --script update-agentic-stack.py
```

### Update policy

`agentic-update-stack` is an unattended convergence command, not a latest-version updater.

- Install and update use the same immutable commit, release, or npm package pins from `agentic_env/stack_metadata.py`.
- Every changed component is checked with its version command; a mismatch fails the run.
- Upgrading the curated stack requires a reviewed metadata, installer checksum, and release-asset checksum change.
- `skills` refers to the pinned CLI only; installed skill-pack contents are not advanced to floating upstream revisions.
- Do not call `agentmemory upgrade` here. That command prompts to re-run the `iii-engine` installer and can mutate the current workspace when `package.json` is present. Run it manually when intentionally refreshing the `iii-engine` runtime.


## Runbooks


### 1) Smoke validate from scratch (recommended)

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose up --build --exit-code-from fresh-install
```

What this runbook validates:
- installs from clean container
- verifies `hermes`, `omp`, `codex`, `claude`, `lean-ctx`, `codebase-memory-mcp`, `agentmemory` are callable
- verifies Hermes/OMP MCP artifacts and global skills are present

### 2) Interactive container validation (same checkbook, inspectable)

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose run --rm --entrypoint sh fresh-install
```

Important: this opens a **fresh image**. It does not pre-install `hermes`, `lean-ctx`, or any MCP tooling.
Run install/configure commands first, then smoke checks.

Inside container:

```bash
cd /workspace
# Install all components into the container first
uv tool install --force .
agentic-bootstrap --yes

# Quick runtime checks for each CLI
hermes --help
omp --help
lean-ctx doctor
agentmemory doctor
codebase-memory-mcp --version
```

You can also run all steps in one command:

```bash
docker compose run --rm --entrypoint sh fresh-install -lc "cd /workspace && uv tool install --force . && agentic-bootstrap --yes && hermes --help && omp --help && lean-ctx doctor && agentmemory doctor && codebase-memory-mcp --version"
```

### 3) Host-side install + configure smoke (no docker)

If you need to run on the host machine directly:

```bash
cd /path/to/your/dotfiles/agentic-env
uv tool install --force .
agentic-bootstrap --yes
lean-ctx doctor
agentmemory doctor
codebase-memory-mcp --version
hermes --help
omp --help
```

Use `./docker-smoke-test.sh` when you want the strict full contract assertions from one command.


### 4) Check MCP visibility inside Hermes

In a working Hermes install:

```bash
hermes mcp list
```

If you see the two entries below, they are wired:
- `agentmemory` (transport: `npx`)
- `codebase-memory-mcp` (transport: `codebase-memory-mcp`)

Functional checks:

```bash
hermes mcp test agentmemory
hermes mcp test codebase-memory-mcp
```

If `hermes mcp list` crashes, your `~/.hermes/config.yaml` likely has malformed MCP YAML.
Repair by adding clean blocks:

```bash
hermes config set memory.provider agentmemory
agentic-configure-agent-mcps --yes --server lean-ctx --server codebase-memory-mcp --server agentmemory --agent hermes
```

Then rerun `hermes mcp list`.


### 5) Existing-project onboarding (no full fresh bootstrap)

From an already-installed machine/CI agent environment, wire the memory MCPs in-place:

```bash
cd /path/to/your/dotfiles/agentic-env
agentic-install-skills-mcps --all-skills --all-mcps --yes
agentic-configure-agent-mcps --yes
```

Then from any repo:

```bash
hermes mcp list
hermes mcp test agentmemory
hermes mcp test codebase-memory-mcp
```

Ponytail (`ponytail`) is installed as a **global, language-agnostic skill bundle** via
`agentic-install-skills-mcps` and is available to all supported harnesses that read user
global skills.

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
1. `uv tool install --force .` succeeds.
2. `agentic-bootstrap --yes` succeeds.
3. Root script wrappers load and expose help through `uv run --script`.
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
- `rich` is required and is installed automatically through package dependencies or uv script metadata.
