# agentic-env verification map

Read [the skill](../SKILL.md) for launch, isolation, evidence and cleanup; this index selects the user journeys. Product commands and selection policy are grounded in [README](../../../../README.md) and [Decisions §6](../../../../DECISIONS_AI_TOOLING.md#6-skills).

## Baseline preconditions

- Work from the complete checkout root with Python 3.12+ and uv. Set `V=.agents/skills/verify-agentic-env/verifier/control.py`.
- Run `python3 "$V" launch`, then `python3 "$V" doctor`; require current source/build identity. Use only its reported owned workspace, never host skill/config directories.
- The workspace starts with an empty sandbox HOME and no copied packages. For another fresh journey, preserve evidence, run cleanup, then launch again. Launch alone does not reset files.
- Copier, safe bootstrap, source-only drift and configurator journeys require no provider credentials. Native skills installation additionally requires npm/Git/network. Full provisioning/update belongs to the existing authorized clean-acceptance runner, not the offline sandbox.
- No background service, TCP port, seed database or browser is applicable. Synchronize on process exit or the named terminal prompt, not sleeps.

## Driving conventions

Helper drives execute real app commands with `uv run --frozen`; `--entry module` and `--entry console` are distinct management entry points. Copier instead supports `script` and `module`, with no installed console command. Do not report one route as coverage of another.

Every map uses exactly four H2s. IDs in `Sub-features` name the report rows; the drive section gives actions and observable outcomes. For an affected option, cover every enabled selector value, syntax (repeat/comma where supported), default/explicit mode and compatible combination that changes the journey. Common `--help`/`--verbose` routes matter when command parsing/output changes; they are not proof that the operation ran.

For every applicable branch, record success, cancel/decline, error, intentionally empty selection, and persistence/no-write behavior. Mark each entry point as passed, failed, blocked (attempt + unmet precondition), or N/A (reason). Unsupported wrapper routes are not N/A product features: exercise them in the authorized isolated environment or report the block. Fixtures/tests supplement those paths, not substitute for them.

User-visible installed entry points are `agentic-install-agents`, `agentic-install-skills-mcps`, `agentic-configure-agent-mcps`, `agentic-bootstrap`, `agentic-update-stack`, `agentic-stack-doctor`, and `agentic-skill-drift`. Each also has `uv run --frozen python -m agentic_env.<module>` from the checkout. The standalone copier is `python3 agentic_env/copy_skills.py` or `python3 -m agentic_env.copy_skills`; its Windows route uses `py -3`/`python`.

## Proof and skip reporting

Run wrapper doctor before/after each proof group. Save exact action/prompt, stdout/stderr, exit code, fingerprint and read-only persisted observation. Source/test/verifier changes require relaunch and repeating affected actions. Keep helper evidence and any external acceptance transcripts after cleanup.

The isolation profile is not a skill profile. Copier default/`drive copy --all` means every locally packaged manifest skill and remote-only exclusion notices. Installer profiles are explicit selectors; bootstrap chooses `default` unless overridden. Curated skills are optional: doctor requires no curated profile; drift requires absent curated skills only with `--skill-profile`.

## Features

- [Copier](copier.md): direct/module and Windows routes, complete package/subset/all copy, rejected selections/collisions and persisted hashes.
- [Skills installation and pickers](skills-install.md): native custom-directory and managed targets, selectors, confirmation/cancel/empty choices, MCP tools and real installation boundary.
- [MCP configuration](mcp-config.md): OMP/Hermes, server/descriptor options, dry runs, repeat convergence, notify-only drift and preserved configuration.
- [Bootstrap and update](bootstrap-update.md): plans/reports/skips, interactive agent installation and authorized clean acceptance/update.
- [Diagnosis and drift](diagnosis-drift.md): read-only stack diagnosis, source/installed/upstream comparisons, scopes, errors and separately authorized baseline review.
