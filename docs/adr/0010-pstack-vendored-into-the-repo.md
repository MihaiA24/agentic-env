# ADR 0010: pstack skills vendored into the repo

## Status
Accepted 2026-09-15. Closes issue #42's pinning question; changes how one pack in `skill-packs.json` is sourced.

## Context
Every pack is meant to be pinned (`README.md` "Upgrading": installed skill-pack contents never advance to floating upstream revisions). `cursor/plugins` (pstack) publishes no tags. The `skills` CLI at the pinned `1.5.16` clones by branch name (`git clone --branch <ref>`), so both `cursor/plugins#<sha>` and the `/tree/<sha>/pstack/skills` URL form fail with `Remote branch <sha> not found`. The pack has therefore floated on `main` since 2026-08-22, and nothing could detect drift. Issue #42 grows the pstack roster from 4 to 9 skills, so more content floats.

Facts checked: `pstack/LICENSE` is MIT; none of the nine roster skills reference files outside their own directory; the CLI accepts a local path source and installs from it into `~/.agents/skills` with the same symlinks as a remote source.

## Decision
Copy the nine roster skill directories and `LICENSE` from `cursor/plugins` at commit `c1c0a32802223f4be824112dd83d33ad29a8b26c` (2026-09-14) into `agentic_env/vendored/pstack/`. `UPSTREAM.md` records the commit, date, scope, and "local modifications: none". The manifest `source` becomes `./vendored/pstack/skills`. `SkillManifest.source` resolves a `./` source against the package directory and passes the absolute path to the CLI. The copy ships in the wheel (`pyproject.toml` artifacts), so `uv tool install` gets it without a network fetch. `skill-packs.json` keeps its shape; only this pack's `source` value changed.

## Considered options
1. **Fork `cursor/plugins` and tag the fork** — rejected. It gives the same immutability but adds a second repository to own, sync, and authorize pushes to. A fork's `main` drifts the same way unless someone maintains it.
2. **Keep floating, record the reviewed SHA in the manifest note** — rejected. Nothing enforces it; the recorded SHA proves nothing about what a clean host installs.
3. **Installer post-install hash check** — rejected. It detects drift after the fact without pinning, and it adds a checksum table for 37 files that a re-copy would have to regenerate anyway.
4. **Vendor the copy** — taken. One directory and no new remote. Provenance and licence travel with the files, and the CLI's existing local-path support does the install.

## Consequences
- `agentic_env/vendored/pstack/` is upstream text under MIT and is not edited locally. A needed change goes upstream or becomes a documented local modification in `UPSTREAM.md`.
- Upstream fixes do not arrive automatically; the re-copy trigger is in `DECISIONS_AI_TOOLING.md` Upstream watch.
- `tests/test_install_skills_mcps.py` fails when the roster names a skill missing from the copy, so a bad re-copy is caught before install time.
- Reopen when `cursor/plugins` starts tagging: switch to `source: cursor/plugins#<tag>` and delete the copy.
