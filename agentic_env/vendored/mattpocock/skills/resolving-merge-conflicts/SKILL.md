---
name: resolving-merge-conflicts
description: "Use when you need to resolve an in-progress git merge/rebase conflict."
---

1. **See the current state** of the merge/rebase. Check git history, and the conflicting files. If the user asks to abort, run the appropriate `--abort` and stop.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made, and what the original intent was. Read the commit messages, check the PRs, check original issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour.

4. Discover the project's **automated checks** and run them, typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage only the conflicted paths you resolved, leaving unrelated work unchanged. Finish with `git merge --continue`, `git rebase --continue`, or a merge commit only when the user asked for the merge/rebase to be finished; otherwise stop with the resolution staged and report. Never push.
