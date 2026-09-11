# Agentic environment tools

This folder packages commands that provision and update a local multi-agent tooling stack.

Docs:
- [Project memory stack](docs/project-memory-stack.md) – guide and one-repo template for `codebase-memory-mcp`, `agentmemory`, `CONTEXT.md`, and ADR usage.
- [Decisions](DECISIONS_AI_TOOLING.md) – the operative stack contract, one section per layer (Decided → Why → Rejected → Revisit → Wiring); `lean-ctx` was removed stack-wide (ADR-0009).

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
    - `agentmemory` (CLI + Hermes MCP config)
  - Skill packs are driven by the bundled `agentic_env/skill-packs.json` default with:
    - `packs` entries whose `source` is `owner/repo#<tag>` (pinned; `skills add` clones that tag) and which can define optional `skills` (array of specific skill names)
      to install only those from that pack by default. `cursor/plugins` (pstack) publishes no tags and floats on `main`.
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
  - Adds selected project-memory MCP servers when missing:
    - Hermes: `codebase-memory-mcp` and `agentmemory`
      - Accepts scalar block lists, including Hermes/PyYAML's indentless style. List mappings, nested lists, and unsupported list syntax are rejected without writing. When entries are added, the writer preserves scalar types and empty mappings but normalizes formatting and drops comments.
    - OMP: `codebase-memory-mcp` only, written gated (kept in `disabledServers`, enable per session); `agentmemory` and `lean-ctx` are excluded — stale entries are removed and both names stay in `disabledServers` so OMP's `~/.claude.json` import cannot mount them (ADR-0006/ADR-0009)
  - Adds matching global skills, with the same OMP exclusions.
  - Converges `~/.omp/agent/config.yml` to the stack contract: seeds it when absent (mnemopi memory, compaction handoff @ 150K, verification/canary hook extensions, `enableClaudeUser: true` + `enableAgentsUser: false`); when present, verifies the contract settings and reports drift without rewriting user YAML.
- `agentic-bootstrap`
  - One-shot onboarding in phase order:
    - installs agent CLIs
    - installs MCP tooling and matching skills
    - configures MCP servers and global skills
    - runs `agentic-stack-doctor` (a mandatory-check failure fails the bootstrap)
  - defaults:
    - `--skill-profile default`
    - all install/configure targets
    - non-interactive execution with phase `--yes` flags
  - split execution with:
    - `--skip-install-agents`
    - `--skip-install-skills`
    - `--skip-configure`
    - `--skip-doctor`
    - `--configure-no-skills`
- `agentic-update-stack`
  - Converges installed components to the reviewed versions in `agentic_env/stack_metadata.py` without interactive prompts:
    - `hermes`, `omp`, `codex`, `claude`, `skills` CLI, `codebase-memory-mcp`, `agentmemory` CLI
  - Ends with `agentic-stack-doctor`; a mandatory-check failure makes the update exit non-zero.
  - Does not self-update `agentic-env`; use `uv tool upgrade agentic-env`.
- `agentic-stack-doctor`
  - Read-only diagnosis of the stack contract. Mandatory = the OMP layer (binaries, both `mcp.json` roots wired + gated incl. the `node_repl` built-in, excluded servers absent there and in `~/.claude.json`, no read-interception prose incl. `~/.claude.json`, `config.yml` contract, hooks registered once and present, curated skill roster, no `lean-ctx` skill dir). Hermes wiring (incl. a stale `lean-ctx` entry) and the Hermes / Claude Code / Codex binaries only warn (`TODO secondary`). Exit 1 only on a mandatory failure; prints the corrective command per failure; never repairs.
- Checkout development runs the package modules through `uv run python -m agentic_env.<module>`; installed workflows use the `agentic-*` commands.
- `setup_helpers.sh`
  - Shared quiet/verbose `run_cmd` helper used by shell setup scripts and the Docker smoke test.

## Quick usage

Install the command set from this checkout:

```bash
cd /path/to/your/dotfiles/agentic-env
uv tool install --force .
agentic-bootstrap
agentic-update-stack

# Split steps (legacy):
# agentic-install-agents --all --yes
# agentic-install-skills-mcps --all-mcps --yes
# agentic-configure-agent-mcps --yes
```

Run package modules directly when developing from the checkout:

```bash
uv run python -m agentic_env.bootstrap
uv run python -m agentic_env.install_agents
uv run python -m agentic_env.install_skills_mcps
uv run python -m agentic_env.configure_agent_mcps
uv run python -m agentic_env.update_agentic_stack
uv run python -m agentic_env.stack_doctor
```

### Update policy

`agentic-update-stack` is an unattended convergence command, not a latest-version updater.

