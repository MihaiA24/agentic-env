# ast-grep rules for the comment ban

Tested with ast-grep 0.50. Without installing it, run `uvx --from ast-grep-cli ast-grep` in a Python repo or `npx -p @ast-grep/cli ast-grep` in a Node repo wherever the commands below say `ast-grep`. The ban in CI needs it as a dev dependency: `ast-grep-cli` on PyPI, `@ast-grep/cli` on npm.

## Configuration

`sgconfig.yml` at the repo root. A repo that already has one adds the directory to its `ruleDirs`.

```yaml
ruleDirs: [ast-grep/rules]
```

### Python

`ast-grep/rules/no-comments-python.yml`:

```yaml
id: no-comments-python
language: python
severity: error
message: Comments are banned. Delete it, move a decision to an ADR, or file an issue for the hack.
files:
  - <src/**>
ignores: []
rule:
  kind: comment
  not:
    regex: "^#(!|\\s*(noqa: *[A-Z]+[0-9]+(, *[A-Z]+[0-9]+)* +-- +\\S|type:|pyright:|pyrefly:|mypy:|pragma:|fmt:|isort:|shortcut:|ponytail:|SPDX-License-Identifier|Copyright|-\\*- coding))"
```

### TypeScript

`ast-grep/rules/no-comments-typescript.yml`. Copy it to `no-comments-tsx.yml` with `id: no-comments-tsx` and `language: tsx`, and to `no-comments-javascript.yml` the same way when the scope has JavaScript; ast-grep parses each with its own grammar.

```yaml
id: no-comments-typescript
language: typescript
severity: error
message: Comments are banned. Delete it, move a decision to an ADR, or file an issue for the hack.
files:
  - <src/**>
ignores: []
rule:
  kind: comment
  not:
    any:
      - regex: "^(//|/\\*)\\s*(eslint-|@ts-expect-error|prettier-ignore|SPDX-License-Identifier|Copyright|shortcut:|ponytail:)"
      - regex: "^///\\s*<reference"
```

### What the ban allows

Tool directives, licence headers, the shebang and encoding lines, TypeScript triple-slash references, and `shortcut:` markers, with the older `ponytail:` form, which `/ponytail-debt` collects into a ledger. A Python `# noqa` passes only with rule codes and a reason, as in `# noqa: TID251 -- needed for streaming`. JSDoc blocks are comments like any other. Python docstrings are strings to ast-grep, so the ban never sees them. Add the repo's other tool directives to the regex, such as `pylint:` or `c8 ignore`.

## Check command

```bash
ast-grep scan || exit 1
if git grep --untracked -nE '(#|//|/\*) *ast-grep-ignore'; then exit 1; fi
```

ast-grep honours `ast-grep-ignore` comments: one hides its own line or the next, and one on line 1 followed by a blank line hides the whole file. No flag turns them off, so the second line fails on any of them. `|| exit 1` keeps the scan's failure: in a script without `set -e`, the second line's exit status would replace it.

## Ratchet

`ignores` lists the files that still hold comments, as globs relative to the repo root. A listed file also accepts new comments. ast-grep does not report an entry whose file is clean, so each cleanup deletes its own entries.

## Listing

Comments to sort, with `ignores` still empty:

```bash
ast-grep scan --json=stream | jq -r '"\(.file):\(.range.start.line + 1) \(.text)"'
```

Lines that comments fill on their own, per file:

```bash
ast-grep scan --json=stream | jq -rs 'map(select(.lines | test("^\\s*(#|//|/\\*)")) | {file, n: (.range.end.line - .range.start.line + 1)}) | group_by(.file) | map("\(map(.n) | add) \(.[0].file)") | .[]'
```
