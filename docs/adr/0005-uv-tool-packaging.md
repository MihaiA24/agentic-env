# ADR 0005: Install agentic-env scripts as uv tools

## Status
Accepted; the root-script-wrapper portion is superseded by direct checkout module execution.

## Context
The installer scripts first ran as `uv` single-file scripts from the checkout. The goal is a set of globally installed commands, but development and container verification still need to run from the checkout. Root scripts stayed as compatibility wrappers during the packaging transition.

## Decision
Package the implementation as the `agentic-env` distribution, with import package `agentic_env` and a Python 3.12+ compatibility floor. Keep the six primary installed `uv tool` entry points: `agentic-install-agents`, `agentic-install-skills-mcps`, `agentic-configure-agent-mcps`, `agentic-bootstrap`, `agentic-update-stack`, and `agentic-stack-doctor`. Development and verification run from the checkout through the matching package modules with `uv run python -m agentic_env.<module>`. The former root-script compatibility wrappers are superseded, and no new wrapper layer replaces them. Move the default `skill-packs.json` into the package as bundled data, keeping a path override. `uv` owns the provisioner lifecycle: `agentic-update-stack` updates the managed stack but does not replace `agentic-env`.

**Scope clarification (2026-09-22):** the [Python-only skill copier](../../README.md#python-only-copy-on-windows) is a dependency-free package module that runs directly from a complete checkout. It copies vendored packages. It does not provision the stack, add a root wrapper, or add another installed entry point. The `uv` lifecycle above still owns the management commands; standalone destinations are maintained separately.

## Alternatives considered

1. **Keep root scripts only**
   - Rejected: keeps the checkout workflow but gives no persistent commands installed with `uv tool install`.

2. **One namespace command with subcommands**
   - Rejected for now: puts fewer commands on PATH, but changes the current command model more than needed.

3. **Prefixed direct commands with package modules**
   - Accepted: avoids collisions with generic command names, keeps the migration small, and gives the packaged entry points one maintainable source of truth.

## Consequences

- The README should present `uv tool install` and the prefixed commands as the primary workflow.
- Smoke verification should run the full fresh-install flow through the six installed tool commands, and module `--help` checks through direct checkout execution, not root-script wrappers.
- Removing the six root-script wrappers changes only how the checkout is invoked. The six installed `agentic-*` entry points remain the user-facing command contract; do not rename them casually.
- `agentic-update-stack` should not self-update `agentic-env`; users upgrade the tool with `uv tool upgrade agentic-env`.
