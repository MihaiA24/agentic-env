# Agentic environment tools

This folder packages commands that provision and update a local multi-agent tooling stack.

Docs:
- [Stack overview](docs/stack-overview.md) – the landscape: which layers the stack has, which alternatives were surveyed per layer, and where each survey lives.
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
    - caveman and the vendored pstack skills (global)
    - `codebase-memory-mcp` (UI install supported)
    - `agentmemory` (CLI + Hermes MCP config)
  - Skill packs are driven by the bundled `agentic_env/skill-packs.json` default with:
    - `packs` entries whose `source` is `owner/repo#<tag>` (pinned; `skills add` clones that tag) or `./<dir>` (a copy vendored inside the package, installed as a local path; pstack lives at `agentic_env/vendored/pstack`, provenance in its `UPSTREAM.md`, ADR-0010). Each pack can define optional `skills` (array of specific skill names) to install only those from that pack by default.
      The roster's roles, triggers and exclusions: `DECISIONS_AI_TOOLING.md` §6; review standards: `CODING_STANDARDS.md`.
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
      - `~/.hermes/config.yaml` is parsed with PyYAML (the same library Hermes writes it with); malformed YAML or a non-mapping root is rejected without writing. When entries are added, the file is re-serialized: scalar types and structure are preserved, formatting is normalized and comments are dropped (a `.agentic-env.bak` copy is kept).
    - OMP: `codebase-memory-mcp` only, written gated (kept in `disabledServers`, enable per session); `agentmemory` and `lean-ctx` are excluded — stale entries are removed and both names stay in `disabledServers` so OMP's `~/.claude.json` import cannot mount them (ADR-0006/ADR-0009)
  - Existing selected MCP entries are validated, not repaired: a mismatched command, arguments, or Hermes memory provider is reported for manual correction and fails configuration without rewriting that file. Missing entries are added only when the file is otherwise valid; unrelated settings are preserved.
  - Adds matching global skills, with the same OMP exclusions.
  - Seeds `~/.omp/agent/config.yml` from the stack contract when absent (mnemopi memory, compaction handoff @ 150K, verification/canary hook extensions, `enableClaudeUser: true` + `enableAgentsUser: false`); when present, verifies the contract settings and reports drift without rewriting user YAML.
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
  - Reinstalls installed components without interactive prompts: floating ones move to the current latest, fixed-identity ones (Hermes, `codebase-memory-mcp`) stay at the reviewed artifact:
    - `hermes`, `omp`, `codex`, `claude`, `skills` CLI, `codebase-memory-mcp`, `agentmemory` CLI
  - Ends with `agentic-stack-doctor`; a mandatory-check failure makes the update exit non-zero.
  - Does not self-update `agentic-env`; use `uv tool upgrade agentic-env`.
- `agentic-stack-doctor`
  - Read-only diagnosis of the stack contract. Binary checks are version floors: at or above the reviewed version passes, below fails. Mandatory = the OMP layer (binaries, both `mcp.json` roots wired + gated incl. the `node_repl` built-in, excluded servers absent there and in `~/.claude.json`, no read-interception prose incl. `~/.claude.json`, `config.yml` contract, hooks registered once and present, curated skill roster, no `lean-ctx` skill dir). Hermes wiring (incl. a stale `lean-ctx` entry) and secondary-agent binaries only warn (`TODO secondary`). Exit 1 only on a mandatory failure; prints corrective guidance per failure; never repairs.
  - Checks actual managed MCP definitions and the compaction method order (`handoff`, `remote`, `soft`), not just entry names. Existing definition mismatches require manual correction; rerunning the add-missing-only configurator does not repair them.
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

Unit tests: `uv run pytest -q` (pytest comes from the `dev` dependency group in `pyproject.toml`).

### Version policy

Reviewed versions in `agentic_env/stack_metadata.py` are **floors** (`STACK_VERSION_FLOORS`), not exact pins.

- Install fetches the latest release of each floating component and fails if the result is below the floor; a host running ahead of the review is compliant. The `npx` skills fallback verifies its CLI version before installing any skill pack and fails closed if the version cannot be read.
- Claude Code installs from its `latest` channel, not the delayed `stable` channel.
- `agentic-update-stack` reinstalls the floating components unconditionally, so every run lands on the current latest.
- Two components do not float: Hermes (installer fetched at commit `HERMES_INSTALL_COMMIT`, which refuses to roll a checkout backwards) and `codebase-memory-mcp` (per-arch SHA256-pinned release archives). They move only when this repo's reviewed metadata does.
- Remote install scripts stay checksum-pinned regardless of which version they install; npm references install `@latest` and carry a written reason in the remote contract.
- Floors are raised at review time to the latest stable release, together with any installer checksum and release-asset checksum change.
- Installed skill-pack contents are not advanced to floating upstream revisions; packs move by tag (or by re-copy, for the vendored pstack pack).
- Do not call `agentmemory upgrade` here. That command prompts to re-run the `iii-engine` installer and can mutate the current workspace when `package.json` is present. Run it manually when intentionally refreshing the `iii-engine` runtime.


