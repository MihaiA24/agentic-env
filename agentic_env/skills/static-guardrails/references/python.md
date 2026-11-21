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

`banned-api` takes modules and qualified attributes. Each `msg` names the replacement; ruff prints it after "is banned:". Replace the angle-bracket names with the repo's real ones.

Ruff honours `# noqa` for every rule, so `import requests  # noqa: TID251 -- needed for streaming` passes a normal run. Run the ban codes a second time with `--ignore-noqa` in the check command:

```bash
ruff check
ruff check --select TID251 --ignore-noqa
```

`--ignore-noqa` still honours `per-file-ignores`. Put the module that implements the replacement there, and each approved exception, with the reason in a comment on its entry:

```toml
[tool.ruff.lint.per-file-ignores]
"<app/net/http_client.py>" = ["TID251"]  # Implements the replacement.
```

## Types: pyrefly

A repo that already runs a type checker keeps it, in its strictest mode: pyright or basedpyright with `typeCheckingMode = "strict"`, `enableTypeIgnoreComments = false` and `reportUnnecessaryTypeIgnoreComment = "error"`, mypy with `strict = true` and `warn_unused_ignores = true`. Pyright still honours `# pyright: ignore`, and mypy honours `# type: ignore`, so `PGH003` above at least requires a rule code on each one.

A repo without one gets pyrefly 1.0 or later. It is fast enough to run on every change, and `enabled-ignores = []` makes it report errors under `# type: ignore` and `# pyrefly: ignore` comments too:

```toml
[tool.pyrefly]
preset = "strict"
enabled-ignores = []
baseline = "pyrefly-baseline.json"
baseline-matching-mode = "column-ordered"

[[tool.pyrefly.sub-config]]
matches = "<app/legacy/import_shim.py>"
errors = { bad-argument-type = false }  # Wraps an untyped C extension.
```

The `sub-config` block is the shape of an approved exception: one file, the error kinds it may break. Run `pyrefly check`. ty is still in beta, and its `# ty: ignore` comments cannot be turned off.

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

- ruff: fix the existing violations of a new rule, or list each file that has them in `per-file-ignores` with the rule's code. A listed file also accepts new violations of that rule, so clean the listed files first. Never run `ruff check --add-noqa`: it writes a `# noqa` comment on each violation, and agents copy them. Ruff does not report an entry that no longer matches, so each cleanup commit deletes its own entries.
- pyrefly: `pyrefly check --update-baseline` records existing errors in the `baseline` file. With `column-ordered` matching, a new error of the same kind in a listed file still fails. Run `pyrefly check --error-stale-baseline` in the check command, so an entry a cleanup made obsolete fails the run until `pyrefly check --prune-baseline` removes it. Pyrefly's docs mark the baseline experimental. Never run `pyrefly suppress`: it writes ignore comments.
- pyright: keep `typeCheckingMode = "standard"` and list the clean directories in `strict = ["src/app/core"]`, adding each after its cleanup commit. With basedpyright, `basedpyright --writebaseline` records existing errors in `.basedpyright/baseline.json`.
- import-linter: list existing violations in the contract's `ignore_imports`, such as `"app.domain.models -> app.web.forms"`. By default it fails on an entry that no longer matches an import, so the list shrinks with each cleanup.