- Install and update use the same immutable commit, release, or npm package pins from `agentic_env/stack_metadata.py`.
- Every changed component is checked with its version command; a mismatch fails the run.
- Exception: a Hermes checkout already *ahead* of `HERMES_COMMIT` is left alone (the Hermes installer refuses to roll an install backwards; drift above the pin is tolerated). The doctor still warns until the pin catches up.
- Upgrading the curated stack requires a reviewed metadata, installer checksum, and release-asset checksum change.
- `skills` refers to the pinned CLI only; installed skill-pack contents are not advanced to floating upstream revisions.
- Do not call `agentmemory upgrade` here. That command prompts to re-run the `iii-engine` installer and can mutate the current workspace when `package.json` is present. Run it manually when intentionally refreshing the `iii-engine` runtime.


## Runbooks


### 1) Smoke validate from scratch (recommended)

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose up --build --force-recreate --exit-code-from fresh-install
```

`--force-recreate` matters: with unchanged image layers, `compose up` restarts the previous container and its `/root` state, which is no longer a fresh install.

If a GitHub clone fails inside the container with "Authentication failed" / "could not read Username" for a public repo while the host clones fine (the Hermes installer's `hermes-agent` clone and `skills add` both hit it), the container's git 2.39 is getting HTTP 401 on `git-upload-pack` over HTTP/2 from your network (seen 2026-09-02, not in CI). Run once with git forced to HTTP/1.1:

```bash
docker compose run --rm --build -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=http.version -e GIT_CONFIG_VALUE_0=HTTP/1.1 fresh-install
```

What this runbook validates:
- installs from clean container
- verifies `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `agentmemory` are callable
- runs `agentic-stack-doctor` (OMP mandatory contract) and checks Hermes MCP/skill artifacts

### 2) Interactive container validation (same checkbook, inspectable)

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose run --rm --entrypoint sh fresh-install
```

Important: this opens a **fresh image**. It does not pre-install `hermes` or any MCP tooling.
Run install/configure commands first, then smoke checks.

Inside container:

```bash
cd /workspace
# Install all components into the container first
uv tool install --force .
agentic-bootstrap

# Quick runtime checks for each CLI
hermes --help
omp --help
agentic-stack-doctor
agentmemory doctor
codebase-memory-mcp --version
```

You can also run all steps in one command:

```bash
docker compose run --rm --entrypoint sh fresh-install -lc "cd /workspace && uv tool install --force . && agentic-bootstrap && hermes --help && omp --help && agentmemory doctor && codebase-memory-mcp --version"
```

### 3) Host-side install + configure smoke (no docker)

If you need to run on the host machine directly:

```bash
cd /path/to/your/dotfiles/agentic-env
uv tool install --force .
agentic-bootstrap
agentic-stack-doctor
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
agentic-configure-agent-mcps --yes --server codebase-memory-mcp --server agentmemory --agent hermes
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

## Clean-host acceptance

Files:
- `Dockerfile.agentic` – minimal container base and runtime dependencies
- `Dockerfile.arch` – Arch prerequisites and an unprivileged user, without an installed agent stack
- `docker-compose.yml` – build + run contract
- `docker-smoke-test.sh` – verification script (fails non-zero if checks fail)
- `.dockerignore` – trims compose build context for faster local/CI builds



### CI contract

`.github/workflows/agentic-env-smoke-test.yml` preserves `push` / `pull_request`
triggers for changes under `agentic-env/`, `omp/hooks/`, or the workflow itself,
plus `workflow_dispatch`. Every job runs the same `docker-smoke-test.sh`;
bootstrap, CLI, doctor, and Hermes assertions are not relaxed by platform.

| Job | Environment | Architecture |
|---|---|---|
| Existing Debian smoke | `node:20-bookworm-slim` container on `ubuntu-latest` | x86_64 |
| Arch fresh install | `archlinux:base` container on `ubuntu-latest` | x86_64 |
| Native macOS fresh install | `macos-15` GitHub-hosted runner, no Linux container | arm64 |

Arch installs prerequisites with pacman: Python, Node/npm, uv, curl, git, CA
certificates, base-devel, unzip, and xz. Bootstrap runs as the unprivileged
`agentic` user with a user-writable npm prefix. Package sources are copied into
the image; host virtual environments, installed agents, and configuration are
not mounted. Only `omp/hooks` is mounted read-only. The `arch` profile keeps this
service out of the existing default Debian command.

macOS uses a new temporary HOME and XDG directories, a user-local npm prefix,
Node 20, and uv with Python 3.12 available. It does not restore a uv cache and
rejects preinstalled agent-stack commands on PATH. The runner provides curl,
git, certificates, and Xcode command-line tools. Neither added job needs
agent-provider credentials or configuration from a workstation.

Arch container evidence covers Arch userland, not a CachyOS image, CachyOS
kernel, or a clean CachyOS machine. A checks-only run on an existing CachyOS
device is separate evidence, not a fresh install. Intel macOS is not covered.
Both added environments print OS, architecture, and user identity in their logs.

