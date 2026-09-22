# Agentic environment tools

Install and maintain an OMP-primary, Hermes-secondary stack.

- [Decisions](DECISIONS_AI_TOOLING.md): operative policy and wiring.
- [Stack overview](docs/stack-overview.md): architecture and research index.
- [Project memory](docs/project-memory-stack.md): per-repo setup.

## Quick usage

Requires Python 3.12+, Node.js 20+/npm, uv, curl, git, CA certificates, shell/archive utilities, C/C++ build tools and the dotfiles checkout.

```bash
cd /path/to/your/dotfiles/agentic-env
uv tool install --force .
agentic-bootstrap
agentic-stack-doctor
```

| Command | Purpose |
|---|---|
| `agentic-bootstrap` | Install agents, skills/MCPs, configure, then run doctor |
| `agentic-install-agents` | Install Hermes, OMP, Codex and Claude Code |
| `agentic-install-skills-mcps` | Install selected skills and MCP tooling |
| `agentic-configure-agent-mcps` | Add missing managed entries; report existing drift |
| `agentic-update-stack` | Refresh components, then run doctor; does not update this package |
| `agentic-stack-doctor` | Read-only diagnosis; OMP failures exit 1, secondary/Hermes failures warn |
| `agentic-skill-drift` | Read-only: compare curated skills against their pack sources and upstreams |

Use each command's `--help` for options. Update this package with `uv tool upgrade agentic-env`.

Without selection flags on a terminal, `agentic-install-agents` and `agentic-install-skills-mcps` open checkbox pickers. Space toggles a row, `a` toggles all, `i` inverts, enter confirms. The skills run asks for skills, then target agents, then MCP servers, then prints the selection with the flag-only command that repeats it and confirms before installing.

`--yes` takes the flags as given without prompting, and a run without a terminal needs flags because no picker can open. `agentic-bootstrap --interactive` lets its two install phases prompt instead of installing every CLI and the `--skill-profile` packs.

### Skills

```bash
agentic-install-skills-mcps --skill-profile default --yes
```

[The manifest](agentic_env/skill-packs.json) selects 38 skills. Use `--skill-pack` to select packs, `--skill` to filter their selected names, and `--skill-agent` to override the default `hermes,claude,codex` targets. `--skill-config` supplies a manifest with the same shape; a pack without a `skills` list installs all its contents.

The skills picker lists one row per skill under its pack heading, plus an `All of <pack>` row that takes the whole roster. The `default` profile pre-checks the pack rows; `--skill NAME` pre-checks those skill rows instead. A manifest `skills` entry is either a name or `{"name": ..., "description": ...}`, and the description shows under the list while that row is pointed at. `--mcp` installs a single MCP server (`codebase-memory-mcp` or `agentmemory`); `--all-mcps` installs both.

