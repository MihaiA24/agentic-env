# Python baseline

## Lint: ruff

```toml
# pyproject.toml
[tool.ruff.lint]
extend-select = [
  "TID251",  # banned-api: a banned import or attribute, with a message
  "PGH003",  # a bare `# type: ignore` without a rule code
  "PGH004",  # a bare `# noqa` without a rule code
  "RUF100",  # a `# noqa` that no longer suppresses anything
  "ERA001",  # commented-out code
]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"requests".msg = "Use <app.net.http_client>; it sets timeouts and retries."
"datetime.datetime.utcnow".msg = "Use <app.clock.now()>, which returns an aware datetime."
```

`banned-api` takes modules and qualified attributes. Each `msg` names the replacement; ruff prints it after "is banned:". Replace the angle-bracket names with the repo's real ones. Use `per-file-ignores` to let the module that implements the replacement import the banned API.

## Types: pyright

```toml
[tool.pyright]
typeCheckingMode = "strict"
reportUnnecessaryTypeIgnoreComment = "error"
```

For a gradual start, keep `typeCheckingMode = "standard"` and list the clean directories in `strict = ["src/app/core"]`. Add each directory after its cleanup commit. A repo that already uses mypy keeps it: enable `strict = true` and `warn_unused_ignores = true`.

## Import boundaries: import-linter

```toml
[tool.importlinter]
root_package = "app"

[[tool.importlinter.contracts]]
name = "Domain code does not import the web layer"
type = "forbidden"
source_modules = ["app.domain"]
forbidden_modules = ["app.web"]
broken_contract_guidance = "Return a domain value and let <app.web.views> render it."

[[tool.importlinter.contracts]]
name = "Layers import downward: web, then services, then domain"
type = "layers"
layers = ["app.web", "app.services", "app.domain"]
broken_contract_guidance = "Move the shared code down a layer, or call it through <app.services>."
```

Run `lint-imports`. `broken_contract_guidance` (import-linter 2.14 and later) prints below each broken contract, so it names the fix.

## Dead code

Ruff's default `F401` and `F841` catch unused imports and variables. `vulture` finds unused functions and classes; `deptry` finds unused and missing dependencies.

## Ratchets

- ruff: `ruff check --select <code> --add-noqa` adds a `# noqa: <code>` to each existing violation, so only new ones fail. `RUF100` flags each one that the cleanup makes unnecessary.
- pyright: the per-directory `strict` list above. With basedpyright, `basedpyright --writebaseline` records existing errors in `.basedpyright/baseline.json`.
- import-linter: list existing violations in the contract's `ignore_imports`, such as `"app.domain.models -> app.web.forms"`. By default it fails on an entry that no longer matches an import, so the list shrinks with each cleanup.

## Comment ban (opt-in)

ast-grep's `comment` nodes, with allowed prefixes for the shebang, licence headers and tool directives:

```yaml
# rules/no-comments-python.yml
id: no-comments-python
language: python
severity: error
message: Comments go stale and excuse workarounds. Encode the rule in a type, a lint or a test, or rename the code so it explains itself.
rule:
  kind: comment
  not:
    regex: "^#(!|\\s*(noqa|type:|pyright:|SPDX-License-Identifier|Copyright|-\\*- coding))"
```

Point `sgconfig.yml` at the rule directory with `ruleDirs: [rules]` and run `ast-grep scan`. Docstrings are strings, not comments, so this rule leaves them alone.
