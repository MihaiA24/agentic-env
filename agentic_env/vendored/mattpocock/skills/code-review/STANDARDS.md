# Coding standards

Six review lenses bundled with `/code-review` and applied in every repository it
reviews. Each miss is one labelled finding on the Standards axis.

**Source.** Condensed from Lauren Tan's pstack `principle-*` skills
(`cursor/plugins` @ `c1c0a32`) and narrowed where the source overreaches: §1
`prove-it-works`, §2 `build-the-lever`, §3 `minimize-reader-load`, §4
`boundary-discipline` and `type-system-discipline`, §5
`separate-before-serializing-shared-state`, §6 `encode-lessons-in-structure`.
Not Matt Pocock's work. Copyright (c) 2026 Lauren Tan, MIT License.

**Precedence.** Highest first: the user's instruction, the reviewed
repository's own standards, these lenses, then the Fowler smell baseline in
`SKILL.md`. A repository standard (`CODING_STANDARDS.md`, `CONTRIBUTING.md` and
similar) adds a rule or overrides one lens; every lens it does not mention
still applies. Where it endorses what a lens would flag, report nothing. When a
user instruction overrides a lens, say once which lens applies, what it would
have wanted, and what you did instead, then proceed. Never re-argue it, and
never comply silently.

## 1. Prove it works

Check the real thing, never a proxy: run the feature path, read the actual
value, inspect the delegate's diff rather than its summary. When a check fails,
suspect the observation before the system. Script the check when possible, and
keep the output where a reviewer can re-run it. Commit the script only when the
trail must outlive the session.

*Test:* "How would a reviewer re-prove this without trusting me?"

## 2. Build the lever (narrowed)

For repetitive or hard-to-review edits, write and re-run a codemod, generator,
or query instead of applying each unit by hand. Do the first unit by hand to
learn the recipe, then let the tool do the rest and diff it against the hand
version. Narrowing: the lever exists to make work reproducible or reviewable,
not to add a file to the diff. A couple of visible edits need no tool.

*Test:* "Would a reviewer rather read the script or re-do the edits?"

## 3. Minimize reader load

Two independent axes: layers to trace and state to hold. Collapse wrappers with
one caller, adapters with no second implementation, pass-through layers that
repeat the same arguments. Prefer returns over mutation, locals over fields,
fields over module state; derive rather than sync. Name an invariant once, at
the boundary.

*Test:* "Where does X come from? What can change X?" A new reader should answer
both in under thirty seconds; otherwise cut a layer or a piece of state.

## 4. Boundary and type discipline

Validate at boundaries (CLI args, config, network, external APIs, env, DB
rows); trust typed data inside. Parse raw input into domain types once; do not
re-export transport or storage shapes through the public API. Keep logic in
pure functions; the shell only calls them. Make illegal states unrepresentable:
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

Turn a recurring correction into a mechanism, not a second instruction. From
strongest to weakest: an unrepresentable state, a lint or banned API that fails
CI, a canonical helper, a runtime check. Pick the strongest that fits. If the
fix is structural, delete the instruction; if it needs judgment, make the
instruction prominent and show the failure mode.

*Test:* "Am I writing this instruction for the second time?"
