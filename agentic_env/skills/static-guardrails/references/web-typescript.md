# TypeScript and web baseline

## Compiler

In `tsconfig.json`, set `compilerOptions`:

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "noImplicitOverride": true,
  "noFallthroughCasesInSwitch": true
}
```

TypeScript has no suppression baseline. When a flag produces many errors, enable it in a second config, such as `tsconfig.strict.json`, whose `include` lists only the clean directories. Run both configs in the check command, and add each directory to the list once its cleanup commit lands.

## ESLint

Use flat config and typescript-eslint's `strictTypeChecked` preset. `reportUnusedDisableDirectives` fails on a disable comment that no longer suppresses anything.

```js
// eslint.config.js
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import comments from "@eslint-community/eslint-plugin-eslint-comments";

export default defineConfig(
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    linterOptions: { reportUnusedDisableDirectives: "error" },
    plugins: {
      "react-hooks": reactHooks,
      "@eslint-community/eslint-comments": comments,
    },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
      "@typescript-eslint/ban-ts-comment": [
        "error",
        { "ts-expect-error": "allow-with-description", "ts-ignore": true, "ts-nocheck": true },
      ],
      "@eslint-community/eslint-comments/require-description": "error",
      "@eslint-community/eslint-comments/no-unlimited-disable": "error",
    },
  },
);
```

Drop the React entries in a repo without React.

## Bans whose errors name the fix

Scope each ban to product directories with `files`. The directory that implements the replacement keeps access. Each message names the replacement, so the agent reads the fix in the error. The examples ban effects and imperative timers; replace the angle-bracket names with the repo's real ones.

```js
{
  files: ["src/features/**/*.{ts,tsx}"],
  rules: {
    "no-restricted-imports": ["error", {
      paths: [{
        name: "react",
        importNames: ["useEffect", "useLayoutEffect"],
        message: "Effects are banned in product code. Use <useSubscription from src/lib/data> for external state, or derive the value during render.",
      }],
    }],
    "no-restricted-syntax": ["error", {
      selector: "MemberExpression[object.name='React'][property.name=/^use(Layout)?Effect$/]",
      message: "Effects are banned in product code. Use <useSubscription from src/lib/data>.",
    }],
    "no-restricted-globals": ["error",
      { name: "setTimeout", message: "Timers patch over ordering bugs. Use <scheduler.after from src/lib/scheduler>, or fix the order of state updates." },
      { name: "requestAnimationFrame", message: "Use <scheduler.nextFrame from src/lib/scheduler>." },
      { name: "requestIdleCallback", message: "Use <scheduler.whenIdle from src/lib/scheduler>." },
    ],
    "no-restricted-properties": ["error",
      { object: "window", property: "setTimeout", message: "Use <scheduler.after from src/lib/scheduler>." },
    ],
  },
}
```

## Import boundaries

For layers or processes that must not import each other, such as `src/electron/main` and `src/electron/renderer`, use dependency-cruiser:

```js
// .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: "renderer-not-to-main",
      comment: "Renderer code runs in the UI process. Call main through <the IPC client in src/electron/renderer/ipc>.",
      severity: "error",
      from: { path: "^src/electron/renderer" },
      to: { path: "^src/electron/main" },
    },
    {
      name: "main-not-to-renderer",
      comment: "Main process code must not load UI modules. Move shared code to <src/shared>.",
      severity: "error",
      from: { path: "^src/electron/main" },
      to: { path: "^src/electron/renderer" },
    },
  ],
  options: { tsConfig: { fileName: "tsconfig.json" } },
};
```

Run it with `depcruise src --config .dependency-cruiser.cjs`. `eslint-plugin-boundaries` is the alternative when the repo wants boundary errors inside ESLint.

## Dead code

Run `knip` for unused files, exports and dependencies. Deleting what it reports removes code an agent would otherwise copy.

## Ratchets

- ESLint: `eslint --suppress-rule <rule>` records, for each file, how many violations of the rule it has in `eslint-suppressions.json`. Only rules set to `"error"` are suppressed. When a change takes a file over its count, ESLint reports every violation of that rule in that file, old ones included. After a cleanup commit, `eslint --prune-suppressions` removes the fixed entries.
- dependency-cruiser: `depcruise-baseline src` writes `.dependency-cruiser-known-violations.json`. The check runs `depcruise src --ignore-known`.
- TypeScript: the per-directory config above.

## Comment ban (opt-in)

Use an ast-grep rule on `comment` nodes, with allowed prefixes for licence headers and tool directives:

```yaml
# rules/no-comments.yml
id: no-comments
language: tsx
severity: error
message: Comments go stale and excuse workarounds. Encode the rule in a type, a lint or a test, or rename the code so it explains itself.
rule:
  kind: comment
  not:
    regex: "^(//|/\\*)\\s*(eslint-|@ts-expect-error|SPDX-License-Identifier|Copyright)"
```

Put the rule in a `rules/` directory and point `sgconfig.yml` at it with `ruleDirs: [rules]`, then run `ast-grep scan`. Add one rule file for each language the repo uses, such as `typescript` and `tsx`.
