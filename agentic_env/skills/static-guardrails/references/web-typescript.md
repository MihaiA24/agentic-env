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

Use flat config and typescript-eslint's `strictTypeChecked` preset. `reportUnusedDisableDirectives` fails on a disable comment that no longer suppresses anything. `defineConfig` from `eslint/config` needs ESLint 9.22 or later.

```js
// eslint.config.js
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";
import comments from "@eslint-community/eslint-plugin-eslint-comments";

export default defineConfig(
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    linterOptions: { reportUnusedDisableDirectives: "error" },
    plugins: { "@eslint-community/eslint-comments": comments },
    rules: {
      "@typescript-eslint/ban-ts-comment": [
        "error",
        { "ts-expect-error": "allow-with-description", "ts-ignore": true, "ts-nocheck": true },
      ],
      "@eslint-community/eslint-comments/require-description": "error",
      "@eslint-community/eslint-comments/no-unlimited-disable": "error",
      "@eslint-community/eslint-comments/no-use": ["error", {
        allow: ["eslint-disable", "eslint-disable-line", "eslint-disable-next-line", "eslint-enable"],
      }],
    },
  },
);
```

## Bans whose errors name the fix

Scope each ban to product directories with `files`. The directory that implements the replacement keeps access. Each message names the replacement, so the agent reads the fix in the error. The examples ban a package export, direct console calls and imperative timers; replace the angle-bracket names with the repo's real ones.

```js
{
  files: ["src/features/**/*.{ts,tsx}"],
  rules: {
    "no-restricted-imports": ["error", {
      paths: [{
        name: "<package>",
        importNames: ["<export>"],
        message: "<Why it is banned>. Use <replacement from src/lib/...>.",
      }],
    }],
    "no-restricted-syntax": ["error", {
      selector: "CallExpression[callee.object.name='console']",
      message: "Use <logger from src/lib/log>.",
    }],
    "no-restricted-globals": ["error",
      { name: "setTimeout", message: "Timers patch over ordering bugs. Use <scheduler.after from src/lib/scheduler>, or fix the order of state updates." },
      { name: "requestAnimationFrame", message: "Use <scheduler.nextFrame from src/lib/scheduler>." },
      { name: "requestIdleCallback", message: "Use <scheduler.whenIdle from src/lib/scheduler>." },
    ],
    "no-restricted-properties": ["error",
      { object: "window", property: "setTimeout", message: "Use <scheduler.after from src/lib/scheduler>." },
    ],
    "@eslint-community/eslint-comments/no-restricted-disable": ["error",
      "no-restricted-imports", "no-restricted-syntax", "no-restricted-globals", "no-restricted-properties",
    ],
  },
}
```

`no-restricted-disable` reports each disable comment for a listed rule, so `// eslint-disable-next-line no-restricted-globals -- wait for layout` fails even with its reason. The base config's `no-use` allows only disable and enable comments, so a file-level `/* eslint no-restricted-globals: "off" */` or `/* global */` comment fails too. List every ban rule in `no-restricted-disable`, and add `"boundaries/*"` when the repo uses `eslint-plugin-boundaries`. An approved exception is its own config block after the ban, with the reason in a comment above it:

```js
{
  // <Reason>, approved by <name> on <date>.
  files: ["src/features/<file>.ts"],
  rules: { "no-restricted-globals": "off" },
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

- ESLint 9.24 or later: `eslint --suppress-rule <rule>` records, for each file, how many violations of the rule it has in `eslint-suppressions.json`. Only rules set to `"error"` are suppressed. When a change takes a file over its count, ESLint reports every violation of that rule in that file, old ones included. After a cleanup commit, `eslint --prune-suppressions` removes the fixed entries.
- dependency-cruiser: `depcruise-baseline src` writes `.dependency-cruiser-known-violations.json`. The check runs `depcruise src --ignore-known`.
- TypeScript: the per-directory config above.
