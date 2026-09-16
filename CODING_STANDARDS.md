# Coding standards

Six review lenses, condensed from pstack's `principle-*` skills (`cursor/plugins`
@ `c1c0a32`, MIT) and narrowed where the source overreaches. `/code-review`'s
Standards axis reads this file; each miss is one labelled finding. A repo
standard overrides the reviewer's generic smell list.

**Precedence.** These apply by default. A user instruction overrides any of
them. When it does, say so once — which lens, what it would have wanted, what
was done instead — then proceed. Never re-argue it, never silently comply.

## 1. Prove it works

Check the real thing, never a proxy: run the feature path, read the actual
value, inspect the delegate's diff rather than its summary. When a check fails,
suspect the observation before the system. Script the check when it can be
scripted; keep the output where a reviewer can re-run it. Commit the script
only when the trail must outlive the session.

*Test:* "How would a reviewer re-prove this without trusting me?"

## 2. Build the lever (narrowed)

For repetitive or hard-to-review edits, write the codemod, generator, or query
and re-run it, rather than hand-applying units. Do the first unit by hand to
learn the recipe, then let the tool do the rest and diff it against the hand
version. Narrowing: the lever exists to make work reproducible or reviewable,
not to manufacture a file in the diff. A couple of visible edits need no tool.

*Test:* "Would a reviewer rather read the script or re-do the edits?"

## 3. Minimize reader load

Two independent axes: layers to trace and state to hold. Collapse wrappers with
one caller, adapters with no second implementation, pass-through layers that
repeat the same arguments. Prefer returns over mutation, locals over fields,
fields over module state; derive rather than sync. Name an invariant once, at
the boundary.

*Test:* "Where does X come from? What can change X?" — under thirty seconds for
a new reader, or cut a layer or a piece of state.

## 4. Boundary and type discipline

Validate at boundaries (CLI args, config, network, external APIs, env, DB
rows); trust typed data inside. Parse raw input into domain types once; do not
re-export transport or storage shapes through the public surface. Keep logic in
pure functions the shell merely calls. Make illegal states unrepresentable:
sum types over bags of optionals, branded ids for look-alike primitives,
exhaustive matches the compiler enforces, types derived from the authoritative
schema. Strengthen a type only where a runtime assertion marks it as too weak.

*Tests:* "Is this data crossing a boundary right now?" If not, the check is
redundant. "Can I explain in a comment when this field combination is valid?"
If yes, split the type.

## 5. Separate before serializing shared state

When concurrent actors touch the same mutable thing, first remove the sharing:
own files, keys, branches, or state directories per actor, merged at the read
boundary. Only when one write target is a real invariant, serialize it
structurally (lockfile, sequential phase, single writer, compare-and-swap).
"We need a lock" is a smell to examine, not the default.

*Test:* "Do these actors need one canonical object, or are they publishing
independent facts?"

## 6. Encode lessons in structure

A correction that recurs becomes a mechanism, not a second instruction: an
unrepresentable state, then a lint or banned API that fails CI, then a
canonical helper, then a runtime check. Pick the strongest that fits. If the
fix is structural, delete the instruction; if it needs judgment, make the
instruction prominent and show the failure mode.

*Test:* "Am I writing this instruction for the second time?"
