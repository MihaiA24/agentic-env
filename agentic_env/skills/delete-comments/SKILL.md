---
name: delete-comments
description: "Manual only: sort every code comment in a scope as tautology, excuse, stale or decision record, then delete it, draft an issue for the hack it excuses, or move the decision into a minimal ADR, and ban new comments with a ratchet for files not yet cleaned. Reports the lines removed. Run when the user asks: /delete-comments, \"delete the comments\", \"ban comments\". Never start this on your own."
disable-model-invocation: true
---

# Delete comments

Manual skill. Run it when the user asks for it, or when a recipe the user invoked composes it by name. If it loads without either, say so and stop instead of editing code.

Adapted from [Matt Pocock's comment cleanup prompt](https://x.com/mattpocockuk/status/2123798388227403983). Agents copy what the code already does. A comment that excuses a hack lets the hack spread, and a comment that repeats the code goes stale with the next change. A decision belongs in an ADR and a hack in an issue, where each is tracked; the code keeps only tool directives, licence headers and `shortcut:` markers, and a lint ban holds it there.

Invocation authorizes working-tree edits in the scope: deleting comments, writing ADRs, and adding the ban's rule files and its step in the check command. Each new dev dependency, each issue filed, each exception to the ban and each commit needs its own go-ahead from the user.

The scope is what the user names: the whole repo, directories or files. Ask when the request names none.

Exact rule files and commands: `references/ast-grep-rules.md`. Read it as `skill://delete-comments/references/ast-grep-rules.md` in OMP, or through `skill_view` in Hermes.

## 1. List the comments

Write the reference's rule files for each language in the scope, with `files` set to the scope and `ignores` empty. Run the reference's two commands: the comment listing shows each comment the ban would report, and the line count shows, per file, the lines that comments fill on their own.

This step is done when you hold both outputs.

## 2. Sort each comment

Give each listed comment one category and a one-line reason:

- **Tautology:** repeats what the code already shows.
- **Excuse:** lets a hacky implementation pass, so the hack gets copied.
- **Stale:** refers to code or behaviour that no longer exists. Check the names it mentions against the code.
- **Decision record:** an important decision the code cannot show. It must pass the three ADR tests: hard to reverse, surprising without context, the result of a real trade-off. A comment that fails them is a tautology.

This step is done when every listed comment has a category and a reason.

## 3. Act on each category

Work file by file, and finish a file before starting the next, so each file leaves this step either clean or untouched.

- **Tautology, stale:** delete the comment.
- **Excuse:** delete the comment and draft an issue: the hack, its file and line, the comment's text, and the fix when you can see it. File it only after the user approves, through the tracker `docs/agents/issue-tracker.md` names. Ask where issues go when that file is missing.
- **Decision record:** write an ADR in the repo's ADR directory, or `docs/adr/` when it has none, numbered after the highest existing one: `NNNN-slug.md` with a title and one to three sentences giving the context, the decision and why. Add a "Considered options" or "Consequences" section only when a reader would otherwise be surprised. Comments about one decision share one ADR. Then delete the comment.

Every comment you leave is one the next agent copies, so clean as many files as the change can review. Files you leave keep their comments and go into the ratchet in step 4.

This step is done when each file in the scope is either clean or untouched, and each excuse has a drafted issue.

## 4. Ban new comments

Set `ignores` in each rule file to the files that still hold comments. A listed file also accepts new comments, so the reply names these files as the next to clean. ast-grep does not report an entry whose file is now clean, so each later cleanup deletes its own entries.

Add the reference's two check lines to the repo's check command, the one CI runs. ast-grep becomes a dev dependency there, so that change waits for the user's approval; until then, run it through `uvx` or `npx` as the reference shows.

Prove the ban. Add a trailing comment to a code line in a clean file in the scope and run the check command: it fails, and the error is the rule's message. Replace that comment with `# ast-grep-ignore`, or `// ast-grep-ignore` in TypeScript: ast-grep now skips the line, so the command fails on the guard instead. Revert and run the command again: it passes.

This step is done when the check command passes on the tree, with a recorded failing run for the seeded comment and for the ignore comment.

## 5. Count the lines

Take step 1's per-file line counts. The cleaned files' counts add up to the lines this change removed; the ratchet files' counts add up to what cleaning them would shed. Deleted trailing comments come on top: the count covers only comments on lines of their own.

This step is done when the reply can state the lines removed and the lines left in ratchet files.

## Reply

1. **Sorted:** the count per category, with file and line for each excuse and decision record.
2. **ADRs:** each new file and the decision it holds.
3. **Issues:** each draft, waiting for approval.
4. **Ban:** rule files, scope, the ratchet list, the check command lines, and the proof runs.
5. **Lines:** removed by this change, and left in the ratchet files.
6. **Waiting on the user:** each issue to file, the dev dependency, each exception and each commit.
