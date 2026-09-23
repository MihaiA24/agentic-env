---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow the bundled coding standards and this repo's own?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

Two-axis review of an **immutable snapshot** of the intended change, taken against a fixed point the user supplies:

- **Standards**: does the code conform to the bundled coding standards and this repo's own?
- **Spec**: does the code faithfully implement the originating issue / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings. Both read the same snapshot, so neither reviews a working tree that moved underneath it.

Review reports; it never lands anything. No edits, no commits, no pushes, no PRs, no tracker writes from this skill.

## Process

### 1. Pin the review snapshot

The fixed point is whatever the user named (a commit SHA, branch name, tag, `main`, `HEAD~5`). If they didn't name one, ask for it.

Then pick the **mode**, because committed history is not the scope:

- **`refs`**: review between two committed refs. `--base <fixed point>`, optional `--head <ref>` (defaults to `HEAD`).
- **`wip`**: review work in progress. Committed, staged, unstaged **and untracked** content all count. Name the intended scope with one `--path <repo-relative path>` per path; WIP requires at least one, so unrelated work sharing the working tree stays out of the review.

`--base` is compared directly, not as a three-dot range: when the user means "since we diverged from `main`", resolve the merge-base yourself (`git merge-base main HEAD`) and pass that.

**Never ask the user to commit first.** Pre-commit review is a legitimate request, and committing is an effect this skill is not authorised to cause.

Build the snapshot once, into an absolute directory that does not exist yet:

```
python3 <this skill's directory>/scripts/review_snapshot.py \
  --base <fixed point> \
  --mode wip|refs \
  [--head <ref>] \
  [--path <repo-relative path>]... \
  --output <new absolute directory>
```

Resolve `<this skill's directory>` from wherever this skill was loaded; don't hard-code a checkout path.

Its output directory is the review's only source:

- `tree/` — the whole source at snapshot time, frozen. **This is the review source context**: read files here, including the unchanged neighbours a finding needs, never in the live working tree.
- `diff.patch` — the change against the base, limited to the scope paths. This, not `tree/`, is what's under review: unrelated work sharing the working tree never reaches it.
- `commits.txt` — commits between base and head. Legitimately **empty** when the work isn't committed yet.
- `manifest.json` — `mode`, resolved `base` and `head`, the `scope` paths, the `tree` object id, `symlinks_as_text`, and a `files` map of every file in the snapshot to its sha256, so every reviewer can prove it read the same bytes.

Verify with `python3 <this skill's directory>/scripts/review_snapshot.py --verify <snapshot directory>` before dispatch and after review. A mismatch invalidates the run. Keep reviewer prompts and outputs **outside** the snapshot directory, so they do not change its verified file set.

If the script fails, or the diff is empty, stop and report that. A bad ref or an empty scope fails better here than inside two parallel sub-agents.

### 2. Identify the spec source

The spec is the **intent** of the change, so derive it from whoever stated the intent, in this order:

1. What the user told you this change is for, in this conversation or as an argument.
2. A spec, ticket or issue path the user passed.
3. Issue references (`#123`, `Closes #45`, GitLab `!67`) in `commits.txt` or in the branch name. Fetch them by the workflow in `docs/agents/issue-tracker.md` if the repo documents one; otherwise ask the user how issues are tracked here.
4. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.

An empty `commits.txt` is normal in WIP and means "no commits", never "no spec": keep walking the list. Only when every source is exhausted, ask the user where the spec is; if they say there isn't one, the **Spec** sub-agent skips and the report says "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`. Read each from the snapshot's `tree/` when the snapshot carries it, so a standards file the change itself edits is read at the same instant as the code it governs.

Then read `<this skill's directory>/STANDARDS.md`: six bundled lenses that apply in every repo, whether or not it documents anything. The repo's documents add rules and override a lens rule by rule; every lens they don't mention still applies.

On top of both, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **Documented standards override.** A repo standard or bundled lens always wins; where one endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the snapshot:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Dispatch both sub-agents in parallel

Dispatch both axes in one batch with the runtime's delegation tool. In OMP, use a read-only agent (`scout`) unless a dedicated reviewer has an enforced read-only grant. In Hermes, delegate only with read/query tools if those grants can actually be restricted; otherwise use tool-less one-shots with the complete frozen material supplied inline. A "do not edit" prompt is not a tool permission boundary.

Both prompts must include:

- The **absolute path of the snapshot directory**, and the instruction: read `diff.patch`, `commits.txt` and files under `tree/` only. The live working tree is off limits, because it keeps changing while the review runs. Cite findings as `tree/<path>` plus the quoted hunk.
- The scope paths and resolved refs from `manifest.json`, so a finding can be traced back to the exact reviewed bytes.
- Read-only brief: report findings, change nothing.

**Standards sub-agent prompt** adds:

- The list of standards-source files you found in step 3, **plus the bundled `STANDARDS.md` and the smell baseline from step 3**, both pasted in full (the sub-agent has no other access to them).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule, e.g. `STANDARDS.md §3`); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls. A repo standard overrides a bundled lens rule by rule, and both override the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** adds:

- The path or fetched contents of the spec, plus the stated intent from step 2 (what the user said this change is for) when that is the spec's only source.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
