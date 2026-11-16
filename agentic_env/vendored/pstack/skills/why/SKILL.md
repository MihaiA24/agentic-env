---
name: why
description: "Manual only: use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Returns a cited read on decisions and tradeoffs. Use how for runtime behavior."
disable-model-invocation: true
---

# Why

Answer from the record, not the code: read the commits and PR discussions that introduced the target and each later change, and other sources if the trail is thin. Cite what the authors wrote, mark your own inferences as inferences, and say what the record does not answer.

`why` is read-only. It reads code, history and the evidence sources the user has already connected and authorized, and writes nothing back to them: no ticket edits, comments, commits or publication.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than investigating; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that calls `why` by name is a real invocation and proceeds normally.