### Run the Arch clean install locally

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose --profile arch run --rm --build -T fresh-install-arch
```

Every invocation creates a fresh container and removes it on exit; no installed
stack state is cached in the image. `archlinux:base` and pacman packages roll:
retain the image digest and logged OS identity when recording a run.

### Run native macOS acceptance

After the workflow change is present on a GitHub branch, use **Actions →
Agentic env smoke test → Run workflow**, or run from the repository:

```bash
gh workflow run agentic-env-smoke-test.yml --ref <branch>
```

This starts all three jobs, including native macOS. A local Linux container
cannot substitute for that Mac run; its success must be recorded separately.

### Recorded verification — 2026-09-11

| Environment | Result |
|---|---|
| Clean Arch container, x86_64, UID 1000 | **Passed:** the local Arch command above exited 0 with `Smoke test complete`, including bootstrap, all CLI checks, stack-doctor, and Hermes YAML assertions. |
| Existing CachyOS device, x86_64, kernel `7.2.4-1-cachyos` | **Failed:** checks-only command exited 1 with 12 mandatory doctor failures and missing `agentmemory`. This was not a clean install; no host bootstrap or repair was run. |
| Native macOS 15, arm64 | **Not executed:** workflow added and validated with actionlint; native provisioning requires a Mac runner. No successful macOS install is claimed. |

Arch reported `VERSION_ID=20260906.0.587075`; pacman supplied Python 3.14.7,
Node 26.8.2, and uv 0.12.13. The base image digest was
`archlinux:base@sha256:b944cc65c5f28665dfd5fdbf5ed2997c88f5bb4a0aefac7ee8a7ef01893e5ed9`.
The initial attempt passed bootstrap but failed to create `/workspace/.venv`;
making the copied workspace directory user-owned fixed the test environment,
and the complete fresh-install run then passed without changing stack pins.

The device failures included an OMP version mismatch, missing OMP MCP files,
configuration drift, unregistered hooks, missing curated skills/descriptors,
and stale `lean-ctx` configuration/skills. The script stopped at the doctor;
the separate Hermes YAML assertions did not run on the device.

### CI badge / workflow links
- Workflow page: https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml
- Badge (SVG): https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg
  - Markdown:
    - `[![Agentic env smoke test](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg)](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml)`

### Run full fresh install test
```bash
cd /path/to/your/dotfiles/agentic-env
docker compose up --build --force-recreate --exit-code-from fresh-install
```

### Check the existing device without installing the stack

```bash
cd /path/to/your/dotfiles/agentic-env
SKIP_INSTALL=1 uv run --frozen sh ./docker-smoke-test.sh
```

`uv run` supplies the provisioner's checkout entry points; `SKIP_INSTALL=1`
skips stack installation and configuration. Existing binaries must be on PATH.
This checks the current device, not a clean host. The script exits nonzero on
failure and does not repair drift; a doctor failure stops before the separate
Hermes YAML assertions.

### Current smoke contract
The run is successful only if all checks pass:
1. `uv tool install --force .` succeeds.
2. `agentic-bootstrap` succeeds (its final phase is `agentic-stack-doctor`).
3. All six package module entry points load and expose help through `uv run python -m agentic_env.<module> --help`.
4. Binary checks pass for:
   - `agentic-*` entry points incl. `agentic-stack-doctor`
   - `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `agentmemory`
5. `agentic-stack-doctor` exits 0 — the OMP mandatory contract:
   - `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` contain `codebase-memory-mcp`, gated in `disabledServers` together with the `node_repl` built-in; `agentmemory` and `lean-ctx` absent from `mcpServers` (also in `~/.claude.json`)
   - no read-interception prose in the OMP MCP files or `~/.claude.json`
   - `~/.omp/agent/config.yml` matches the contract; each hook registered once with its file present
   - curated `default` skill roster present; `codebase-memory-mcp` and `ponytail` descriptors in the OMP skill roots; no `lean-ctx` skill dir
6. Hermes config checks pass:
   - `~/.hermes/config.yaml` contains `codebase-memory-mcp` and `agentmemory` MCP entries and `memory.provider: agentmemory` (a stale `lean-ctx` entry is a doctor warning, not a smoke failure)

## Design and tradeoffs
- **Chosen base image:** `node:20-bookworm-slim` (Debian bookworm; the Linux smoke environment)
- **Measured image size:** about **329MB** for `agentic-env-fresh-install` on the earlier `bullseye-slim` base; not re-measured after the bookworm switch.
- `.dockerignore` in `agentic-env/` trims compose build context for faster local/CI builds.
- `node:20-bullseye-slim` was the original minimum; the image moved to `bookworm-slim` in `b49fa8f` when it gained `xz-utils`/`libatomic1`/`unzip` for Hermes' Node 26 + bun runtime (ADR-0001 records the bullseye-era measurements).
- `alpine` images were rejected due installer/runtime incompatibilities (`omp`/Hermes path).
## Dependencies
- `rich` is required and is installed automatically as a package dependency.
