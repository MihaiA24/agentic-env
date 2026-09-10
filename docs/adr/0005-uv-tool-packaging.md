# ADR 0005: Install agentic-env scripts as uv tools

## Status
Accepted; the root-script-wrapper portion is superseded by direct checkout module execution.

## Context
The installer scripts originally ran as `uv` single-file scripts from the checkout, but the desired primary workflow is a globally installed set of commands. The project still needs checkout execution for development and container verification. Root scripts were retained as transitional compatibility wrappers during packaging; that portion is now superseded by running package modules directly from the checkout.

## Decision
Package the implementation as the `agentic-env` distribution with import package `agentic_env` and Python 3.12+ as the compatibility floor. Preserve the six primary installed `uv tool` entry points: `agentic-install-agents`, `agentic-install-skills-mcps`, `agentic-configure-agent-mcps`, `agentic-bootstrap`, `agentic-update-stack`, and `agentic-stack-doctor`. Run development and verification from the checkout through the corresponding package modules with `uv run python -m agentic_env.<module>`; the former root-script compatibility wrappers are superseded and no new wrapper layer is introduced. Move the default `skill-packs.json` into the package as bundled data while preserving a path override. Keep the provisioner lifecycle owned by `uv`; `agentic-update-stack` updates the managed stack but does not replace `agentic-env`.

## Alternatives considered

1. **Keep root scripts only**
   - Rejected: it preserves the current checkout workflow but does not provide persistent commands installed with `uv tool install`.

2. **One namespace command with subcommands**
   - Rejected for now: cleaner PATH surface, but it changes the current command model more than necessary.

3. **Prefixed direct commands with package modules**
   - Accepted: avoids generic command-name collisions, keeps migration small, and gives the packaged entry points a maintainable source of truth.

## Consequences

- The README should present `uv tool install` and prefixed commands as the primary workflow.
- Smoke verification should run the full fresh-install flow through the six installed tool commands and module `--help` checks through direct checkout execution, not root-script wrappers.
- Removing the six root-script wrappers changes only checkout invocation; the six installed `agentic-*` entry points remain the user-facing command contract and should not be renamed casually.
- `agentic-update-stack` should not self-update `agentic-env`; users upgrade the tool with `uv tool upgrade agentic-env`.
