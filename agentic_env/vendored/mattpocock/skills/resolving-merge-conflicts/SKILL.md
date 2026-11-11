---
name: resolving-merge-conflicts
description: "Use when you need to resolve an in-progress git merge/rebase conflict."
---

1. **See the current state** of the merge/rebase. Check git history, and the conflicting files. If the user asks to abort, run the appropriate `--abort` and stop.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made, and what the original intent was. Read the commit messages, check the PRs, check original issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour.

4. Discover the project's **automated checks** and run them, typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage the conflicted paths you resolved and the files you changed in step 4 to fix the merge, leaving unrelated work unstaged. Only when the user asked for the merge/rebase to be finished, conclude it with `git merge --continue` (or a merge commit) or `git rebase --continue`, repeating steps 1–4 for each later commit that stops until the rebase completes; otherwise stop with the resolution staged and report. Never push.
