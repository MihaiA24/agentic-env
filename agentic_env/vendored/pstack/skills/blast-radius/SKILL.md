---
name: blast-radius
description: "Manual only: find what a change could break somewhere else before it ships, beyond the diff, and prove the one fact it's safe because of by running real code instead of writing it up. Use for 'blast radius of X', 'what could this break', or reviewing a small diff you don't trust."
disable-model-invocation: true
---

# Blast radius

Find what a change breaks somewhere else, before it ships. Use for "blast radius of X", "what could this break", or reviewing a small diff you don't trust yet.

Manual only. If this skill loaded without the user asking for it, stop and say so rather than starting an investigation; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that escalates here by name is a real invocation and proceeds normally.

Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it's shaped that way. Blast radius tells you what it breaks somewhere else.

Listing the callers is not the job. The agent can grep those in a second. The job is the breakage grep won't show you.

## Don't trust your own writeup

A blast-radius writeup that sounds right is worthless. It reads as convincing whether or not it's true. So don't hand back the writeup. Find the one or two facts the whole thing depends on and prove them by running code.

### How sure are you

For each fact the change's safety depends on, get it as far down this list as is cheap, and say where it stopped.

1. You said so. Worthless on its own.
2. You pointed at the line. A real `file:line`, or the library's own source.
3. You showed the bad case can't happen. You walked the failure step by step and it doesn't reach.
4. You ran it. A script or test that calls the real code and fails loud if you're wrong.
5. You reproduced it in the running app.

Any safety fact you can't get to step 4, say so. Don't write it up as settled. Step 4 is usually one small script that imports the same library the app ships and calls the exact function you're worried about.

## What you're allowed to do to prove it

Proving a fact means running code, so this skill runs code. Local, reversible actions are in scope: write a throwaway script or test, run it, call the real library the app ships, read a local database copy, start the app locally and drive it. Clean up the scratch files afterwards.

Out of scope without a separate, explicit authorization: changing production behaviour, touching shared or production data, committing, pushing, opening a PR, posting the writeup anywhere, or editing the change under review. This skill reports; it doesn't ship.

## Steps

1. Read the change. The diff, the symbols it adds, changes, and deletes, and what it now does differently, including the part the diff doesn't spell out. Use `why` step 2 to pull the PR and commits.
2. Find the one fact it's safe because of. Most changes that look risky are safe because of a single fact, like "this call only drops already-dead cache entries and does nothing else". Find that fact. If it holds, most risky cases are cleared at once. Spend your time here, not on a long list of maybes.
3. Look where grep stops. Read the source of the library you call, and check its pinned version and any local patch. Work out when things run: microtasks, unmount and teardown, Solid versus React. Follow what a symbol search misses: the JSON an API returns, a DB column, a wire format, another language reading the same bytes, a feature flag, code three hops downstream.
4. Be honest about each risk. Give it a real chance of happening and a real cost if it does. Keep the risks you confirmed. List the ones you checked and cleared separately. Same rules as `why`. Cite a real `file:line`, a search that finds nothing is still an answer, and never make up a caller or an API.
5. Prove the one fact. Write a script or test that runs the real code, run it, and paste what happened. If you can't prove it cheaply, mark it unproven. Don't overstate.
6. For a big or wide change, consider one explicit multi-model pass. `interrogate` is the escalation: give it the same snapshot and the same one safety fact, and merge what comes back. Only claim multiple models if the runtime actually returned distinct ones; check what each call reports as its provider and model. If it can't, say multi-model review was unavailable and hand back the single-model result. Never present one model under several agent names as model diversity.

## What to hand back

- **What it does.** What changed, including the part that isn't obvious.
- **The one fact it's safe because of.** State it, say which step you got it to, and show the proof. If you couldn't prove it, write unproven.
- **Risks.** Only the real ones. Each names how it breaks, the `file:line`, how likely and how bad, and how to check. Paste the proof for the ones that matter.
- **Cleared.** What you checked and why it's fine.
- **Before you merge.** The cheapest test or repro that catches the real bug, including the script you wrote.

Write it through `unslop`, cite real code, and strip anything private before it goes anywhere public. Publishing is the user's call, not yours.

**Reply:** the writeup above, with the one safety fact either proven or marked unproven.

## Runtime notes

- **OMP:** run proof scripts with `bash` or `eval`; fan out only for genuinely independent risk slices, one `task` call with all items. `interrogate` and the sibling skills `how`, `why` and `unslop` resolve by name through `skill://<name>`.
- **Hermes:** `delegate_task` for slices, `skill_view` to load a sibling skill.
- Model aliases from another harness don't exist here. Use the runtime default unless the user names one you've confirmed.
