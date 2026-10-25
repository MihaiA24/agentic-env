# agentic-env

- Policy and wiring: `DECISIONS_AI_TOOLING.md`. Skill invocation and routing: its §6.
- Vendored skills: `agentic_env/vendored/<pack>/skills/<name>/SKILL.md`; local adaptations in each pack's `UPSTREAM.md`. Packs and profiles: `agentic_env/skill-packs.json`. Repo-owned skills: `agentic_env/skills/`.
- Guides for applying the stack to other repositories: `guides/`.
- Local gate: run `./local-ci.sh` once when a branch's work is done, not per commit, then commit `local-ci.attestation` (README "Local gate"). For quick checks while working, run `uv run --frozen pytest -q`.
