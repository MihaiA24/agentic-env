---
name: unslop
description: "Manual only: cut AI tells from any writing. Run it explicitly, or as the named cleanup step of a recipe that produces prose."
disable-model-invocation: true
---

# Unslop

Edit text to remove AI patterns. Scan for the patterns below, then rewrite. Preserve meaning and match the intended tone.

## When to run it

Manual only. If this skill loaded without the user asking for it, stop and say so instead of editing anything; a runtime that ignores `disable-model-invocation` is not an invocation. A user-invoked recipe that composes it by name, or `technical-writing` running its cleanup step, is a real invocation and proceeds normally.

There is no "always apply": a rule that fires on every token gets ignored, and blanket rewriting damages text that was fine. Run it when a recipe names it or the user asks:

- A prose deliverable is about to be handed over: a report, a PR body, a design doc, a README, a changelog entry.
- A skill names it as its cleanup step. `blast-radius` writeups, `why` answers, `show-me-your-work` logs and documentation work all route their final prose through it.
- The user asks for an editing pass on existing text.

Composing it into a recipe means one pass over the finished draft, before it is handed back. Not a running filter on every message, and not a pass over files the task never touched.

## What not to touch

The rules are diagnostics for prose that says nothing, not a blacklist to sweep. Each hit is a question ("does this word earn its place here?"), and the answer is sometimes yes. Never change:

- **Domain vocabulary.** A term the project defines and uses (in a glossary, `CONTEXT.md`, an ADR, or consistently across the codebase) stays, even when it appears on a list below. Renaming it breaks the reader's mapping to the code.
- **Identifiers and literals.** Symbol names, file paths, commands, flags, config keys, error strings, code blocks and anything inside them.
- **Quotations and citations.** Quoted text, commit messages, ticket titles, log output and transcript excerpts are evidence. Edit them and the citation stops matching the source.
- **Calibrated uncertainty.** Hedges that carry meaning ("appears to", "likely", "unproven", confidence tiers, "we searched X and found nothing") are the finding. Rule 24 targets stacked hedging, never the epistemics.
- **The repository's format conventions.** Heading style, table layout, frontmatter, list shape, line width and the house punctuation of the file you're editing. Match the surrounding document.

No mechanical passes. Don't regex a word list out of a file, don't normalize punctuation document-wide, and don't rewrite a section you weren't asked to touch. If a rule's fix would make the sentence less accurate or less concrete, the rule loses.

## Patterns to detect and fix

Rule numbers are stable ids that other skills cite. A removed rule leaves a gap, and renumbering silently breaks every citation. Keep the numbers as they are; if a rule stops applying, leave its number in place.

3. No trailing "-ing" phrases that add no fact ("highlighting...", "ensuring...").
5. No vague attributions ("experts believe"). Name the source or delete.
7. No AI vocabulary: additionally, crucial, delve, enhance, foster, landscape, pivotal, showcase, testament, underscore, vibrant.
8. Say "is" or "has", not "serves as", "stands as", "boasts", "features".
9. No "not just X, but Y". State the point.
10. Don't force ideas into threes.
11. One name per thing. Repeat it.
12. No "from X to Y" unless X and Y sit on a real scale.
13. No em dashes, en dashes, or hyphens used as dashes, and no parentheses in their place. Use a period or a comma.
14. A colon goes before a list or an example, never mid-sentence as a connector.
15. Don't bold every proper noun or acronym.
16. No bold label and colon that restates its line ("**Performance:** Performance improved..."). A bold lead-in that ends in a period and adds new detail is fine.
17. Sentence case headings.
18. No decorative emojis.
19. Straight quotes.
20. No chatbot phrases ("I hope this helps!", "Let me know if...").
22. No praise or agreement openers. Respond directly.
23. Cut filler. "In order to" becomes "to". Delete "it is important to note that".
24. One hedge at most: "may".
25. No generic conclusions. State specific plans or facts.
26. No abstract metaphor nouns: substrate, wedge, vector, nexus, primitive, harness, surface, scaffolding, paradigm, ratchet, north star, flywheel. Use the concrete word.
27. Say what it does, not how it feels. Name the mechanism or the number. Cut a sentence that could appear unchanged in another project's docs.
28. One idea per sentence. Split a sentence the reader has to reread.
29. Active voice. Name the actor unless it is unknown or doesn't matter.
30. Cut adverbs or use a stronger verb. Give the number.
31. Use the plain word: "use", not "utilize" or "leverage".
32. No metaphor, aphorism, personified code, or figurative verb where a literal phrase exists.
33. Write whole sentences with their articles and verbs. Spell out arrows and abbreviations.
