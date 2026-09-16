# ADR 0010: pstack skills vendored into the repo

## Status
Accepted 2026-09-15. Closes issue #42's pinning question; changes how one pack in `skill-packs.json` is sourced.

## Context
Every pack is meant to be pinned (`README.md` "Upgrading": installed skill-pack contents never advance to floating upstream revisions). `cursor/plugins` (pstack) publishes no tags. The `skills` CLI at the pinned `1.5.16` clones by branch name (`git clone --branch <ref>`): both `cursor/plugins#<sha>` and the `/tree/<sha>/pstack/skills` URL form fail with `Remote branch <sha> not found`. The pack therefore floated on `main` since 2026-08-22 and nothing could detect drift. With #42 the pstack roster grows from 4 to 9 skills, so the floating surface grows too.

Facts checked: `pstack/LICENSE` is MIT; none of the nine roster skills reference files outside their own directory; the CLI accepts a local path source and installs from it into `~/.agents/skills` with the same symlinks as a remote source.

## Decision
Copy the nine roster skill directories and `LICENSE` from `cursor/plugins` at commit `c1c0a32802223f4be824112dd83d33ad29a8b26c` (2026-09-14) into `agentic_env/vendored/pstack/`, with `UPSTREAM.md` recording commit, date, scope, and "local modifications: none". Manifest `source` becomes `./vendored/pstack/skills`; `SkillManifest.source` resolves a `./` source against the package directory and hands the absolute path to the CLI. The copy ships in the wheel (`pyproject.toml` artifacts), so `uv tool install` has it without a network fetch. `skill-packs.json` keeps the same shape; only the `source` value changed for this one pack.

## Considered options
1. **Fork `cursor/plugins` and tag the fork** — rejected. Same immutability, but adds a second repository to own, sync, and authorize pushes to; a fork's `main` drifts the same way unless someone tends it.
2. **Keep floating, record the reviewed SHA in the manifest note** — rejected. Zero mechanism; the recorded SHA proves nothing about what a clean host installs.
3. **Installer post-install hash check** — rejected. Detects drift after the fact without pinning; adds a checksum table for 37 files that a re-copy would have to regenerate anyway.
4. **Vendor the copy** — taken. One directory, no new remote, provenance and licence travel with the files, the existing local-path support in the CLI does the install.

## Consequences
- `agentic_env/vendored/pstack/` is upstream text under MIT; it is not edited locally. A needed change goes upstream or becomes a documented local modification in `UPSTREAM.md`.
- Upstream fixes do not arrive by themselves; the trigger to re-copy is in `DECISIONS_AI_TOOLING.md` Upstream watch.
- `tests/test_install_skills_mcps.py` fails when the roster names a skill the copy does not contain, so a bad re-copy is caught before install time.
- Reopen: `cursor/plugins` starts tagging → `source: cursor/plugins#<tag>`, delete the copy.
