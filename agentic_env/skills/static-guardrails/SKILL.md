---
name: static-guardrails
description: "Manual only: set up a repository's deterministic guardrails before agents write code there: compiler strictness, lint bans whose errors name the replacement, import boundaries, dead code and suppression rules, ratcheted so only new occurrences fail, proven on a seeded violation, and run by one command locally and in CI. TypeScript and Python baselines included. Run when the user asks: /static-guardrails, \"set up lint and types for agents\", \"tighten the guardrails\". Never start this on your own."
disable-model-invocation: true
---

# Static guardrails

Manual skill. Run it when the user asks for it, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of editing configuration.

Agents copy what the repo already does and take the shortest path that compiles. A rule enforced by the compiler or a linter holds on every change; a rule written in prose holds only when an agent reads it. This skill sets up the deterministic floor: the checks that fail a bad change before anyone reviews it. `/correct` reacts to a mistake made twice; this skill sets the floor up front. Both keep one rule table.

Invocation authorizes working-tree edits to compiler, lint and boundary configuration, rule files, suppression baselines and the check command. Each new dev dependency, each commit, each push of a CI change and each exception approval needs its own go-ahead from the user.

Per-language baselines and exact configuration:

- TypeScript and web: `references/web-typescript.md`
- Python: `references/python.md`

Read them as `skill://static-guardrails/references/<file>` in OMP, or through `skill_view` in Hermes. For any other language, write ast-grep or Semgrep rules whose `message` names the fix.

## 1. Inventory the deterministic layer

Read the repo's configuration and CI workflows. Run nothing that writes. Record, with the file that shows it:

- **Compiler and types:** strictness flags, and which directories they cover.
- **Lint:** the config, the enabled presets, and the rules that ban a pattern.
- **Suppressions:** the count of each kind, such as `eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `# type: ignore` and `noqa`, and whether each carries a reason.
- **Boundaries:** import rules between layers or processes, and the tool that enforces them.
- **Dead code:** unused files, exports and dependencies, and the tool that finds them.
- **Local equals CI:** the command a developer runs, the command CI runs, and every difference between them.
- **Repeated mistakes:** the patterns the agent instruction file, review comments and reverts warn about.

This step is done when every item has a value or "none", each with its evidence.

## 2. Choose the rules

Start from the language baseline in the reference, then add a rule for each repeated mistake from step 1. For each rule, write down:

- the pattern it bans and the directories it covers;
- the error message, naming the function, hook, module or type to use instead;
- the current occurrence count.

A rule needs a replacement that already exists in the repo. When none exists, building it is design work: report the gap instead of adding the rule.

This step is done when each proposed rule has all three entries, and the user has seen the list.

## 3. Add each rule with a ratchet

A new rule fails only on occurrences a change adds. Record the existing ones in the tool's own baseline: ESLint bulk suppressions, a dependency-cruiser known-violations file, a basedpyright baseline, `ruff check --add-noqa`, or import-linter `ignore_imports`. A tool without a baseline gets the rule only on directories that are already clean; widen the list as each directory is cleaned.

Plan the cleanup of old occurrences as separate commits, one rule each, and say what each would change. Delete deprecated code and dead exports in those commits too, since agents copy whatever they find.

This step is done when the check command passes on the current tree with every new rule enabled as an error.

## 4. Prove each rule

For each rule, write one violation in a scratch change, in a file the rule covers. Run the check command. Confirm that it fails, and that the error names the replacement. Then revert the scratch change and confirm that the command passes again.

This step is done when every rule has a recorded failing run, its error text and a passing run after the revert.

## 5. Use one command locally and in CI

Make one command run every check: types, lint, boundaries, dead code. Point CI at that same command. Put the CI change in the working tree; pushing it is a separate request.

This step is done when the local command and the CI step invoke the same entry point.

## 6. Record the rules

Add each rule to the rule table in the agent instruction file (`AGENTS.md`, `CLAUDE.md` or the repo's equivalent), pairing the rule with what enforces it. This is the table `/correct` keeps; create it with that shape if it is missing. When a rule leaves nothing to enforce, remove its row.

## Comments

Banning code comments is opt-in. Add it only when the user asks. Then allow licence headers and tool directives, require a reason on every suppression comment, and enforce the ban with a rule as in the references. A comment that explains a workaround usually marks a missing rule: add that rule instead.

## Reply

1. **Inventory:** the step 1 table.
2. **Rules added:** pattern, scope, message, enforcing tool, baseline size.
3. **Proof:** each rule's failing run and error text.
4. **Command:** the local command and the CI step.
5. **Waiting on the user:** each proposed dev dependency, prepared commit, CI push, exception and cleanup commit.
