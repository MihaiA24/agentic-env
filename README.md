# Agentic environment tools

Install and maintain an OMP-primary, Hermes-secondary stack.

- [Decisions](DECISIONS_AI_TOOLING.md): operative policy and wiring.
- [Stack overview](docs/stack-overview.md): architecture and research index.
- [Project memory](docs/project-memory-stack.md): per-repo setup.
- [pstack workflow](guides/poteto-workflow.md): prepare a repository's verifier and use it on changes.
- [Skill routing](guides/skill-routing.md): choose a skill for the task.

## Quick usage

The full stack targets macOS/Linux and requires Python 3.12+, Node.js 20+/npm, uv, curl, git, CA certificates, shell/archive utilities, C/C++ build tools and the dotfiles checkout. For Windows or an offline copy, the [Python-only copier](#python-only-copy-on-windows) needs only Python and the checkout.

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

Run on a terminal without selection flags, `agentic-install-agents` and `agentic-install-skills-mcps` open checkbox pickers. Space toggles a row, `a` toggles all, `i` inverts, enter confirms. The skills run asks for skills, then a destination: supported harnesses or **Other / custom directory**. Supported harnesses lead to the agent and MCP pickers; a custom directory asks for the exact skills-folder path and skips MCP installation. Both paths print the selection and replay command, then ask for confirmation.

`--yes` uses the flags as given without prompting. Without a terminal no picker can open, so pass flags. `agentic-bootstrap` installs every CLI and the `--skill-profile` packs; `agentic-bootstrap --interactive` lets its two install phases prompt instead.

### Skills

#### Choose an installation path

| Need | Route | Requirements and scope |
|---|---|---|
| Provision the full agent stack | [Quick usage](#quick-usage) | macOS/Linux prerequisites above; installs agents and manages configuration |
| Refresh managed OMP/Hermes/Claude/Codex skills | [Managed refresh](#refresh-skills-on-an-existing-omp-host) | Management CLI and native skills CLI/npm; selected agent directories |
| Copy any curated pack into another harness's folder | [Custom directory](#install-into-another-harnesss-directory) | macOS/Linux, Python 3.12+, uv, Node.js/npm and Git; network for remote packs |
| Copy vendored skills on Windows or offline | [Python-only copy](#python-only-copy-on-windows) | Python 3.12+ and a complete checkout; no other runtime dependencies |

Windows acceptance covers only the Python-only copier, not full-stack provisioning or the native skills CLI path. Copying leaves skill bodies unchanged: scripts and OMP/Hermes-specific tool and delegation instructions may need adapting for another harness or OS.

To install the complete curated selection into the managed skill store:

```bash
agentic-install-skills-mcps --skill-profile default --yes
```

[The manifest](agentic_env/skill-packs.json) selects 38 skills. Use `--skill-pack` to select packs, `--skill` to filter their selected names, and `--skill-agent` to override the default `hermes,claude,codex` targets. `--skill-config` supplies a manifest with the same shape; a pack without a `skills` list installs all its contents.

The skills picker lists one row per skill under its pack heading, plus an `All of <pack>` row that takes the whole roster. The `default` profile pre-checks the pack rows; `--skill NAME` pre-checks those skill rows instead. A manifest `skills` entry is either a name or `{"name": ..., "description": ...}`; the description shows under the list while that row is highlighted. `--mcp` installs a single MCP server (`codebase-memory-mcp` or `agentmemory`); `--all-mcps` installs both.

[Decisions §6](DECISIONS_AI_TOOLING.md#6-skills) owns routing, invocation, review scope and Hermes limitations. Complete Matt/pstack packages are vendored; their `UPSTREAM.md` files record sources and adaptations.

#### Install into another harness's directory

`--skills-dir PATH` copies complete selected packages into `PATH/<skill>/SKILL.md`, including their scripts and references. `PATH` is the skills folder, not the project root. This route needs no OMP/Hermes installation but still uses the native skills CLI and npm, even for vendored-only selections. Without them, use the Python-only route below.

For the guided flow, run `uv run agentic-install-skills-mcps` from this checkout: choose skills, select **Other / custom directory**, enter the path, then review and confirm. Choose **Supported harnesses** instead to keep the existing managed-agent installation. Ctrl-C at either destination prompt cancels without installing anything.

From this checkout, without replacing the host's installed management CLI:

```bash
cd /path/to/your/dotfiles/agentic-env

# Skip the destination prompts; still choose skills interactively.
uv run agentic-install-skills-mcps --skills-dir "/path/to/project/.devin/skills"

# All 38 curated skills without prompts.
uv run agentic-install-skills-mcps \
  --skills-dir "/path/to/project/.devin/skills" --skill-profile default --yes

# Or a subset, in any directory you choose.
uv run agentic-install-skills-mcps \
  --skills-dir "/path/to/custom skills" --skill-pack mattpocock --skill tdd,code-review --yes
```

Run **one** of the commands above. The `--skill-pack`, `--skill-profile`, `--skill`, and `--skill-config` selectors still apply. Directory mode writes only the given destination: it selects no agent roots, installs no MCPs and registers no global provenance. Combining it with `--skill-agent`, `--mcp`, or `--all-mcps` is an error.

The result is standalone copies, not links or managed installations. After copying, follow the shared [verification and refresh procedure](#verify-and-refresh-standalone-copies).

The example uses Devin for Terminal's `.devin/skills` layout. Set the directory your harness actually discovers.

#### Python-only copy on Windows

This fallback needs only Python 3.12+ and the checkout. It downloads nothing, installs no agents, configures no MCPs and runs without prompts.

Use a complete checkout or an extracted repository ZIP. The copier needs `skill-packs.json` and the vendored directories beside it, so the Python file alone is not enough. Git is not required once you have the files.

From the dotfiles checkout root, confirm the interpreter is 3.12 or newer:

```powershell
py -3 --version
```

Without the `py` launcher, use `python` after checking `python --version`. Choose the exact folder your harness discovers, outside the source skill packages, then run one of these commands:

```powershell
# From the dotfiles checkout; choose ONE command.
py -3 agentic-env\agentic_env\copy_skills.py --skills-dir "C:\work\project\.devin\skills"

# Or copy only these vendored skills.
py -3 agentic-env\agentic_env\copy_skills.py --skills-dir "C:\work\project\.devin\skills" --skill "tdd,code-review"
```

On macOS/Linux, the equivalent command from the checkout root is:

```bash
python3 agentic-env/agentic_env/copy_skills.py --skills-dir "/path/to/project/.devin/skills"
```

By default it copies the **30 vendored Matt/pstack skills**, including scripts and references, and lists the **8 remote-only caveman/ponytail skills it did not copy**. The manifest owns this roster. `--skill` accepts comma-separated or repeated names. An unavailable name or an empty `--skill` is an error; the copier never substitutes a different selection.

The copier accepts only `--skills-dir`, `--skill` and `--help`. Pack, profile and custom-manifest selectors, `--yes`, agent targets and MCP flags belong to `agentic-install-skills-mcps`. Success is the copy message plus exit status 0; in PowerShell, check `$LASTEXITCODE` immediately after the command.

The copier only copies files. It does not convert Bash assets or OMP/Hermes-specific instructions into Windows workflows. Verify and refresh the destination with the procedure below.

#### Verify and refresh standalone copies

This procedure covers both custom-directory routes, not the managed-agent refresh below.

1. **Check the result.** Require exit status 0. Confirm each selected skill has `PATH/<skill>/SKILL.md` and its scripts/references. A default Python-only copy leaves out the eight remote-only skills by design; an explicitly requested unavailable skill fails before copying.
2. **Check harness discovery separately.** Confirm the destination is the harness's documented skills folder, then load one selected skill by name without executing its recipe. Copying files proves neither discovery nor workflow compatibility. Doctor and `agentic-skill-drift` inspect the managed stack, not an arbitrary destination.
3. **Refresh into a new directory.** Get the reviewed checkout or manifest version you want, and record its revision or archive identity and your selection. Rerun the same route with a new destination. Compare whole package directories, and preserve local edits and back up the existing selected packages before you replace them. `uv tool upgrade agentic-env` and `agentic-update-stack` do not refresh standalone copies.
4. **Handle errors without overwriting.** Both routes refuse existing skill names, including dangling symlinks, before copying any package, and leave unrelated files alone. Choose a fresh destination instead of deleting local work. A filesystem failure mid-copy can leave incomplete new packages, because failure does not roll back. Inspect the failed destination, fix the error, and retry into a new one.

There is no force-overwrite, automatic merge, uninstall or rollback command for standalone copies. To remove one, preserve local changes, then delete only the package directories you copied.

#### Refresh skills on an existing OMP host

Use this runbook when OMP already runs on the host. It refreshes the management CLI and selected skills, not agent binaries or MCP configuration, so full bootstrap is unnecessary. Before replacing installed skills, review and preserve intentional edits to them.

1. **Refresh the management CLI from the checkout.** This picks up the checkout's manifest, vendored adaptations and guided installer; an older installed CLI may not have the current picker.

   ```bash
   cd /path/to/your/dotfiles/agentic-env
   uv tool install --force .
   ```

2. **Check OMP discovery.** `~/.omp/agent/config.yml` should contain these settings. Merge missing fields into the existing `skills` mapping; do not replace the whole configuration. The configurator reports drift in existing settings but does not repair them.

   ```yaml
   skills:
     enableClaudeUser: true
     enableAgentsUser: false
   ```

   OMP reads `~/.claude/skills`, whose links point into the canonical `~/.agents/skills` store. There is no `--skill-agent omp`. Keep the default `hermes,claude,codex` targets, or select both Claude and Codex: Claude provides OMP's discovery path and Codex populates the canonical store. A Claude-only install writes copies instead and does not create this layout on a fresh store. Claude Code does not need to run.

3. **Choose one installation path.**

   Guided selection on a terminal:

   ```bash
   agentic-install-skills-mcps
   ```

   Select individual skills or pack rows, choose **Supported harnesses**, keep the targets described above, and **clear every MCP row** for a skills-only refresh. **Other / custom directory** makes standalone copies and does not refresh the managed OMP layout. Review the printed selection and replay command before confirming; declining the final confirmation installs nothing.

   Or install the complete curated profile without prompts:

   ```bash
   agentic-install-skills-mcps --skill-profile default --yes
   ```

   This uses all default skill targets and installs no MCPs.

4. **Check installation and configuration.**

   ```bash
   agentic-stack-doctor
   agentic-skill-drift
   ```

   Doctor checks stack wiring. Drift checks the manifest's full roster, not just your selection, so skills you left out can report `missing`. Read each drift column: `foreign:<source>` concerns recorded provenance, not necessarily different file contents, and an upstream `unknown` is unverified, not a pass. If the upstream lookup is unavailable, use `--no-upstream` for a separate source/install check. Do not use `--update-baseline` just to clear warnings.

5. **Start a new OMP session and check discovery.** Ask OMP to read `skill://<selected-name>` and report its name without executing the recipe. Check one selected skill from each installed pack; for Matt/pstack, `writing-for-agents` and `how` are examples if selected. OMP hides manual-only skills from automatic discovery but still loads them by name.

6. **Test workflows separately.** Installation and named loading do not prove end-to-end behavior. Exercise the chosen methods on bounded tasks and keep the evidence. Doctor and drift checks are not proof of a bug fix, downstream safety, or verifier coverage. See the [recorded verification scope](docs/skills-workflow-recheck-2026-09-21.md). To start work in a repository, follow the [pstack workflow](guides/poteto-workflow.md) and [skill routing](guides/skill-routing.md) guides.

#### Source drift

```bash
agentic-skill-drift                 # every pack; exits 1 on drift
agentic-skill-drift --pack ponytail --offline --no-upstream
agentic-skill-drift --update-baseline
```

The report has three columns per curated skill. **Source** compares the pack source with the reviewed fingerprint in [`skill-fingerprints.json`](agentic_env/skill-fingerprints.json); a moved tag or an unreviewed vendored edit shows as `changed`. **Installed** compares `~/.agents/skills/<skill>` with that source and reports `missing`, `modified`, or `foreign:<source>` when the skills CLI lockfile names another origin. **Upstream** compares upstream at the pinned revision with upstream today, so a vendored pack's documented adaptations never count as drift but a real upstream edit does.

This command has no `--skills-dir` override; the Installed column always checks the canonical managed store. Check standalone copies with [destination verification](#verify-and-refresh-standalone-copies) instead.

Pinned revisions come from the pack `source` for remote packs and the `upstream` block for vendored ones. Source trees are cached under `~/.cache/agentic-env/skill-sources`; `--offline` uses that cache only, `--no-upstream` skips the GitHub API. Record a reviewed state with `--update-baseline` after every deliberate pack move.

## Configuration and updates

- The configurator validates existing managed MCP definitions and OMP settings but does not repair them. Correct reported fields manually; it adds missing entries only to valid configuration.
- Hermes YAML writes keep a `.agentic-env.bak` backup but may drop comments and formatting. The configurator fails on Hermes drift; doctor only warns.
- OMP gates `codebase-memory-mcp` and `node_repl`; `agentmemory` and `lean-ctx` stay excluded. The configurator seeds missing OMP settings only when the required checkout hooks exist. See [the contract](DECISIONS_AI_TOOLING.md).
- Reviewed versions in [stack metadata](agentic_env/stack_metadata.py) are floors. Install/update fetch the latest floating components and reject versions below the floor. Claude uses its `latest` channel.
- Hermes (its release and its installer script) and the `codebase-memory-mcp` archives stay at reviewed identities; remote scripts stay checksum-pinned.
- Do not substitute `agentmemory upgrade`: it can invoke the `iii-engine` installer and modify the current workspace.

Check Hermes wiring with `hermes mcp list` and `hermes mcp test <server>`. Expected definitions are in [the configurator](agentic_env/configure_agent_mcps.py). To select Hermes' memory provider and add missing entries:

```bash
hermes config set memory.provider agentmemory
agentic-configure-agent-mcps --yes --server codebase-memory-mcp --server agentmemory --agent hermes
```

## Development

```bash
uv run --frozen python -m agentic_env.stack_doctor
uv run --frozen pytest -q
```

From the checkout, run other management commands as `uv run --frozen python -m agentic_env.<module>`; installed commands are `agentic-*`. The exception is the dependency-free copier, which you run directly with Python as shown above.

To run the portable copier checks without installing dependencies, from `agentic-env`:

```powershell
py -3 -S -m unittest discover -s tests -p test_copy_skills.py -v
```

Use `python3 -S -m unittest discover -s tests -p test_copy_skills.py -v` on macOS/Linux. These checks launch the real copier with site packages disabled and an empty `PATH`, using temporary destinations. The full suite includes Unix PTY tests, so it is not the Windows check.

## Clean-platform acceptance

Full-stack acceptance uses [the smoke script](docker-smoke-test.sh). [The isolation wrapper](clean-acceptance.sh) rejects root, the real HOME and nonempty fresh environments, clears inherited credentials/configuration, and uses checkout hooks. No provider credentials are required. Doctor only warns on Hermes, but smoke still checks Hermes wiring. Windows gets only the copier check under [Development](#development), not this provisioning contract.

### Containers

Requires Docker/Compose with amd64 support. Run from this directory:

```bash
# Debian bookworm x86_64
docker compose up --build --force-recreate --exit-code-from fresh-install fresh-install
# Arch rolling x86_64
docker compose --profile arch up --build --force-recreate --exit-code-from fresh-install-arch fresh-install-arch
```

`--force-recreate` stops Compose from reusing a previous installation. To inspect and recheck one retained installation:

```bash
docker compose run --rm --entrypoint sh fresh-install
# Inside that container:
sh ./clean-acceptance.sh
SKIP_INSTALL=1 sh ./clean-acceptance.sh
```

Checks-only requires the same provisioned HOME; a newly recreated container is not valid checks-only evidence. Exiting the `--rm` container discards it. On an already-provisioned host, use `SKIP_INSTALL=1 sh ./docker-smoke-test.sh`.

`VERBOSE=1` streams each command's output instead of capturing it. Without it, `run_cmd` prints output only when a command fails, so use it to watch the skills phase.

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

- **`UV_PROJECT_ENVIRONMENT` is required.** The repo mounts read-only, so `uv run` fails trying to write `.venv` inside it. Your host's `.venv` is also visible through the mount and points at an interpreter the container does not have.
- **Skill targets decide where skills land.** `--skill-agent claude` writes real directories under `~/.claude/skills` and never creates `~/.agents/skills`, so `agentic-skill-drift` reports the whole roster as `missing`. Omit the flag, or include `codex`, to populate the canonical store.
- **A clone failure surfaces as a false auth error.** `Failed to clone … Authentication failed` on a public repo means git mangled the ref advertisement (`expected flush after ref listing`). Remote packs are cloned, and caveman is the first remote pack, so it hits the error first. The image pins `http.version HTTP/1.1` to avoid this; set the same in any other container.

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

[CI](../.github/workflows/agentic-env-smoke-test.yml) runs native macOS arm64, Debian x86_64 and Arch x86_64 acceptance only after unit tests pass. Each acceptance job runs fresh installation, then checks-only. Linux checks-only also exercises updates; macOS skips that second update to avoid another unauthenticated GitHub lookup. [Run manually](https://github.com/MihaiA24/.dotfiles/actions/workflows/agentic-env-smoke-test.yml) when needed.

The independent **Windows Python-only skill copy** job uses `windows-latest` and Python 3.12 to run the dependency-free checks above. It covers complete vendored copies, reported remote exclusions, selection errors, collision preflight and refusal to copy into a source package. It does not install agents or MCPs or validate skill workflows.

On 2026-09-22, that [Windows job passed](https://github.com/MihaiA24/.dotfiles/actions/runs/35761661410/job/106860923046) at [`d9bff13`](https://github.com/MihaiA24/.dotfiles/commit/d9bff133715b6b3e063b705381c682bc52934d8e). This is copier acceptance, separate from the historical full-stack evidence below.

Historical [run 34526778331](https://github.com/MihaiA24/.dotfiles/actions/runs/34526778331), at [`2cb1f08`](https://github.com/MihaiA24/.dotfiles/commit/2cb1f08f9d0a7538ecef12e7532dfaee554a6400) on 2026-09-10, passed fresh and checks-only on:

| Environment | Architecture |
|---|---|
| Native macOS 15.7.9, build 24G830 | arm64 |
| Arch container, `VERSION_ID=20260906.0.587075` | x86_64 |
| Debian 12 bookworm container | x86_64 |

Linux used the Ubuntu host's `6.17.0-1022-azure` kernel: container-userland, not native distro-boot evidence. This historical run does not validate later changes. [Skill integration evidence](docs/skills-workflow-recheck-2026-09-21.md) is recorded separately.
