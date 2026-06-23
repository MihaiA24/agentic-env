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
    - ponytail skill bundle (global, agent-dispatch)
    - `codebase-memory-mcp` (UI install supported)
    - `lean-ctx`
    - `agentmemory` (CLI + Hermes MCP + OMP extension config)
  - Skill packs are driven by `skill-packs.json` (default) with:
    - `packs` entries that can define optional `skills` (array of specific skill names)
      to install only those from that pack by default.
    - `profiles` (named pack sets).
  - Supported options:
    - `--skill-pack` (comma-separated, repeated) to choose packs.
    - `--skill` (comma-separated, repeated; filters each selected pack).
    - `--skill-agent` (comma-separated, repeated; defaults to `hermes,ohmipy,claude,codex`).
    - `--skill-profile` (for example: `default`, `minimal`, `agentic-only`).
    - `--all-skills` to install every configured pack.
  - Example:
    - `uv run ./install-skills-mcps.py --all-skills --skill-agent hermes,ohmipy,claude,codex --yes`
  - Skill config JSON (example):
    ```json
    {
      "packs": [
        {
          "name": "mattpocock",
          "source": "mattpocock/skills",
          "label": "mattpocock skills",
          "aliases": ["mattpocock", "mattpocock/skills"],
          "skills": ["ask", "tdd"]
        },
        {
          "name": "ponytail",
          "source": "DietrichGebert/ponytail",
          "label": "ponytail skill",
          "aliases": ["ponytail", "dietrichgebert/ponytail"]
        }
      ],
      "profiles": {
        "default": ["mattpocock", "ponytail"],
        "minimal": ["mattpocock"],
        "agentic-only": ["ponytail"]
      }
    }
    ```
    - Packs without `skills` install full pack contents by default.
    - When `skills` exists and you pass `--skill`, installs the intersection of both lists.
- `configure-agent-mcps.py`
  - Adds selected project-memory MCP servers to Hermes and OMP global config when missing:
    - `lean-ctx`
    - `codebase-memory-mcp`
    - `agentmemory`
  - Adds matching global skills for Hermes and OMP when missing.
- `update-agentic-stack.py`
  - Updates installed components without interactive prompts:
    - `hermes`, `omp`, `codex`, `claude`, `skills`, `codebase-memory-mcp`, `lean-ctx`, `agentmemory` CLI
- `setup_helpers.sh`
  - Shared quiet/verbose `run_cmd` helper used by shell setup scripts and the Docker smoke test.
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

### Update policy

`update-agentic-stack.py` is an unattended maintenance command.

- Use each tool's native updater when it supports one (`hermes update --yes`, `omp update`, `claude update`).
- Update npm-installed CLIs through npm (`codex`, `agentmemory`) instead of re-running curl installers.
- Do not call `agentmemory upgrade` here. That command prompts to re-run the pinned `iii-engine` installer and can mutate the current workspace when `package.json` is present. Run it manually when intentionally refreshing the `iii-engine` runtime.


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
uv run --script install-agents.py --all --yes
uv run --script install-skills-mcps.py --all-mcps --yes
uv run --script configure-agent-mcps.py --yes

# Quick runtime checks for each CLI
hermes --help
omp --help
lean-ctx doctor
agentmemory doctor
codebase-memory-mcp --version
```

You can also run all steps in one command:

```bash
docker compose run --rm --entrypoint sh fresh-install -lc "cd /workspace && uv run --script install-agents.py --all --yes && uv run --script install-skills-mcps.py --all-mcps --yes && uv run --script configure-agent-mcps.py --yes && hermes --help && omp --help && lean-ctx doctor && agentmemory doctor && codebase-memory-mcp --version"
```

### 3) Host-side install + configure smoke (no docker)

If you need to run on the host machine directly:

```bash
cd /path/to/your/dotfiles/agentic-env
uv run ./install-agents.py --all --yes
uv run ./install-skills-mcps.py --all-mcps --yes
uv run ./configure-agent-mcps.py --yes
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
uv run ./configure-agent-mcps.py --yes --server lean-ctx --server codebase-memory-mcp --server agentmemory --agent hermes
```

Then rerun `hermes mcp list`.


### 5) Existing-project onboarding (no full fresh bootstrap)

From an already-installed machine/CI agent environment, wire the memory MCPs in-place:

```bash
cd /path/to/your/dotfiles/agentic-env
uv run ./install-skills-mcps.py --all-skills --all-mcps --yes
uv run ./configure-agent-mcps.py --yes
```

Then from any repo:

```bash
hermes mcp list
hermes mcp test agentmemory
hermes mcp test codebase-memory-mcp
```

Ponytail (`ponytail`) is installed as a **global, language-agnostic skill bundle** via
`install-skills-mcps.py` and is available to all supported harnesses that read user
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