[Decisions §6](DECISIONS_AI_TOOLING.md#6-skills) owns routing, invocation, review scope and Hermes limitations. Complete Matt/pstack packages are vendored; their `UPSTREAM.md` files record sources and adaptations.

#### Source drift

```bash
agentic-skill-drift                 # every pack; exits 1 on drift
agentic-skill-drift --pack ponytail --offline --no-upstream
agentic-skill-drift --update-baseline
```

Three columns per curated skill. **Source** compares the pack source with the reviewed fingerprint in [`skill-fingerprints.json`](agentic_env/skill-fingerprints.json) — a moved tag or an unreviewed vendored edit shows as `changed`. **Installed** compares `~/.agents/skills/<skill>` with that source and reports `missing`, `modified`, or `foreign:<source>` when the skills CLI lockfile names another origin. **Upstream** compares upstream at the pinned revision with upstream today, so a vendored pack's documented adaptations never register as drift while a real upstream edit does.

Pinned revisions come from the pack `source` for remote packs and the `upstream` block for vendored ones. Source trees are cached under `~/.cache/agentic-env/skill-sources`; `--offline` uses that cache only, `--no-upstream` skips the GitHub API. Record a reviewed state with `--update-baseline` after every deliberate pack move.

## Configuration and updates

- Existing managed MCP definitions and OMP settings are validated, not repaired. Correct reported fields manually; missing entries are added only to valid configuration.
- Hermes YAML writes keep a `.agentic-env.bak` backup but may discard comments/formatting. The configurator fails on Hermes drift even though doctor only warns.
- OMP gates `codebase-memory-mcp` and `node_repl`; `agentmemory` and `lean-ctx` stay excluded. Missing OMP settings are seeded only when the required checkout hooks exist. See [the contract](DECISIONS_AI_TOOLING.md).
- Reviewed versions in [stack metadata](agentic_env/stack_metadata.py) are floors. Install/update fetch the latest floating components and reject versions below the floor. Claude uses its `latest` channel.
- Hermes' installer and `codebase-memory-mcp` archives retain reviewed identities; remote scripts remain checksum-pinned. Skill packs move only by reviewed tags or vendored updates.
- Do not substitute `agentmemory upgrade`: it can invoke the `iii-engine` installer and modify the current workspace.

Check Hermes wiring with `hermes mcp list` and `hermes mcp test <server>`. Expected definitions are in [the configurator](agentic_env/configure_agent_mcps.py). To deliberately select its memory provider and add missing entries:

```bash
hermes config set memory.provider agentmemory
agentic-configure-agent-mcps --yes --server codebase-memory-mcp --server agentmemory --agent hermes
```

## Development

```bash
uv run --frozen python -m agentic_env.stack_doctor
uv run --frozen pytest -q
```

Other checkout commands use `uv run --frozen python -m agentic_env.<module>`; installed commands use `agentic-*`.

## Clean-platform acceptance

[The smoke script](docker-smoke-test.sh) owns the executable checks. [The isolation wrapper](clean-acceptance.sh) rejects root, the real HOME and nonempty fresh environments, clears inherited credentials/configuration, and uses checkout hooks. No provider credentials are required. Doctor's softer Hermes severity does not replace smoke's Hermes wiring checks.

### Containers

Requires Docker/Compose with amd64 support. Run from this directory:

```bash
# Debian bookworm x86_64
docker compose up --build --force-recreate --exit-code-from fresh-install fresh-install
# Arch rolling x86_64
docker compose --profile arch up --build --force-recreate --exit-code-from fresh-install-arch fresh-install-arch
```

`--force-recreate` prevents reuse of a previous installation. To inspect and recheck one retained installation:

```bash
docker compose run --rm --entrypoint sh fresh-install
# Inside that container:
sh ./clean-acceptance.sh
SKIP_INSTALL=1 sh ./clean-acceptance.sh
```

Checks-only requires the same provisioned HOME; a newly recreated container is not valid checks-only evidence. Exiting the `--rm` container discards it. On an already-provisioned host, use `SKIP_INSTALL=1 sh ./docker-smoke-test.sh`.

`VERBOSE=1` streams each command instead of capturing it, which is how you see the skills phase: without it `run_cmd` prints output only when a command fails.

#### Driving the install by hand

To run the phases yourself rather than the scripted contract, keep a container alive and exec into it:

```bash
docker compose run -d --name agentic-manual --entrypoint sleep fresh-install infinity
docker exec -it agentic-manual bash
# inside:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv
export PATH="$HOME/.local/bin:$PATH"
uv tool install --force --python "$(uv python find 3.12)" .
agentic-install-skills-mcps --skill-profile default --yes
agentic-skill-drift --no-upstream
docker rm -f agentic-manual   # from the host, when finished
```

Three things differ from the scripted run, which provides them through `env -i`:

- **`UV_PROJECT_ENVIRONMENT` is required.** The repo mounts read-only, so `uv run` fails trying to write `.venv` inside it — and your host's `.venv` is visible through the mount, pointing at an interpreter that does not exist in the container.
- **Skill targets decide where skills land.** `--skill-agent claude` writes real directories under `~/.claude/skills` and never creates `~/.agents/skills`, so `agentic-skill-drift` reports the whole roster as `missing`. Omit the flag, or include `codex`, to populate the canonical store.
- **A clone failure surfaces as a false auth error.** `Failed to clone … Authentication failed` on a public repo means git mangled the ref advertisement (`expected flush after ref listing`); remote packs are cloned, so caveman absorbs it first. The image pins `http.version HTTP/1.1` for this; set the same in any other container.

### Native Apple Silicon

With Homebrew and working Command Line Tools:

```bash
test "$(uname -m)" = arm64
brew install uv python@3.12 node@20 xz ca-certificates
export AGENTIC_PREREQ_PATH="$(brew --prefix uv)/bin:$(brew --prefix python@3.12)/libexec/bin:$(brew --prefix node@20)/bin:$(brew --prefix xz)/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export AGENTIC_SMOKE_HOME="$(mktemp -d "${TMPDIR:-/tmp}/agentic-env-acceptance.XXXXXX")"
sh ./clean-acceptance.sh
SKIP_INSTALL=1 sh ./clean-acceptance.sh
```

Keep that HOME for inspection/rechecks; use a new empty directory for another fresh run. Intel macOS is out of scope. Arch is proxy evidence, not direct CachyOS verification.

### CI and recorded evidence

[CI](../.github/workflows/agentic-env-smoke-test.yml) gates native macOS arm64, Debian x86_64 and Arch x86_64 acceptance on unit tests. Each acceptance job runs fresh installation then checks-only. Linux checks-only also exercises updates; macOS skips that second update to avoid another unauthenticated GitHub lookup. [Run manually](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml) when needed.

Historical [run 34526778331](https://github.com/MihaiA24/.dotfiles/actions/runs/34526778331), at [`2cb1f08`](https://github.com/MihaiA24/.dotfiles/commit/2cb1f08f9d0a7538ecef12e7532dfaee554a6400) on 2026-09-10, passed fresh and checks-only on:

| Environment | Architecture |
|---|---|
| Native macOS 15.7.9, build 24G830 | arm64 |
| Arch container, `VERSION_ID=20260906.0.587075` | x86_64 |
| Debian 12 bookworm container | x86_64 |

Linux used the Ubuntu host's `6.17.0-1022-azure` kernel: container-userland, not native distro-boot evidence. This historical run does not validate later changes. [Skill integration evidence](docs/skills-workflow-recheck-2026-09-21.md) is recorded separately.
