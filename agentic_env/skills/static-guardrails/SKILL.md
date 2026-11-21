---
name: static-guardrails
description: "Manual only: set up a repository's deterministic guardrails before agents write code there: compiler strictness, lint bans whose errors name the replacement and that no comment can disable, import boundaries, dead code and suppression rules, with existing violations fixed or listed in a baseline outside the code so only new occurrences fail, proven on a seeded violation, and run by one command locally and in CI. TypeScript and Python baselines included. Run when the user asks: /static-guardrails, \"set up lint and types for agents\", \"tighten the guardrails\". Never start this on your own."
disable-model-invocation: true
---

# Static guardrails

Manual skill. Run it when the user asks for it, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of editing configuration.

Agents copy what the repo already does and take the shortest path that compiles. A rule enforced by the compiler or a linter holds on every change; a rule written in prose holds only when an agent reads it. This skill sets up the deterministic floor: the checks that fail a bad change before anyone reviews it. `/correct` reacts to a mistake made twice; this skill sets the floor up front. Both keep one rule table.

Invocation authorizes working-tree edits to compiler, lint and boundary configuration, rule files, suppression baselines and the check command. Each new dev dependency, each commit, each push of a CI change and each exception approval needs its own go-ahead from the user.

Per-language baselines and exact configuration:

- TypeScript and web: `references/web-typescript.md`
- Python: `references/python.md`

Read them as `skill://static-guardrails/references/<file>` in OMP, or through `skill_view` in Hermes. For any other language, or a pattern the reference's linter cannot express, write ast-grep or Semgrep rules whose `message` names the fix. Both honour suppression comments. Run Semgrep with `--disable-nosem`. ast-grep has no such flag, and an `ast-grep-ignore` comment hides its own line, the next line, or on line 1 the whole file, so the check command also fails on any of them: `if git grep --untracked -nE '(#|//|/\*) *ast-grep-ignore'; then exit 1; fi`.

## 1. Inventory the deterministic layer

Read the repo's configuration and CI workflows. Run nothing that writes. Record, with the file that shows it:

- **Frameworks:** each framework and major library, with its version from the manifest or lockfile.
- **Compiler and types:** strictness flags, and which directories they cover.
- **Lint:** the config, the enabled presets, and the rules that ban a pattern.
- **Suppressions:** the count of each kind, such as `eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `# type: ignore` and `noqa`, and whether each carries a reason.
- **Boundaries:** import rules between layers or processes, and the tool that enforces them.
- **Dead code:** unused files, exports and dependencies, and the tool that finds them.
- **Local equals CI:** the command a developer runs, the command CI runs, and every difference between them.
- **Repeated mistakes:** the patterns the agent instruction file, review comments and reverts warn about, and code comments that justify breaking a project rule, such as "a timer is fine here because…". Each such comment marks a missing rule or a missing replacement.

This step is done when every item has a value or "none", each with its evidence.

## 2. Choose the rules

Keep the tools the repo already runs. Express the language baseline's rules in those tools, and take a new tool from the reference only to fill a gap the inventory found. Then add a rule for each repeated mistake from step 1. For each rule, write down:

- the pattern it bans and the directories it covers;
- the error message, naming the function, hook, module or type to use instead;
- the current occurrence count.

A rule needs a replacement that already exists in the repo. When none exists, ask the user to choose: keep the pattern for now and record the missing replacement as open in the rule table, or design the replacement with `/codebase-design` and add the rule once it lands. Building the replacement is not part of this skill.

For each framework in the inventory, look for checks in this order:

1. Rule sets the repo's linter already ships for it. List them from the linter itself before citing one: `ruff linter` shows `DJ` for Django, `FAST` for FastAPI, `AIR` for Airflow, `PD` for pandas, `NPY` for NumPy and `PT` for pytest. For ESLint, look for the plugin the framework's docs recommend.
2. An official lint or analysis tool the framework documents.
3. A custom ban in the repo's linter, or an ast-grep rule, for misuse that nothing above covers. Take the misuse from step 1's repeated mistakes and from the framework's deprecation notes. A framework with no rule set, such as Spark, gets only custom rules.

Propose each check with its source link and occurrence count. A new plugin or tool is a dev dependency, so it waits for the user's approval.

When two layers or processes share a directory, so the boundary between them shows in no path, propose moving each into its own top-level directory and then banning imports between them. Moving code is design work: report the proposal for the user's approval instead of moving anything.

This step is done when each proposed rule has all three entries, and the user has seen the list.

## 3. Add each rule with a ratchet

A new rule fails only on occurrences a change adds. When a rule has few existing violations, fix them in the same change. When it has too many, record them in a baseline the tool keeps outside the code: ESLint bulk suppressions, a dependency-cruiser known-violations file, a pyrefly or basedpyright baseline, import-linter `ignore_imports`, or ruff `per-file-ignores`. Never write the baseline as suppression comments in the code, as `ruff check --add-noqa` does: agents copy those comments as the established pattern. A tool without a baseline gets the rule only on directories that are already clean; widen the list as each directory is cleaned.

No comment in the code can disable a ban. Block disable comments for every ban rule, as the references show. An exception to a ban goes in the lint configuration, scoped to its file, with its reason, and only after the user approves it. Other rules may keep a disable comment on the line, with its reason.

Plan the cleanup of old occurrences as separate commits, one rule each, and say what each would change. Each cleanup commit also deletes the baseline entries it makes obsolete, because some tools, ruff among them, do not report an entry that no longer matches. Delete deprecated code and dead exports in those commits too, since agents copy whatever they find.

This step is done when the check command passes on the current tree with every new rule enabled as an error.

## 4. Prove each rule

For each rule, write one violation in a scratch change, in a file the rule covers. Run the check command. Confirm that it fails, and that the error names the replacement. For each ban, also try each comment that could turn the rule off: a disable comment on the violation's line, then a file-level one, such as `/* eslint <rule>: "off" */` or `# ruff: noqa: <code>`. Confirm that the command still fails each time. Then revert the scratch change and confirm that the command passes again.

This step is done when every rule has a recorded failing run, its error text and a passing run after the revert.

## 5. Use one command locally and in CI

Make one command run every check: types, lint, boundaries, dead code. Point CI at that same command. Put the CI change in the working tree; pushing it is a separate request.

This step is done when the local command and the CI step invoke the same entry point.

## 6. Record the rules

Add each rule to the rule table in the agent instruction file (`AGENTS.md`, `CLAUDE.md` or the repo's equivalent), pairing the rule with what enforces it. This is the table `/correct` keeps; create it with that shape if it is missing. When a rule leaves nothing to enforce, remove its row.

This step is done when each rule from step 3 has a row naming the check that enforces it.

## Comments

The agent rules file says to write no comments: a decision goes in an ADR, a hack in an issue. This skill enforces only what a tool checks without judgment: commented-out code where the linter has a rule for it, such as ruff `ERA001`, a reason on every disable comment, and no disable comment on a ban. A ban on comments needs each existing comment sorted first; `/delete-comments` sorts them and adds the ban.

## Reply

1. **Inventory:** the step 1 table.
2. **Rules added:** pattern, scope, message, enforcing tool, baseline size.
3. **Proof:** each rule's failing run and error text.
4. **Command:** the local command and the CI step.
5. **Waiting on the user:** each proposed dev dependency, prepared commit, CI push, exception, cleanup commit, directory split, and rule whose replacement is missing.
