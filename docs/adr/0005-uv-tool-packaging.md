# ADR 0005: Install agentic-env scripts as uv tools

## Status
Accepted

## Context
The installer scripts already run as `uv` single-file scripts from the checkout, but the desired primary workflow is a globally installed set of commands. The project still needs checkout execution for development and container verification.

## Decision
Package the implementation as the `agentic-env` distribution with import package `agentic_env` and Python 3.12+ as the compatibility floor. Keep the root scripts as `uv runnable script` compatibility wrappers, and expose only prefixed direct `uv tool command` entry points: `agentic-install-agents`, `agentic-install-skills-mcps`, `agentic-configure-agent-mcps`, and `agentic-update-stack`. Move the default `skill-packs.json` into the package as bundled data while preserving a path override.

## Alternatives considered

1. **Keep root scripts only**
   - Rejected: it preserves the current checkout workflow but does not provide persistent commands installed with `uv tool install`.

2. **One namespace command with subcommands**
   - Rejected for now: cleaner PATH surface, but it changes the current command model more than necessary.

3. **Prefixed direct commands with package modules**
   - Accepted: avoids generic command-name collisions, keeps migration small, and gives the packaged entry points a maintainable source of truth.

## Consequences

- The README should present `uv tool install` and prefixed commands as the primary workflow.
- Smoke verification should run the full fresh-install flow through installed tool commands and import/help checks through root-script wrappers.
- Command names become part of the user-facing contract and should not be renamed casually.
- `agentic-update-stack` should not self-update `agentic-env`; users upgrade the tool with `uv tool upgrade agentic-env`.