## Runbooks


### 1) Smoke validate from scratch (recommended)

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose up --build --force-recreate --exit-code-from fresh-install fresh-install
```

`--force-recreate` matters: otherwise Compose restarts the previous container with its retained installation. Acceptance runs as an ordinary user in an isolated HOME, with a user-writable npm prefix and the checkout mounted read-only. No provider credentials are required.

For Arch Linux x86_64:

```bash
docker compose --profile arch up --build --force-recreate --exit-code-from fresh-install-arch fresh-install-arch
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

This starts a fresh image, not a provisioned stack. Inside that same container:

```sh
sh ./clean-acceptance.sh
# Recheck the retained installation without installing again:
SKIP_INSTALL=1 sh ./clean-acceptance.sh
```

The wrapper prints its isolated HOME. Exiting the `--rm` container discards it.

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

Use `SKIP_INSTALL=1 sh ./docker-smoke-test.sh` for strict checks against this already-provisioned host. For native acceptance without using existing workstation configuration, use the isolated macOS procedure below.


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

If configuration reports malformed YAML or an existing MCP definition mismatch, correct the named fields in `~/.hermes/config.yaml` manually. The expected commands and pinned arguments are defined by `MCP_SERVERS` in `agentic_env/configure_agent_mcps.py`; the configurator does not repair existing entries.

To explicitly select the memory provider and then add any missing entries:

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

## Clean-platform acceptance

Files:
- `Dockerfile.agentic` – Debian bookworm prerequisites
- `Dockerfile.arch` – Arch Linux rolling prerequisites
- `docker-compose.yml` – ordinary-user container runs with a read-only checkout
- `clean-acceptance.sh` – isolated HOME, PATH, npm/uv/XDG state, and clean preconditions
- `docker-smoke-test.sh` – shared installation and verification contract
- `.dockerignore` – trims compose build context for faster local/CI builds


### Verified acceptance

