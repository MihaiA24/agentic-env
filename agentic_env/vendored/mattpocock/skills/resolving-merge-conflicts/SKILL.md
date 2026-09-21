---
name: resolving-merge-conflicts
description: "Use when you need to resolve an in-progress git merge/rebase conflict."
---

1. **See the current state** of the merge/rebase. Check git history, and the conflicting files.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made, and what the original intent was. Read the commit messages, check the PRs, check original issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour. Always resolve; never `--abort`.

4. Discover the project's **automated checks** and run them, typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Finishing means committing: a half-resolved merge is a worse state to leave behind than either side. Stage the conflicted paths you resolved, not the whole tree, so unrelated working-tree changes don't ride along in the merge commit. Say what you're about to commit before you commit it, and if the user would rather inspect it first, stop there and leave the resolution staged. If rebasing, continue the rebase process until all commits are rebased.
