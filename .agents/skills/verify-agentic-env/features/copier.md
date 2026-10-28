# Standalone skill copier

Copy complete locally packaged skills into an exact skills folder, without downloads, agent installation, prompts or MCP configuration. These are standalone copies, not a managed installation.

## Sub-features

- `copy-package`: selected packages include every script/reference/metadata file with unchanged bytes and executable bits.
- `copy-select`: default local roster, one name, comma-separated/repeated names and both direct-script/module entry points.
- `copy-reject`: empty/unavailable selections, invalid arguments and unsafe/unwritable destinations fail without replacing existing work.
- `copy-collision`: existing names (including dangling links) are refused before any package is copied; local edits and unrelated files survive.
- `copy-portable`: dependency-free direct Python route, including native Windows; copying does not prove harness discovery or workflow compatibility.

## How to get to it (user POV)

- Direct script: `python3 agentic_env/copy_skills.py --help`; module: `python3 -m agentic_env.copy_skills --help`. There is no copier console command.
- Windows: `py -3 agentic_env\copy_skills.py --help`, or `python` if the launcher is unavailable. Python must be 3.12+ and the checkout must include its manifest/packages.
- Application flags are only required `--skills-dir`, repeatable/comma-separated `--skill`, and `--help`. There is no app `--all`, `--yes`, profile/pack/custom-manifest/agent/MCP/overwrite option. Wrapper `--all` means omit the app's `--skill`; wrapper default instead selects `writing-for-agents`.

## Driving it with the verifier CLI

Preconditions: [baseline](README.md#baseline-preconditions); start each independent selection with no existing `workspace/skills`. Use cleanup/launch/doctor between rows, preserving evidence. The [skill's exact sequence](../SKILL.md#drive) proves one package, persistence and a collision end to end.

- **Direct success (`copy-package`)**: `python3 "$V" drive copy --entry script --skill writing-for-agents`, then `python3 "$V" drive inspect`. Require exit 0 and `Copied 1 vendored skills`; inspect must show `SKILL.md`, `SKILL-MECHANICS.md` and `agents/openai.yaml`, all matching the exact source hashes listed in the skill. No HOME/config changes. Direct script runs with `-I -S`; no site-package import is needed by the copier.
- **Module success (`copy-select`)**: on a fresh workspace, `python3 "$V" drive copy --entry module --skill writing-for-agents`, then inspect. Same complete package/end state; another entry point's successful copy is not this proof.
- **Selection syntax (`copy-select`)**: separately run `python3 "$V" drive copy --skill tdd,code-review` and `python3 "$V" drive copy --skill tdd --skill code-review` in fresh workspaces. Require only the two named packages and matching complete contents. Repeat affected syntax with `--entry module`.
- **Default local roster (`copy-select`)**: `python3 "$V" drive copy --all --entry script`; inspect. Repeat with `--entry module` when affected. Require every manifest package whose source is local, plus the explicit `Not copied (remote-only, ...)` list. Compare whole package paths, bytes and executable modes with their source, not only `SKILL.md`. The copier local roster and installer `default` profile are different selections.
- **Empty selection (`copy-reject`)**: `python3 "$V" drive copy --skill ''`; separately `python3 "$V" drive copy --skill ' , '`. Require argparse exit 2, `--skill must contain a skill name`, and no destination/package creation. This is a usage error, not an intentional successful empty picker selection.
- **Unavailable/partly invalid (`copy-reject`)**: `python3 "$V" drive copy --skill tdd,ponytail`, then `python3 "$V" drive copy --skill not-a-skill`; require exit 1 with unavailable names and no partial `tdd` copy. Repeat affected errors with `--entry module`; inspect each no-write outcome.
- **Collision (`copy-collision`)**: copy `writing-for-agents`, inspect, rerun the identical selection (or `--all` to cover a late collision). Require exit 1/`already exists`; before/after inventories must be identical, including absence of other new packages. Repeat the user path after a deliberate user-file edit/unrelated note in the owned destination when preservation changes; retain those input/output hashes. Dangling-name, destination-file, source-descendant and permission/I/O failures require the corresponding disposable filesystem precondition. If unavailable, report that path blocked; do not mutate source packages or synthesize success with internal copy helpers.
- **Regression supplement**: `python3 "$V" drive tests --suite copy` exercises the real isolated script and additional guard cases. It does not replace the live drives or native Windows proof.
- **Native Windows (`copy-portable`)**, only on a Windows checkout, in PowerShell:

  ```powershell
  $D = Join-Path $env:TEMP ("agentic-env-copy-" + [guid]::NewGuid().ToString())
  py -3 -I -S agentic_env\copy_skills.py --skills-dir "$D\skills" --skill writing-for-agents
  $LASTEXITCODE
  Get-ChildItem "$D\skills\writing-for-agents" -Recurse -File | Get-FileHash -Algorithm SHA256
  py -3 -I -S agentic_env\copy_skills.py --skills-dir "$D\skills" --skill writing-for-agents
  $LASTEXITCODE
  Get-ChildItem "$D\skills\writing-for-agents" -Recurse -File | Get-FileHash -Algorithm SHA256
  ```

  Require 0 then 1, three source-matching file hashes unchanged after collision, and a retained transcript outside `$D` before removing only this run-created temporary directory. Native Windows is blocked on a Unix host, not proved by the Unix helper. `python` is the equivalent command if `py` is absent.

## Gotchas

- Cancellation/decline, interactive empty choices, auth/browser/network and TCP paths are N/A: the copier is synchronous, offline and has no prompts. Killing it mid-copy is not an app cancellation feature; report interrupted/partial evidence instead.
- Both standalone routes preflight collisions but do not roll back filesystem failures mid-copy. Inspect incomplete new packages and retry into a fresh owned destination; never add force-overwrite or erase local work to pass.
- Arbitrary destination/path-type/symlink fixtures are outside this wrapper's fixed destination interface. Exercise them through the direct user command only in a separately owned disposable environment, or report the exact missing precondition. The regression suite is supporting evidence, not a substitute claim.
- `drive inspect` is read-only and must follow the copy attempt. Managed doctor/drift do not verify arbitrary copies. Harness discovery needs a separate load-by-name without executing the copied recipe; no compatibility claim follows from copying alone.
- Source changes invalidate build/evidence. Run doctor before/after and retain evidence through cleanup. There is no standalone refresh/merge/uninstall command: refresh into a new directory after preserving edits.