[Run 34526778331](https://github.com/MihaiA24/.dotfiles/actions/runs/34526778331) passed on 2026-09-10 at code commit [`2cb1f08f9d0a7538ecef12e7532dfaee554a6400`](https://github.com/MihaiA24/.dotfiles/commit/2cb1f08f9d0a7538ecef12e7532dfaee554a6400). Each job provisioned an empty, isolated HOME as an ordinary user, then repeated the complete checks with `SKIP_INSTALL=1` against the retained installation.

| Recorded environment | Architecture | Fresh install | Checks-only |
| --- | --- | --- | --- |
| Native macOS 15.7.9, build 24G830 | arm64 | Passed | Passed |
| Arch Linux rolling container, `VERSION_ID=20260906.0.587075` | x86_64 | Passed | Passed |
| Debian GNU/Linux 12 (bookworm) container | x86_64 | Passed | Passed |

Both Linux containers used the Ubuntu runner's `6.17.0-1022-azure` kernel; this is distro-userland evidence, not native distro-boot evidence. Direct CachyOS verification remains deferred. Intel macOS is outside acceptance scope. Reviewed component versions and installer checksums were unchanged.

### CI contract

`.github/workflows/agentic-env-smoke-test.yml` defines:

| Environment | Execution | Coverage |
| --- | --- | --- |
| Debian bookworm x86_64 | `node:20-bookworm-slim` container on Ubuntu | Existing Linux baseline |
| macOS 15 arm64 | Native `macos-15` GitHub runner | Apple Silicon only |
| Arch Linux x86_64 | Official `archlinux:base` container on Ubuntu | Arch-family proxy, not direct CachyOS verification |

Push and pull-request triggers cover `agentic-env/**`, `omp/hooks/**`, and the workflow itself. `workflow_dispatch` remains available through **Actions → Agentic env smoke test → Run workflow**. A `unit` job (`uv run --frozen pytest -q` in `agentic-env/`) gates the three acceptance jobs: they are skipped when it fails (#38). Every acceptance job runs the same smoke contract twice: a fresh installation, then checks-only against that retained installation; a failed check fails its job.

Prerequisites are prepared before provisioning: Python 3.12+, Node.js 20+/npm, uv, curl, git, CA certificates, shell/archive utilities, and C/C++ build tools. Arch uses `pacman -Syu` because it is rolling. Containers require Docker Engine and Compose with amd64 support (native or emulated). Native macOS requires working Command Line Tools/Xcode.

The wrapper rejects root, the caller's real HOME, nonempty fresh acceptance directories, and preexisting agent commands. It clears inherited credentials/configuration, redirects user installation and cache paths, and uses hook resources from the checkout through `AGENTIC_DOTFILES_ROOT`. OS release, architecture, revision, run identity, and component versions are printed in the job log. No provider API key is required.

### CI badge / workflow links
- Workflow page: https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml
- Badge (SVG): https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg
  - Markdown:
    - `[![Agentic env smoke test](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml/badge.svg)](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml)`

### Run full fresh install test

Use the Debian or Arch commands in Runbook 1 above. Both force a new container; neither relies on an already-installed stack.

### Run native Apple Silicon acceptance

On a macOS arm64 machine with Homebrew and working Command Line Tools:

```bash
cd /path/to/your/dotfiles/agentic-env
test "$(uname -m)" = arm64
brew install uv python@3.12 node@20 xz ca-certificates
export AGENTIC_PREREQ_PATH="$(brew --prefix uv)/bin:$(brew --prefix python@3.12)/libexec/bin:$(brew --prefix node@20)/bin:$(brew --prefix xz)/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export AGENTIC_SMOKE_HOME="$(mktemp -d "${TMPDIR:-/tmp}/agentic-env-acceptance.XXXXXX")"
sh ./clean-acceptance.sh
# Same HOME and prerequisite PATH, no reinstall:
SKIP_INSTALL=1 sh ./clean-acceptance.sh
```

The acceptance HOME is retained for inspection/checks-only. Start another fresh acceptance run with a new empty directory. The hosted job prepares Python, Node, and uv with their setup actions instead of Homebrew; it asserts native arm64 before provisioning.

### Run checks only (skip installs)

Checks-only needs the **same already-provisioned environment**. It cannot validate an installation discarded by container recreation. For a retained Debian container:

```bash
cd /path/to/your/dotfiles/agentic-env
docker compose run --build -d --name agentic-env-debian fresh-install sleep infinity
docker exec agentic-env-debian /bin/sh ./clean-acceptance.sh
docker exec -e SKIP_INSTALL=1 agentic-env-debian /bin/sh ./clean-acceptance.sh
# Remove only this disposable acceptance container when finished:
docker rm -f agentic-env-debian
```

For Arch, use `docker compose --profile arch run --build -d --name agentic-env-arch fresh-install-arch sleep infinity`, then the same `docker exec` commands with `agentic-env-arch`. Compose forwards `SKIP_INSTALL`, but setting it while creating a fresh container is not valid checks-only evidence.

### Current smoke contract
The run is successful only if all checks pass:
1. `uv tool install --force .` succeeds using the absolute prerequisite Python path captured before bootstrap.
2. `agentic-bootstrap` succeeds (its final phase is `agentic-stack-doctor`).
3. All six package module entry points load and expose help through `uv run --frozen ... python -m agentic_env.<module> --help`, using that same interpreter rather than Hermes' managed Python 3.11.
4. Binary checks pass for:
   - `agentic-*` entry points incl. `agentic-stack-doctor`
   - `hermes`, `omp`, `codex`, `claude`, `codebase-memory-mcp`, `agentmemory`
5. `agentic-stack-doctor` exits 0 — the OMP mandatory contract:
   - `~/.omp/agent/mcp.json` and `~/.pi/agent/mcp.json` contain the reviewed `codebase-memory-mcp` command/arguments, gated in `disabledServers` together with the `node_repl` built-in; `agentmemory` and `lean-ctx` are absent from `mcpServers` (also in `~/.claude.json`) and remain disabled on both OMP roots
   - no read-interception prose in the OMP MCP files or `~/.claude.json`
   - `~/.omp/agent/config.yml` matches the contract, including compaction method order `handoff`, `remote`, `soft`; each hook is registered once with its file present
   - curated `default` skill roster present; `codebase-memory-mcp` and `ponytail` descriptors in the OMP skill roots; no `lean-ctx` skill dir
6. Hermes config checks pass:
   - `~/.hermes/config.yaml` contains the reviewed commands and arguments for `codebase-memory-mcp` and `agentmemory`, plus `memory.provider: agentmemory` (a stale `lean-ctx` entry is a doctor warning, not a smoke failure)
   - matching `codebase-memory-mcp`, `agentmemory`, and `ponytail` descriptors exist under `~/.hermes/skills`; missing descriptors fail smoke even though the doctor only warns
7. The skills CLI reports a version at or above the reviewed floor through `npx --yes skills@latest --version`; fresh provisioning does not require a global `skills` binary.
8. On Linux checks-only runs (`SKIP_INSTALL=1`), `agentic-update-stack` exits 0 against the already-provisioned HOME: every floating component reinstalls to the current latest and stays at or above its floor. Skipped on macOS so the shared runner IP does not make a second unauthenticated `api.github.com` request per run.

## Design and tradeoffs
- **Container bases:** `node:20-bookworm-slim` for the Debian baseline and official `archlinux:base` for rolling Arch x86_64; macOS acceptance executes natively.
- `.dockerignore` in `agentic-env/` trims compose build context for faster local/CI builds.
- `node:20-bullseye-slim` was the original minimum; the image moved to `bookworm-slim` in `b49fa8f` when it gained `xz-utils`/`libatomic1`/`unzip` for Hermes' Node 26 + bun runtime (ADR-0001 records the bullseye-era measurements).
- `alpine` images were rejected due installer/runtime incompatibilities (`omp`/Hermes path).
## Dependencies
- `rich` and `pyyaml` are required and are installed automatically as package dependencies.
