# Agentic environment scripts

This folder contains Python scripts to install and update local agent tooling.

- `install-agents.py`
  - Installs/reinstalls:
    - Hermes Agent (`hermes`)
    - OMP / Oh My Pi (`omp`)
    - OpenAI Codex CLI (`codex`)
    - Claude Code (`claude`)

- `install-skills-mcps.py`
  - Skills:
    - mattpocock skills pack (global)
  - MCP tooling:
    - codebase-memory-mcp (UI install supported)
    - lean-ctx

- `update-agentic-stack.py`
  - Updates each tool only if it is already available on PATH:
    - `hermes`, `omp`, `codex`, `claude`, `skills`, `codebase-memory-mcp`, `lean-ctx`

Quick usage
- Install agents interactively:
  - `uv run /Users/mihai/.dotfiles/agentic-env/install-agents.py`
- Install skills + MCPs interactively:
  - `uv run /Users/mihai/.dotfiles/agentic-env/install-skills-mcps.py`
- Update installed tooling:
  - `uv run /Users/mihai/.dotfiles/agentic-env/update-agentic-stack.py`

Dependencies:
- `rich` is required and is installed automatically via uv script metadata.
