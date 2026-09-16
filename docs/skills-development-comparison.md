# Matt Pocock + pstack: a mixed toolkit for efficient development

Reviewed 2026-09-13. **This comparison does not use this host's installations, invocation history, previous adoption decisions, or familiarity with either author.** It replaces the selection rationale in the earlier [host-oriented fit review](skills-fit-review.md), not that report's installation evidence. Nothing has been installed, removed, activated, or rewritten in either upstream skill pack.

> Adjudicated 2026-09-15 (issue #42): the operative roster, roles, recipes and exclusions are `DECISIONS_AI_TOOLING.md` §6. Where this report and §6 differ (pstack `tdd`, `architect`, `swarm`, the `principle-*` skills), §6 is what is installed and why; the report stays as the evidence it was.

## Conclusion

**Use Matt's skills to clarify intent, define domain language and testable interfaces, and separate specification review from code-quality review. Use pstack's skills to reconstruct system behavior, prove changes against reality, investigate downstream risk, and organize expensive parallel work when it earns its cost.** Neither collection deserves automatic ownership of the whole workflow.

This is not a cosmetic endorsement of a mix. Relative to the earlier host-relative ranking:

- **pstack `tdd` is my first choice for an ordinary bug with a practical regression path.** Matt's `tdd` is my first choice for deliberately test-first feature development at agreed interfaces.
- **pstack `how` is a strong development tool**, not redundant merely because an agent can search code. It specifies the mental model that search must produce.
- **pstack `architect` is a strong option for consequential new architecture.** Matt's `codebase-design` is a lighter design reference; his architecture survey solves a different problem.
- **Matt's `to-spec` and `to-tickets` are valuable when work needs durable transfer and dependency-aware execution.** Lack of previous use is not a reason to reject them.
- **pstack `unslop` and selected principles have independent merit.** They are not rejected because another style or simplicity instruction happens to exist. Their value and overreach are assessed below.

The efficient unit is **the smallest workflow that closes the task's actual uncertainty and produces credible evidence**. Installing both complete packs, or invoking every skill in sequence, is not the recommendation.

### How to read this report

- [Public reviews and evidence quality](#public-reviews-and-evidence-quality)
- [Which skills win each development job](#which-skills-win-each-development-job)
- [The mixed workflows I would use](#the-mixed-workflows-i-would-use)
- [Composition rules and source defects](#composition-rules-and-source-defects)
- [Full Matt catalogue](#full-matt-catalogue)
- [Full pstack catalogue](#full-pstack-catalogue)

## Scope and efficiency criteria

Primary-source coverage is **37 Matt skills** at `3cca18b368ae95cdbdebbff572ccafa662551015` and **47 registered pstack skills** at `cursor/plugins@5bf2b1544db739998121a306340631963c2ff3de`, including 23 principles. Matt's snapshot contains 25 promoted, eight beta, and four misc skills. Three additional pstack Benny automation bodies are considered separately. Current-source behavior is not inferred from old videos, package names, or release marketing. [Matt tree][mp-tree], [Matt maturity policy][mp-beta], [pstack source][ps-poteto-mode].

Efficiency means **verified correct delivery**, evaluated on:

1. Avoided wrong work, repeated investigation, and downstream repair.
2. Quality of the task's actual feedback signal, not how confidently the agent reports success.
3. Agent inference/tool cost, elapsed time, and context consumption.
4. Human decision burden and interruption frequency.
5. Ongoing maintenance of generated tests, documents, scripts, and skill forks.

These criteria are qualitative judgments, not a fabricated score out of ten. A longer run can be efficient if it prevents an expensive regression. A shorter prompt can still launch many agents. Body size alone is not runtime cost. A familiar principle can be valuable if its trigger and prescribed check prevent a common agent error.

Two axes remain separate: **method value** and **execution compatibility**. Both packs use portable instructional text, but some bodies require particular tools, paths, model routing, or supporting skills. Adaptation cost matters; it does not make the underlying method worthless. No current-host usage data enters either axis.

## Public reviews and evidence quality

**A direct review covering both exists.** Public evidence is more useful than a catalogue popularity ranking, but still does not establish a controlled Matt-versus-pstack productivity winner. I read the original auto-generated transcripts for Theo and Rob Shocks rather than relying only on search summaries. Transcription can garble names; exact skill contracts below come from repository bodies.

| Source | What was actually reviewed or tried | What it supports | Evidence limit |
|---|---|---|---|
| [Theo, “So I tried Matt's skills...”][public-theo], Aug 19 | Says he used selected skills from both for a week; demonstrates grilling and prose comparisons; discusses diagnosis, `writing-for-agents`, `arena`, and `blast-radius` | Favors pstack's readable, code-oriented methods while finding real value in Matt's interviewing and diagnosis. Reports `blast-radius` caught consequential issues. Explicitly recommends a mix rather than copying either setup | Practitioner review, not a controlled benchmark. Prose comparisons differ in context/environment; his personal fit ranking is not imported into this review. The video includes a Depot sponsorship |
| [Kayvane, “Skill orchestrations, and what I like about pstack”][public-kayvane], May 28 | Existing use of Matt's `grill-me`/architecture survey, followed by two days with pstack and roughly twelve PRs, described as 3–200 lines each | Reports targeted, understandable bug fixes/refactors; explains the router/playbook/principle structure and shared delegate instructions | Short, self-reported trial without matched baseline, independent quality assessment, or cost accounting. Describes an older catalogue |
| [Rob Shocks, “Pstack Is Agent Overkill. Use It Anyway!”][public-rob], Sep 8 | Builds a skill manager with and without pstack. Reports about 30 minutes without skills versus one hour with pstack, including multi-model design and verification; reports three false agent claims corrected by its audit | Concrete evidence that full pstack can buy more verification while increasing elapsed time and inference. He preferred the more thoroughly checked result | One demonstrated project, self-reported timings and quality, not repeated or controlled; treatment also changes model mix and work performed. Not a comparison with Matt. Includes an OpenRouter sponsorship |
| [Flavio Copes, “A deep dive into pstack”][public-flavio], Aug 21 | Detailed source walkthrough, task examples and opinion; distinguishes `arena`, `swarm`, verification, and orchestration | Strong explanation of why real-app verification and caller-first design matter; warns that a complete multi-model process is excessive for small changes | Much of the usage section is “I would use,” not measured experience. Old counts and some simplified claims need current-source checks |
| [Shin Li, “Learning from Matt Pocock's Agent Skills”][public-shin], May 7 | Reflects on using Claude with the architecture skill and on Matt's published workflow | Supports shared requirements, vertical slices, public-interface tests, and codebase legibility as useful engineering practices | Anecdotal, no cost or defect measurements; older `to-prd`/`to-issues` names and conventional red-green-refactor description |
| [Grant Harvey / The Neuron, pstack explainer][public-neuron], Sep 10 | Synthesizes Lauren's guides and Rob's experiment | Useful overview of verification tooling, feature maps, and risk-weighted compute | Secondary reporting, **not a second independent replication** of Rob's result |
| [Matt's “5 Agent Skills I Use Every Day”][author-matt] | Author describes interviewing, specs, vertical tickets, TDD and architecture improvement | Explains intended design and why the parts compose | First-party experience and advocacy, not independent efficacy evidence; page prose differs from the inspected current TDD body |
| [Lauren's direct comparison][author-lauren], Aug 27 thread | Says Matt helps build understanding and clarify intent; pstack is more code-oriented through sketches/prototypes; explicitly says both can be used | The author's own position supports composition, not exclusivity | First-party opinion, not proof of comparative superiority |

### What the reviews agree on, and where I disagree

**Agreement:** skills are most useful when they change a concrete decision or feedback loop, not simply repeat “be a senior engineer.” Clear requirements, usable code structure, real runtime proof, and readable findings recur across both communities. The strongest first-hand review of both prefers several pstack methods; there is no evidence-based reason to privilege Matt merely because he is more familiar.

**Qualification:** enthusiasm for `arena` does not show that four competing models are efficient on routine work. Rob's experiment illustrates the cost, not a universal doubling of development time. Theo's prose examples support trying `unslop`, not a measured reduction in software defects. Kayvane's small PRs are encouraging but do not isolate the plugin as the cause.

**Corrections from current source:** Flavio's “nothing changes until you approve it” description of `reflect` is too broad: skill edits are approval-gated, while the current body separately instructs automatic Backlog ticket filing. His portability discussion correctly points to ports, but loading `SKILL.md` is not proof that Cursor APIs/transcript paths work unchanged. Matt's own TDD guide and several reviews describe red-green-refactor; the inspected skill explicitly moves refactoring to review. [Reflect][ps-reflect], [current Matt TDD][mp-tdd].

**Lower-weight material screened:** [Tosea's guide][public-tosea] is commercially promotional, uses older names, and overstates prose instructions as mechanical enforcement; [Mervin Praison's roundup][public-mervin] mixes useful description with unverified popularity/release claims; [Hysen Labs' open-pstack review][public-hysen] concerns a port, not a measured original-pack comparison; [The Agent Daily interview summary][public-interview] reports Matt's views rather than testing them. None supplies a comparative score here. [AIKit issue #110][public-aikit] records a concrete mixed-source integration proposal, later superseded by another issue; it shows composition interest, not delivered effectiveness.

**Search result:** I found a direct qualitative comparison, practitioner reports, source walkthroughs, and one pstack-versus-no-skills demonstration. I did **not find a controlled, repeated Matt-versus-pstack development benchmark** among the sources reviewed. Searches included both names together, Lauren Tan/Matt Pocock workflows, and pstack review/benchmark/cost terms. This is a bounded search finding, not a claim no evaluation exists anywhere.

## Which skills win each development job

The choices below are my source-based expectations for helping a coding assistant. “Choose” means select for the named task, not run automatically on every request. `Matt/name` and `pstack/name` are comparison notation, **not newly installed aliases or promised invocation syntax**.

### 1. Clarifying what to build: Matt grilling, with domain modeling when needed

[Matt `grilling`][mp-grilling] asks dependency-ordered rounds of genuine decisions, recommends answers, and obtains factual context from tools rather than interrogating the user about the repository. [Domain modeling][mp-domain-modeling] turns ambiguous concepts into stable terms and records consequential trade-offs. [`grill-with-docs`][mp-grill-with-docs] is their convenient two-skill composition, not a separate planning engine.

**My choice:** Matt for uncertain requirements, product boundaries, invariants, and acceptance criteria. The expected gain is avoiding a correct implementation of the wrong product. Stop when implementation-relevant choices are settled; a small explicit change needs no interview. Document meaningful terms and decisions, not every exchange.

[pstack `interrogate`][ps-interrogate] is not a competing requirements interviewer. It reviews an intent/diff or sketch and assumes the goal is correct. [pstack `architect`][ps-architect] tackles solution shape after grounding. Use these later if needed. Do not force users through an interview about facts a source read can answer.

### 2. Understanding existing software: pstack how, why only for historical rationale

[pstack `how`][ps-how] specifies the useful output: concepts, runtime flow, ownership, important locations, and traps. It selects a simple route or 2–4 exploration angles plus synthesis. Even the simple route delegates once as authored, so it is not zero-overhead. Its distinction between a mental model and annotated source is valuable: I need to know where the invariant lives before editing.

[pstack `why`][ps-why] asks a different question. It searches available historical evidence and separates direct evidence from supported inference or speculation. It should recover why a fallback, threshold, or unusual dependency exists before I delete it. Seven source categories are not a requirement to provision seven services; unavailable or intentionally omitted evidence must be reported. [Confidence model][ps-epistemics].

[Matt `research`][mp-research] is stronger for external APIs, standards, or an unfamiliar technical question requiring primary sources and a saved cited note. It is a small research contract, not a substitute for runtime tracing or historical reconstruction.

**My choice:** `how` for current mechanics, `why` for historical constraints, Matt `research` for outside facts. Compose only the missing views. Reuse an adequate current trace instead of paying to reconstruct it at every stage.

### 3. Architecture: Matt for the design lens, pstack for consequential competing designs

[Matt `codebase-design`][mp-codebase-design] defines the interface as everything callers must know, including invariants, ordering, errors and performance, not just a type signature. Its depth/locality/deletion tests help concentrate responsibility and choose testable interfaces. It is primarily a reference, with deeper design assets when needed.

[pstack `architect`][ps-architect] is a full workflow: `how` grounding, `why` when ownership/history matters, `arena` producing at least two structurally distinct designs, comparison, implementation, and redesign if repeated friction invalidates the sketch. It starts with caller usage. Its default model configuration names four runners. Human sign-off is **opt-in**, and default behavior proceeds into implementation.

**My choice:** Matt's reference for ordinary module/API decisions; pstack `architect` for high-consequence new architecture with genuinely different viable shapes. Supply “with checkpoint; no implementation before approval” when the task is design-only. Never deliver its provisional `not implemented` bodies as the finished feature. Its redesign loop needs a concrete new constraint, not endless preference changes.

[Matt `improve-codebase-architecture`][mp-improve-codebase-architecture] is the best of these for **finding where an existing codebase needs deeper modules**. It produces a candidate survey and asks which to pursue. It is not the same job as designing one already-selected change. Use its shared `codebase-design` criteria in an architect comparison, not an additional whole-repo survey of an already-understood design.

### 4. Specs, tickets and scheduling: Matt for durable contracts; pstack for coverage

[Matt `to-spec`][mp-to-spec] synthesizes resolved context into a specification; it is not another interview. [`to-tickets`][mp-to-tickets] turns a spec/plan into vertically sliced execution tickets with explicit blocking edges. These artifacts let a different agent or human work without inheriting the entire discussion. That is distinct from having a todo tool.

[Matt `wayfinder`][mp-wayfinder] manages an unresolved **decision map** across sessions. It does not replace implementation scheduling. [`implement-spec`][mp-implement-spec] is the actual beta ticket-graph executor with isolated worker branches/worktrees and integration into one PR.

[pstack `swarm`][ps-swarm] defines coverage/race/mixed jobs, selection rules, evidence and dropouts. It is well suited to “check each package/platform/caller group” once boundaries are known. [`figure-it-out`][ps-figure-it-out] creates a bespoke executable playbook for unusual work; it is not the first step for a normal feature.

**My choice:** one acceptance statement for a small task; `to-spec`/`to-tickets` when handoff or parallel delivery needs durable contracts; `wayfinder` only while important decisions remain unresolved; `swarm` for independent coverage. `implement-spec` deserves a bounded trial when a whole issue DAG really must become one PR, but not automatic promotion from beta. One execution owner must coordinate any run; do not nest independent orchestrators over the same work.

### 5. TDD: different winners for features and bugs

| Question | Matt `tdd` | pstack `tdd` |
|---|---|---|
| Main job | Test-first feature development or bugs through agreed public interfaces | Focused failing-before/passing-after regression for a bug |
| Strongest mechanism | Independent expected values, meaningful seams, one vertical red-green slice at a time, anti-mocking guidance | Choose the cheapest meaningful existing test path; reject expensive fixture/harness work that adds little signal |
| Human gate | Requires confirmation of seams before writing tests | No blanket seam interview in the body; choose a practical check from the bug/context |
| Impractical test | Broader seam/design discipline; `implement` says use TDD where possible | Explicitly explain the limitation and use a script, runtime reproduction, browser path or other useful executable check |
| Refactoring | Explicitly deferred to review in the inspected body | Small focused fix and nearby validation, not a full feature-design/refactoring cycle |

**My choice:** **pstack for routine bug regressions; Matt for intentional feature TDD.** This is a meaningful change from defaulting to the previously installed name. Use Matt's test-quality criteria when evaluating a pstack regression, without launching another interview/cycle. A TDD test and real user-journey verification can both be necessary; they answer different questions. Conversely, a well-designed integration test may already be the required runtime evidence. Do not rerun an equivalent check just to satisfy two labels. [Matt body][mp-tdd], [pstack body][ps-tdd].

### 6. Hard bugs and performance: Matt diagnosis, pstack safety and runtime methods

[Matt `diagnosing-bugs`][mp-diagnosing-bugs] has the clearest standalone feedback-driven diagnosis procedure in this pair: obtain a useful exact-symptom check, form/test hypotheses, use debugger or performance evidence, make the root-cause fix, then verify the original path. Its human-assisted observation template is useful when an agent cannot reach the failing environment.

pstack's [runtime-forensics][ps-runtime-forensics] and [trace-forensics][ps-trace-forensics] playbooks are valuable for **diagnosis without an unsolicited fix**. Its [attack-the-premise principle][ps-principle-attack-the-premise] is narrower than its title: after failed fixes share an assumption, look for actor/worker/shard imbalance instead of adding another compensation.

**My choice:** Matt diagnosis as the bug investigation procedure, pstack TDD for a practical regression, and the relevant pstack forensics method for captured profiles or live runtime evidence. Add `why` if the supposedly broken behavior may be intentional. Do not stack a second full bug playbook over a working diagnosis loop.

### 7. Code review: separate conformance, adversarial review and safety proof

- [Matt `code-review`][mp-code-review] answers **“Does it follow the project's standards, and does it implement the intended spec?”** Two independent review axes make omissions and unrequested behavior visible even when the code looks clean. Best general-purpose structured review in this pair.
- [pstack `interrogate`][ps-interrogate] answers **“What can independent models find wrong with this intent/diff?”** Same input/rubric, different model families, and a lead that accepts or rejects findings. Best escalation for a consequential PR; multiple reports are not a vote or proof.
- [pstack `blast-radius`][ps-blast-radius] answers **“Which one or two facts make this safe beyond the diff, and can we execute a check of them?”** Especially valuable for lifecycle order, cache invalidation, schemas, wire formats, and dependency behavior. Source navigation is necessary but does not itself prove safety.

**My choice:** Matt's Standards/Spec split for substantial ordinary work; `blast-radius` when the risk is a concrete downstream assumption; `interrogate` when independent judgment can justify the extra inference and review triage. If both review styles are warranted, give one review effort explicit Standards/Spec coverage plus the adversarial rubric, rather than blindly running two complete panels. That is a proposed composition, not vanilla execution of both skills.

There is a real Matt source mismatch: `code-review` prescribes a diff ending at `HEAD`, but `implement` calls review **before committing**. Newly implemented uncommitted changes can fall outside that diff. Explicitly include the actual WIP scope, including new files, before trusting the review. This is a static contract finding, not a reproduced runtime incident.

### 8. Prototypes and alternatives: Matt for the experiment, pstack for comparison

[Matt `prototype`][mp-prototype] produces a decision artifact: a shareable interactive logic model or distinct UI variants. It tests what a domain model or interaction should be, not whether production implementation is complete. Its UI branch already explores alternatives, so adding another arena is not always useful.

[pstack `arena`][ps-arena] can compare code, designs, explanations or reports. It requires independent candidates, a rubric, choosing a base, selective grafts, and checking the synthesized result. Its differentiator is disciplined selection/integration, not merely “run agents in parallel.”

**My choice:** Matt for one concrete design question or UI exploration; pstack arena where materially different solutions remain and choosing badly would be expensive. If using arena to produce prototypes, frame one candidate-generation phase rather than recursively asking each candidate to launch another multi-variant workflow. Use `swarm`, not arena, for exhaustive coverage of distinct items.

### 9. Verification: pstack's most compelling reusable capability

[`create-verification-skill`][ps-create-verification-skill] inspects the application and creates an operational recipe: Launch, Doctor, Drive, Evidence, Cleanup, plus a feature map. It requires exercising one real feature before delivery. The useful artifact is the **project-specific recipe and driver**, not another global instruction to “verify.”

[`maintain-verification-skill`][ps-maintain-verification-skill] compares the map with source and drives every mapped feature live through one coordinator. It can repair stale verification instructions but must not redefine a product regression as intended behavior.

**My choice:** pstack wins this category. Reuse a good existing driver/recipe; create one only if missing, then run its affected paths during development. The generator is not a command to rerun on every change, and full-map maintenance is not the default gate for a one-line edit. For UI work, interact through the actual UI; for storage, inspect persistence; for an integration, check the communication chain. Never substitute fake state setters for the user path.

This has high expected payoff for me because it replaces repeated rediscovery and unsupported “done” claims with executable knowledge. Initial tooling and maintenance cost can be substantial. Benefits remain an expectation until exercised on real projects.

### 10. Communication, documentation and learning: choose the audience

[pstack `unslop`][ps-unslop] is a strong editorial option for readable implementation reports: concrete mechanisms, named sources, stable terminology, fewer stock phrases and less over-compression. That can reduce the human effort needed to audit my work. It does not improve factual correctness by itself. Its punctuation/word bans are taste, not engineering laws. The current body differs from the “add soul” version in Theo's video.

[pstack `technical-writing`][ps-technical-writing] goes further for tutorials, how-tos, reference and explanation. Its document-purpose discipline is the better choice for human-facing technical docs. [Matt `writing-for-agents`][mp-writing-for-agents] is the better choice for skill bodies, agent instructions, context pointers and completion criteria. These are different audiences, not rival prose styles.

[pstack `teach`][ps-teach] is the better everyday choice for explaining a subsystem or PR. It composes `how` and `why`, preserves evidence confidence, and deliberately avoids quizzes. [Matt `teach`][mp-teach] is the better choice for sustained learning: a teaching workspace, lessons, retrieval practice and learning records. Running both at once would create conflicting teaching contracts. Their image/HTML assumptions also require the actual delivery capability.

For a single confusing response, [`bro`][ps-bro] and [`wait-what`][mp-wait-what] are convenience commands; pick either rather than treating both as new engineering capability.

### 11. Learning from failures and preserving context

[pstack `reflect`][ps-reflect] has the more complete retrospective workflow: judgment/tooling/divergent reviews, synthesis, Accepted/Rejected/Backlog, and approval before selected skill edits. [Matt `retro`][mp-retro] looks more broadly at the working environment, but its beta README still explicitly calls it a nonfunctional stub/design note. **Choose pstack reflect today for a deliberate retrospective**, with external publication separately authorized. Do not run it after every tiny success.

Pair it with [encode-lessons-in-structure][ps-principle-encode-lessons-in-structure]: a recurring mistake may deserve a type invariant, lint rule or repeatable check rather than another paragraph the agent can ignore. [Matt writing-for-agents][mp-writing-for-agents] then helps when the remaining fix really is instructional. [`automate-me`][ps-automate-me] is for intentionally mining histories and authoring a personalized workflow, with commit/PR side effects; not a prerequisite for using a mixed toolkit and not used in this review.

[Matt `handoff`][mp-handoff] prepares portable context for a known transfer. [pstack `recall`][ps-recall] reconstructs missing topic state from previous sessions and shared records, then checks current branches/issues. Preparation and recovery are not substitutes. Use the existing trustworthy capsule when it exists; forensic history mining is for missing or doubtful context. Neither should become a required manual ritual before every continuation.

### 12. pstack principles: useful development checks, not 23 compulsory modes

The highest-value principles for this assistant are:

- **[Prove it works][ps-principle-prove-it-works]:** real artifact evidence before success claims.
- **[Build the lever][ps-principle-build-the-lever]:** a deterministic codemod/check can beat many agents doing repetitive work. The source applies this to any nontrivial task, not just repetition. I recommend narrowing its blanket “must produce a file in the diff” rule: use a tool when it improves execution or reviewability, not to manufacture a deliverable.
- **[Minimize reader load][ps-principle-minimize-reader-load]:** count both indirection and hidden state. Fewer lines alone can make either worse.
- **[Boundary discipline][ps-principle-boundary-discipline] / [type system discipline][ps-principle-type-system-discipline]:** validate external data and encode genuine invariants rather than scatter defensive branches.
- **[Separate before serializing shared state][ps-principle-separate-before-serializing-shared-state]:** isolate writers before adding locks or letting them collide.
- **[Encode lessons in structure][ps-principle-encode-lessons-in-structure]:** convert recurrent, checkable corrections into durable mechanisms.

These can guide the selected task without becoming separate user-facing ceremonies. They complement Matt's design vocabulary rather than proving that either pack owns simplicity. Apply the actual test each principle suggests; saying its name adds no value.

The full principle catalogue below includes narrower tools and overreaches. In particular, “never block on the human” cannot authorize destructive/external actions, “migrate then delete” cannot erase a published compatibility promise, and serial verification should not be interpreted as a full-suite barrier after each keystroke.

## The mixed workflows I would use

These are **routing recipes, not mandatory command chains**. Start from the task's unresolved uncertainty. Once a stage's artifact is adequate, reuse it downstream. No new orchestration framework is required to follow this plan.

### A. Small, well-specified feature

1. Read the relevant implementation and state the observable acceptance condition. Use `how` only if the current mechanism is unclear.
2. Implement the smallest coherent change. If the request is test-first, use Matt `tdd` at agreed seams; otherwise use the existing appropriate check without imposing a TDD interview.
3. Exercise the changed behavior through an existing real-app recipe or focused command. Check the adjacent behavior at risk.
4. Inspect the actual diff for acceptance and correctness; use Matt `code-review` if a structured independent review is warranted.

**Do not add:** a spec issue, ticket graph, architecture arena, multi-model panel, or retrospective for an obvious local change. Completion is checked behavior, not passing through four branded skills.

### B. Uncertain product feature

1. Matt `grilling` + `domain-modeling`: settle users, behavior, invariants, exclusions and consequential choices.
2. Matt `prototype` if an interaction or state model remains uncertain; Matt `research` if external facts block a choice.
3. Matt `to-spec` if implementation must survive handoff; `to-tickets` if several independently verifiable slices are needed. For one session, an explicit acceptance statement may suffice.
4. Use `codebase-design` for the interfaces. Escalate to pstack `architect` only if alternative whole designs have materially different trade-offs; do not add a second independent prototype/arena cascade.
5. Implement one vertical slice, test it, and run the real feature path. Review against the settled spec.

**Stop planning** when the next coherent slice has sufficient constraints and a check. Keep future unknowns explicit rather than specifying imagined details.

### C. Production bug or intermittent failure

1. Matt `diagnosing-bugs`: establish the observable failure and narrow the cause using an appropriate runtime signal.
2. Use pstack `why` only if historical intent affects the diagnosis; use a forensics playbook for captured traces rather than general code guessing.
3. pstack `tdd`: preserve a practical failing-before check, or state why a focused runtime reproduction is the credible alternative.
4. Fix the shared cause; verify the original failure no longer occurs and the neighboring invariant remains intact.
5. Add pstack `blast-radius` if the fix changes lifecycle, concurrency, shared state or downstream behavior. Reserve `interrogate` for consequential residual uncertainty.

**Do not stop** at a passing mock or a newly weakened assertion. **Do not expand** a known local fix into an architecture rewrite without evidence that the design itself is responsible.

### D. Risky API, schema or cross-package migration

1. pstack `how` traces producers/consumers. `why` recovers compatibility and historical constraints where needed.
2. Matt `grilling` settles policy choices, then `to-spec`/`to-tickets` preserves the cutover contract and blocking edges.
3. Use Matt `codebase-design`, or pstack `architect` for a genuinely new shape. Define the dangerous safety facts before changing code.
4. Prefer a deterministic codemod when possible. Otherwise pstack `swarm` covers non-overlapping caller groups with explicit ownership and one integration coordinator. Verify coherent units against isolated states, not another writer's half-finished shared tree.
5. pstack `blast-radius` proves the affected compatibility/lifecycle facts; real-app checks cover the external path. Review Standards/Spec and use a different-model panel only if justified.
6. Remove obsolete internal paths after callers migrate. Retain externally promised compatibility unless the approved release plan ends it. Keep `show-me-your-work` when someone must audit the run afterward.

**Do not combine** `implement-spec` and another scheduler over the same graph. If trialing the beta executor, it owns execution; the task contract still comes from the spec/tickets.

### E. Unfamiliar repository or PR

1. pstack `how` for the current mechanism and ownership.
2. Narrow `why` if motivation is the question; Matt `research` for outside technology facts.
3. pstack `teach` if the human needs a layered explanation; Matt `domain-modeling` only if terminology genuinely needs clarification.
4. End with the traced model and evidence. Do not silently switch a read-only question into a refactor.

**Use Matt `teach` instead** when the goal is a multi-session learning program, not understanding today's PR.

### F. Long parallel delivery

1. Agree a falsifiable finish condition and publication/merge permissions. Resolve shared design contracts first.
2. Use Matt `to-tickets` for persistent work units, pstack `swarm` for a bounded coverage job, or trial Matt `implement-spec` for an entire spec-to-one-PR run. Choose one execution owner.
3. Give each writer separate outputs/worktrees; give reviewers the same intended contract and actual final artifacts. Use `arena` only for competing solutions, not distinct slices.
4. Use pstack `show-me-your-work` for meaningful decisions and evidence pointers, with one canonical writer. It is not a replacement for the evidence files themselves.
5. Integrate and run the real behavior on the integrated result. Parallel individual success is not integration proof.
6. Run `reflect` only if mistakes or costly detours suggest a reusable improvement. Prefer a structural fix over growing the prompt library.

**Do not confuse** wall-clock parallelism with less total inference. Compare the cost of worker setup, duplicate reading, synthesis and merge repair against the work they save.

## Composition rules and source defects

1. **One owner per artifact and execution phase.** A decision map, spec, execution tickets, project verification map and decision trail have distinct jobs. Reuse each one; do not generate multiple versions of the same contract under different skill names.
2. **Resolve name collisions.** Both packs have `tdd` and `teach`. Preserve source qualification or select one deliberate entry point; do not let discovery order silently choose. Comparison notation in this report is not an implemented namespace.
3. **Load dependencies deliberately.** `grill-with-docs` needs grilling/domain modeling; Matt TDD conditionally needs codebase-design; pstack architect needs how/arena and sometimes why; pstack recall's technical-topic path needs why; several pstack skills use unslop. Supporting references belong with the selected skill. A folder copied without its dependencies is not a complete workflow.
4. **Keep real model independence honest.** Four named agents using one model are not a four-family panel. Fewer candidates/reviewers can be a good explicit adaptation, but do not describe that as the unchanged full upstream recipe.
5. **Keep plan and execution permissions separate.** pstack architect implements by default; Matt implement commits on the current branch; triage/spec/ticket skills can publish; reflect has separate automatic Backlog writes. Specify authorized outputs, not just the slash command.
6. **Match review scope to actual changes.** Matt's HEAD-ended diff can omit WIP, especially when composed with pre-commit implement. Include index, working tree and relevant new files when that is the request.
7. **Do not confuse logs and proof.** show-me-your-work's TSV does not seal, revision-bind or freshness-check artifacts. The verification generator initially proves one feature, not the whole map. Maintenance must report product bugs rather than absorb them into expected output.
8. **Prefer principles over unjustified absolutes.** Matt's strict terminology, “two adapters means a real seam,” and return-over-side-effects advice are useful lenses, not universal architecture laws. pstack's no-comments policy can delete rationale; build-the-lever can create needless script artifacts; sequence-verifiable-units prescribes rebasing and per-edit checks that are not appropriate for every branch or concurrent workflow.
9. **One pstack testing heuristic is technically wrong.** `principle-test-behavior-not-implementation` claims a broad group of tests would pass if imported functions returned undefined, including assertion shapes that would fail. Judge whether a test defends a real consumer contract; do not use that heuristic as an automatic deletion classifier. [Source][ps-principle-test-behavior-not-implementation].
10. **Metadata and runtime integration matter.** Many workflows are explicitly user-invoked. A matching description is not permission to auto-trigger them. Cursor model/Task schemas, transcript locations, cloud execution, image generation and project skill roots require actual supported equivalents. The same is true of Matt's Skill-tool calls, tracker conventions, and Claude-only helpers.

For efficient development, **keep the semantic contracts, then make any necessary adaptation explicit and small**. This report recommends no silent rewrites, no full-stack replacement and no installation action.

## How I would establish whether the mix really helps

The public evidence does not justify percentage savings. A future evaluation should compare the same bounded tasks under three conditions: ordinary assistant behavior, the relevant unmodified source workflow where compatible, and the proposed mixed workflow. Fix the model/tool environment and initial repository state, repeat runs, and include failed/blocked runs.

Measure verified acceptance and regressions first; then elapsed time, total inference, human clarification/correction effort, review noise, and maintenance left behind. Include a small feature, difficult bug, architecture choice, and broad migration. Do not reward more tests or more documents unless they defend behavior or enable a real handoff. Do not compare a single-model baseline with four frontier models and attribute the whole difference to wording.

**Not run in this review:** any skill execution, benchmark, installation, upstream helper, or application change. Evidence here is source inspection, public reviews/transcripts, and report completeness/link checks. The rankings are specific, falsifiable hypotheses about workflow value, not measured host outcomes.

## Full Matt catalogue

The catalogue assesses every current skill once. **Primary** means a preferred choice for its development job, not mandatory on every task. **Conditional** means valuable for an explicit larger/specialized task. **Convenience** means a wrapper/rephrasing with limited incremental capability. **Specialized** needs the matching toolchain/integration. **Defer** denotes unresolved maturity or a risky default, not deletion from an installation.

| Skill | Selection | Intrinsic value and limits |
|---|---|---|
| [ask-matt][mp-ask-matt] | Convenience | User-facing menu for choosing the right Matt workflow. Useful for discovery, not a persistent execution controller or a reason to install the whole pack. |
| [claude-handoff][mp-claude-handoff] | Specialized · beta | Hands long work to Claude background agents through `claude --bg --name` and manages them with `claude agents`. Useful if that is the intended runner; otherwise its method needs an explicit runner adaptation. |
| [code-review][mp-code-review] | Primary | Separate Standards and Spec reviewers. Strong general review frame; the authored HEAD-ended diff needs explicit correction when reviewing uncommitted implementation. |
| [codebase-design][mp-codebase-design] | Primary | Deep modules, caller-visible invariants, locality and test seams. Useful even without a redesign ceremony; preserve established domain terms rather than applying its vocabulary bans mechanically. |
| [diagnosing-bugs][mp-diagnosing-bugs] | Primary | Exact-symptom feedback, hypotheses, debugger/performance branches and a human-observation fallback. Best standalone diagnosis procedure here; obtain useful evidence rather than repeatedly guessing patches. |
| [domain-modeling][mp-domain-modeling] | Primary | Build a consistent domain vocabulary and record significant decisions. Valuable where disputed concepts create design errors; avoid renaming a sound established model just to fit the skill. |
| [git-guardrails-claude-code][mp-git-guardrails-claude-code] | Specialized | Installs Claude PreToolUse/Bash safety hooks and edits Claude settings. Useful in that runtime; does not guard tools outside the hook path or replace permissions. |
| [grill-me][mp-grill-me] | Convenience | Thin user entry point to grilling without the documentation composition. Useful for stateless decisions; no additional interview capability beyond grilling. |
| [grill-with-docs][mp-grill-with-docs] | Convenience | Composes grilling and domain modeling. Best entry point when the same discussion should also produce durable terms/decisions; it does not itself create a spec or ticket graph. |
| [grilling][mp-grilling] | Primary | Dependency-aware rounds of questions, recommendations and context gathering. Strongest requirements/decision discovery procedure here; use only while consequential uncertainty remains. |
| [handoff][mp-handoff] | Conditional | Writes a self-contained transfer of goal, state, decisions and next steps. Useful across sessions or agents; do not duplicate an adequate automatic handoff or serialize unnecessary history. |
| [implement][mp-implement] | Convenience | Short TDD-where-possible, check, review and commit wrapper. Useful for an agreed small task; not a scheduler, and review-before-commit exposes the code-review diff-scope mismatch. |
| [implement-spec][mp-implement-spec] | Conditional · beta | Executes a blocking ticket graph with isolated work and integration into one PR. Useful for durable multi-agent delivery; validate tracker/worktree integration and give it sole scheduling ownership. |
| [improve-codebase-architecture][mp-improve-codebase-architecture] | Conditional | Surveys an existing codebase for deepening opportunities and presents candidates in an HTML report before selection. Best for finding the seam to improve, not compulsory before every known local design. |
| [loop-me][mp-loop-me] | Conditional · beta | Interviews about recurring human/automation workflows and records workflow documents. Useful when designing repeated work, not an implementation retry loop; overlaps only part of the problem solved by transcript-driven automate-me. |
| [migrate-to-shoehorn][mp-migrate-to-shoehorn] | Specialized | Migrates TypeScript test construction toward @total-typescript/shoehorn. Appropriate for a deliberate partial-test-data convention, not a generic reason to add a testing dependency. |
| [prototype][mp-prototype] | Conditional | Creates a throwaway logic model or three UI variants for a concrete question. Strong early decision evidence; the prototype and its deliberately simplified behavior are not the production deliverable. |
| [research][mp-research] | Primary | Investigates against trustworthy primary sources and records a cited result. Strong for APIs/standards/unknown facts; skip a separate report when the answer is a trivial known lookup. |
| [resolving-merge-conflicts][mp-resolving-merge-conflicts] | Primary for conflicts | Reconciles competing change intent and verifies the merged behavior. A focused maintenance workflow; the completion criterion is semantic correctness, not merely removal of conflict markers. |
| [retro][mp-retro] | Defer · beta | Broader environment retrospective concept. Its beta README labels it a nonfunctional stub/design note; do not present it as a ready alternative to pstack reflect. |
| [scaffold-exercises][mp-scaffold-exercises] | Specialized | Creates TypeScript course exercises using ai-hero-cli grammar/lint conventions and commits scaffolding. Valuable in that teaching toolchain, not general feature scaffolding. |
| [setup-matt-pocock-skills][mp-setup-matt-pocock-skills] | Specialized | One-time per-project tracker, labels and documentation conventions. Respect existing conventions and the outputs it writes; setup is an integration prerequisite where needed, not development work itself. |
| [setup-pre-commit][mp-setup-pre-commit] | Specialized | Sets up Husky/lint-staged/Prettier and commit-time checks. Useful for that JavaScript workflow if no adequate hook pipeline exists; imposing full checks on every commit can add latency. |
| [setup-ts-deep-modules][mp-setup-ts-deep-modules] | Specialized · beta | Enforces a chosen TypeScript module-entry layout with dependency-cruiser and examples. Useful once the architecture is agreed; a new dependency and boundary policy need a real project requirement. |
| [tdd][mp-tdd] | Primary for feature TDD | Public-interface behavior, independent expectations and one red-green vertical slice. Requires human seam agreement; excellent for deliberate test-first design, more ceremony than pstack for an obvious cheap regression. |
| [teach][mp-teach] | Conditional | A stateful teaching workspace with lessons and learning records. Best for sustained learning rather than a one-off code explanation; pstack teach is intentionally a different learning product. |
| [to-questionnaire][mp-to-questionnaire] | Conditional | Turns unknown stakeholder knowledge into an asynchronous questionnaire and readies its recipient/context. Useful when another human must supply unavailable facts, not a replacement for repository research. |
| [to-spec][mp-to-spec] | Conditional | Synthesizes resolved context into a durable implementation specification. Strong handoff contract; avoid duplicate specs or freezing unresolved design guesses. |
| [to-tickets][mp-to-tickets] | Conditional | Produces vertical work slices and blocking relationships from a spec/plan. Useful for parallel or multi-session delivery; issue creation and tracker writes must be intended. |
| [triage][mp-triage] | Conditional | Turns incoming bugs, features and external PRs into durable agent-ready briefs with tracker state/labels. Useful at the intake boundary; not for re-triaging already-specified self-owned work. |
| [wait-what][mp-wait-what] | Convenience | Repitches one confusing response using simpler technical English. Useful human escape hatch, largely interchangeable with pstack bro; not a lasting language model or correctness check. |
| [wayfinder][mp-wayfinder] | Conditional | Maintains the dependency map of unresolved decisions across sessions. Strong for large ambiguous efforts; do not mistake its decision graph for an implementation scheduler. |
| [wizard][mp-wizard] | Conditional | Authors an interactive shell guide for steps only a human can perform. Useful for credentials, inaccessible dashboards and cutovers; do not transfer agent-executable work to the user or put secrets in logs. |
| [writing-beats][mp-writing-beats] | Conditional · beta | Selects the next grounded narrative beat interactively. Useful for intentional long-form authoring, an alternative editorial approach rather than a compulsory stage after writing-shape. |
| [writing-for-agents][mp-writing-for-agents] | Primary for agent docs | Instruction hierarchy, trigger wording, context pointers and completion contracts. Best for prompts, skills and AGENTS-style documents; needs actual editing and maintenance, not automatic drift detection. |
| [writing-fragments][mp-writing-fragments] | Conditional · beta | Interviews for raw source material before a narrative/article. Useful for human-authored courses and essays, too much ceremony for routine technical change notes. |
| [writing-shape][mp-writing-shape] | Conditional · beta | Organizes source material around reader prerequisites, paragraph by paragraph. Useful structural editing when requested; pstack technical-writing is the more direct default for task-oriented engineering docs. |

## Full pstack catalogue

### Workflow and utility skills

These 24 registered skills are distinct from the 23 principle files below. Supporting playbooks are part of the execution model, not another 23 equivalent standalone skills.

| Skill | Selection | Intrinsic value and limits |
|---|---|---|
| [architect][ps-architect] | Conditional | Ground, sketch competing designs, choose, implement and redesign when evidence invalidates the sketch. Excellent for consequential architecture; defaults to implementation without a human checkpoint and can create provisional stubs. |
| [arena][ps-arena] | Conditional | Independent full attempts, cross-judging, base selection, selective grafting and final verification. Useful when distinct solutions are plausible and expensive to choose wrongly; high total inference and integration cost. |
| [automate-me][ps-automate-me] | Conditional | Mines session histories to author a personalized mode/workflow. Useful for intentional workflow redesign, not neutral skill selection; needs history access and carries file/commit/PR effects. |
| [blast-radius][ps-blast-radius] | Primary for risky changes | Traces effects beyond the diff and executes the key safety facts. Especially useful for shared state, lifecycle, compatibility and hidden consumers; bounded proof is stronger than a long speculative impact list. |
| [bro][ps-bro] | Convenience | Rephrases the preceding answer plainly. Same narrow job as Matt wait-what; retain one preferred entry point rather than pretend these are distinct development tools. |
| [create-verification-skill][ps-create-verification-skill] | Primary when missing | Builds a project Launch/Doctor/Drive/Evidence/Cleanup recipe and feature map, then proves one feature. Strong recurring-development payoff; reuse existing tooling and do not claim full-map validation from initial creation. |
| [figure-it-out][ps-figure-it-out] | Conditional | Designs a bespoke auditable playbook for work no existing recipe fits. Useful for genuinely unusual tasks; do not add a meta-planning phase to an ordinary well-understood edit. |
| [how][ps-how] | Primary | Produces the current system mental model: concepts, runtime flow, ownership and traps. Simple path still delegates once; complex path uses explorers then synthesis. Bound the question and reuse current findings. |
| [interrogate][ps-interrogate] | Conditional | Independent model-family critique of one intent/diff or sketch with lead adjudication. Useful for high-stakes review, not requirements elicitation or proof by majority vote. |
| [maintain-verification-skill][ps-maintain-verification-skill] | Conditional maintenance | Refreshes source/feature maps and has a coordinator drive every feature live. Strong anti-drift capability; reserve the full run for appropriate maintenance, not every minor patch. |
| [make-bot-ui][ps-make-bot-ui] | Specialized | Builds a Cursor/Grok Bot webhook dashboard with Tailscale exposure. Concrete value for that workflow, not a generic app UI skill; networking and external exposure require explicit scope. |
| [no-comments][ps-no-comments] | Do not use wholesale | Delegates aggressive comment deletion through Comment Sicko, including ambiguous rationale. Removing narration is useful; a broad removal policy can erase non-obvious constraints and the reason code is shaped as it is. |
| [poteto-mode][ps-poteto-mode] | Conditional orchestration | Sticky router, explicit playbook steps and shared delegate instructions. Real execution discipline for complex autonomous work, not merely a menu; full policy/dependency load is inappropriate as an unexamined universal default. |
| [recall][ps-recall] | Conditional | Reconstructs topic state from transcripts and shared history, checking current branches/issues. Useful when context is missing or suspect; costs less only if it avoids more expensive rediscovery and needs supported history access. |
| [reflect][ps-reflect] | Conditional | Parallel retrospective perspectives, synthesis and approved skill edits, plus automatic Backlog writes in the source. Best ready retrospective here; restrict external writes to authorized destinations and avoid doing it after every small task. |
| [setup-pstack][ps-setup-pstack] | Specialized | Configures pstack model roles, including multi-model workflows. Useful for faithful execution in the supported runtime; model selection does not port Task APIs, subagent wrappers or external integrations by itself. |
| [show-me-your-work][ps-show-me-your-work] | Conditional | Six-column append-only TSV decision trail for long/unattended work. Useful review context with one canonical writer; not an evidence recorder, freshness checker or cryptographic audit log. |
| [swarm][ps-swarm] | Conditional | Coverage/race/mixed worker orchestration with explicit selection, coverage accounting and merge judgment. Useful beyond native spawning; use disjoint ownership/isolation and do not delegate repetitive deterministic work unnecessarily. |
| [tdd][ps-tdd] | Primary for bug regressions | Choose a cheap meaningful failing check, make the focused fix, confirm it passes, or use a credible runtime fallback. Best pragmatic bug-test procedure in this pair; not a universal feature design process. |
| [teach][ps-teach] | Primary for explanations | Combines bounded how/why investigation into an explanation at the reader's pace. Preserves historical confidence and avoids quizzes; use Matt teach for sustained curriculum, not simultaneously. |
| [technical-writing][ps-technical-writing] | Primary for human docs | Separates tutorials, how-tos, reference and explanation, with reader-focused instructions. More useful than prose shortening alone; use Matt writing-for-agents for agent-consumed contracts. |
| [typescript-best-practices][ps-typescript-best-practices] | Specialized | Concrete TypeScript rules supporting type-system discipline. Useful for TS decisions and review; project language versions and public interface constraints take precedence over blanket stylistic preferences. |
| [unslop][ps-unslop] | Primary editorial option | Concrete wording, consistent names, attributed claims and fewer filler phrases. Strong readability aid, supported by practitioner examples; punctuation bans are optional taste and no substitute for factual verification. |
| [why][ps-why] | Primary when rationale matters | Reconstructs motivation from available history and explicitly distinguishes confidence. Use before removing odd-looking intentional behavior; scope expensive cross-system investigation and disclose missing evidence. |

### Engineering principles

The displayed names omit the common `principle-` prefix; source links preserve the exact upstream names. These ratings concern the rule's engineering value, not whether a separate invocation should occur.

| Principle | Selection | Intrinsic value and limits |
|---|---|---|
| [attack-the-premise][ps-principle-attack-the-premise] | Conditional | After repeated failed fixes share an assumption, measure whether bad outcomes concentrate in particular actors/shards/workers. Useful evidence-led reframing; not a generic invitation to challenge every requirement. |
| [boundary-discipline][ps-principle-boundary-discipline] | Primary | Validate external inputs and keep invariants at the layer that owns them. Reduces scattered guards; first establish what is actually a trust boundary rather than assuming all internal data is safe. |
| [build-the-lever][ps-principle-build-the-lever] | Primary method; narrow default | Prefer deterministic codemods/scripts/checks to repeated manual work or redundant agent fan-out. Source requires a file in the diff for nontrivial work; waive that artifact mandate when existing tools already provide the proof. |
| [encode-lessons-in-structure][ps-principle-encode-lessons-in-structure] | Primary | Move recurring checkable corrections into types, lints, metadata or scripts; retain explicit guidance only where judgment remains. Strong way to reduce repeated prompting rather than grow an instruction archive. |
| [exhaust-the-design-space][ps-principle-exhaust-the-design-space] | Conditional | Compare materially different alternatives before an expensive commitment. Strong for uncertain design, unnecessary for a known fix; one arena/prototype exercise should satisfy the need. |
| [experience-first][ps-principle-experience-first] | Conditional | Judge the user experience before choosing the easiest implementation. Useful in UI/interaction trade-offs; does not justify unrequested polish or ignoring accessibility and reliability. |
| [fix-root-causes][ps-principle-fix-root-causes] | Primary | Reproduce, identify the shared cause and fix it once instead of adding compensations. Reinforces a concrete diagnosis workflow; repeating the slogan without a feedback signal does not diagnose anything. |
| [foundational-thinking][ps-principle-foundational-thinking] | Conditional | Choose data structures and interface shape before burying decisions in logic. Useful for new systems; scaffold-first ordering and temporary breakage need bounded scope and a complete final implementation. |
| [guard-the-context-window][ps-principle-guard-the-context-window] | Conditional | Use bounded delegation and compact evidence to protect the coordinating context. Useful for large independent read sets; delegation setup and repeated reading can cost more than small inline tasks. |
| [laziness-protocol][ps-principle-laziness-protocol] | Primary | Prefer deletion, reuse and the smallest coherent solution before adding machinery. Valuable check against generated bloat; minimizing the diff must not omit a shared root cause or required behavior. |
| [make-operations-idempotent][ps-principle-make-operations-idempotent] | Conditional | Make retries converge to the intended state. Important for jobs, migrations and external operations; add this requirement where retry/crash semantics actually exist, not as speculative infrastructure. |
| [migrate-callers-then-delete-legacy-apis][ps-principle-migrate-callers-then-delete-legacy-apis] | Conditional | Complete authorized internal cutovers rather than preserve parallel APIs. Reduces maintenance once all consumers migrate; externally promised compatibility requires its own release/deprecation contract. |
| [minimize-reader-load][ps-principle-minimize-reader-load] | Primary | Reduce indirection and hidden mutable state; require each layer to hide meaningful decisions. Complements Matt's deep-module model; one caller alone does not prove a function or module is useless. |
| [model-the-domain][ps-principle-model-the-domain] | Conditional | Choose explicit domain states and relationships instead of synchronized flags and accidental structure. Strong code-shaping complement to Matt's vocabulary/ADR workflow, not a duplicate domain glossary. |
| [never-block-on-the-human][ps-principle-never-block-on-the-human] | Conditional; bound authority | Proceed with reversible, source-grounded decisions and expose choices. Useful reduction in unnecessary interruption; cannot authorize destructive actions, external publication or a materially different product requirement. |
| [outcome-oriented-execution][ps-principle-outcome-oriented-execution] | Conditional | Converge on the intended target rather than preserve temporary compatibility layers. Useful during approved rewrites; temporary nonworking states must be isolated and cannot become the delivered result. |
| [prove-it-works][ps-principle-prove-it-works] | Primary | Observe the actual artifact, exercise changed behavior and verify delegated outputs rather than trust reports. A task-specific executable check is stronger than build-only confidence; inspect the full relevant input/output path. |
| [redesign-from-first-principles][ps-principle-redesign-from-first-principles] | Conditional | Ask how the design would look if the new requirement had existed from day one. Useful when repeated patches reveal the wrong model; not permission to redesign unrelated working systems. |
| [separate-before-serializing-shared-state][ps-principle-separate-before-serializing-shared-state] | Primary when sharing matters | Eliminate accidental shared writers before introducing serialization. Strong for concurrency and parallel agents; necessary shared state still needs correct synchronization, not just optimistic isolation claims. |
| [sequence-verifiable-units][ps-principle-sequence-verifiable-units] | Conditional; adapt granularity | Order small coherent units so each can be checked. Useful for migrations and reviewer comprehension; automatic rebase, each-edit gates, or a full suite against concurrently edited state can be unsafe or wasteful. |
| [subtract-before-you-add][ps-principle-subtract-before-you-add] | Conditional | Remove obsolete structure before building on it. Useful for a planned reshape; scope deletion to what the change obsoletes instead of adding an unrelated cleanup phase. |
| [test-behavior-not-implementation][ps-principle-test-behavior-not-implementation] | Keep intent; reject heuristic | Assert real consumer-observable contracts instead of source text or wiring. The blanket undefined-return classification is technically false for several listed assertions; never use it as an automatic test-deletion rule. |
| [type-system-discipline][ps-principle-type-system-discipline] | Primary where types help | Encode meaningful states/invariants and parse at input boundaries. Strong for preventing agent-generated impossible states; brands and type machinery must hide or prevent real complexity, not simply add annotations. |

### Auxiliary playbooks and automation

The full `poteto-mode` brings value beyond a collection of leaf prompts: routed steps, explicit skips and shared delegate instructions can keep a long run from silently dropping work. Its runtime/trace forensics playbooks are useful read-only investigation procedures, and [visual parity][ps-visual-parity] preserves a pre-change baseline and forbids manipulating the harness/baseline to fake a match. For repeated complex work, deliberate full-mode use is reasonable. For a mixed day-to-day workflow, load the task-specific method instead of importing every policy and dependency.

The [Benny automation pack][ps-benny] is outside the registered skills root. Its three bodies were inspected; the deeper adapter/template implementations were not independently audited:

- **setup-benny:** copies/configures the pack, preserves user configuration, verifies committed inputs and control adapters, and hands approved automation setup to Cursor's automation facilities.
- **triage-issue-reports:** processes Slack reports using immutable thread coordinates, configured deduplication and tracker ownership, read-only investigation, and fail-closed publication behavior.
- **reproduce-and-fix-issues:** requires trusted triage provenance, honors existing human/fix ownership, reproduces through the real UI, captures before/after evidence, and permits bounded fixes and draft PRs, not merge/deploy.

These are substantial specialized automation methods, not ordinary slash-command substitutes. Their proof/ownership rules can inform a future incident workflow. Adopting the actual automation requires explicitly selecting its Slack/tracker/app-control integrations and publication permissions; it is not part of this recommendation's initial execution.

## Bottom line

For helping an AI assistant deliver useful software, my preferred mix is **pstack's operational understanding and verification, Matt's intent and interface discipline, and risk-selected review from both**. I would give pstack more responsibility in ordinary execution than the earlier host-biased report did. I would also restore Matt's specs/tickets when they serve a real handoff instead of treating past non-use as a verdict.

Start small at invocation time, not by pretending the other useful skills do not exist. The best default for a well-specified tiny task is still direct work plus a credible check. The best escalation depends on whether the missing piece is intent, system knowledge, design evidence, delivery coordination, or proof.

## Source links

Individual skill links above are pinned to the inspected commits. Public reviews describe their own dates and sometimes earlier skill versions. Recommendations are analysis; source contracts, reported experience and measured outcomes are not interchangeable.

[author-lauren]: https://x.com/poteto/status/2092852487716065681
[author-matt]: https://www.aihero.dev/5-agent-skills-i-use-every-day
[mp-ask-matt]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/ask-matt/SKILL.md
[mp-beta]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/README.md
[mp-claude-handoff]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/claude-handoff/SKILL.md
[mp-code-review]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/code-review/SKILL.md
[mp-codebase-design]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/codebase-design/SKILL.md
[mp-diagnosing-bugs]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/diagnosing-bugs/SKILL.md
[mp-domain-modeling]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/domain-modeling/SKILL.md
[mp-git-guardrails-claude-code]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/git-guardrails-claude-code/SKILL.md
[mp-grill-me]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grill-me/SKILL.md
[mp-grill-with-docs]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/grill-with-docs/SKILL.md
[mp-grilling]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling/SKILL.md
[mp-handoff]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/handoff/SKILL.md
[mp-implement]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/implement/SKILL.md
[mp-implement-spec]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/implement-spec/SKILL.md
[mp-improve-codebase-architecture]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/improve-codebase-architecture/SKILL.md
[mp-loop-me]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/loop-me/SKILL.md
[mp-migrate-to-shoehorn]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/migrate-to-shoehorn/SKILL.md
[mp-prototype]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/prototype/SKILL.md
[mp-research]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/research/SKILL.md
[mp-resolving-merge-conflicts]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/resolving-merge-conflicts/SKILL.md
[mp-retro]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/retro/SKILL.md
[mp-scaffold-exercises]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/scaffold-exercises/SKILL.md
[mp-setup-matt-pocock-skills]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/setup-matt-pocock-skills/SKILL.md
[mp-setup-pre-commit]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/setup-pre-commit/SKILL.md
[mp-setup-ts-deep-modules]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/setup-ts-deep-modules/SKILL.md
[mp-tdd]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/SKILL.md
[mp-teach]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/teach/SKILL.md
[mp-to-questionnaire]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/to-questionnaire/SKILL.md
[mp-to-spec]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/to-spec/SKILL.md
[mp-to-tickets]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/to-tickets/SKILL.md
[mp-tree]: https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills
[mp-triage]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/triage/SKILL.md
[mp-wait-what]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/wait-what/SKILL.md
[mp-wayfinder]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/wayfinder/SKILL.md
[mp-wizard]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/wizard/SKILL.md
[mp-writing-beats]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-beats/SKILL.md
[mp-writing-for-agents]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/writing-for-agents/SKILL.md
[mp-writing-fragments]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-fragments/SKILL.md
[mp-writing-shape]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-shape/SKILL.md
[ps-architect]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/architect/SKILL.md
[ps-arena]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/arena/SKILL.md
[ps-automate-me]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/automate-me/SKILL.md
[ps-benny]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/automations/benny/README.md
[ps-blast-radius]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/blast-radius/SKILL.md
[ps-bro]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/bro/SKILL.md
[ps-create-verification-skill]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/create-verification-skill/SKILL.md
[ps-epistemics]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/references/epistemics.md
[ps-figure-it-out]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/figure-it-out/SKILL.md
[ps-how]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/how/SKILL.md
[ps-interrogate]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/interrogate/SKILL.md
[ps-maintain-verification-skill]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/maintain-verification-skill/SKILL.md
[ps-make-bot-ui]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/make-bot-ui/SKILL.md
[ps-no-comments]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/no-comments/SKILL.md
[ps-poteto-mode]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/SKILL.md
[ps-principle-attack-the-premise]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-attack-the-premise/SKILL.md
[ps-principle-boundary-discipline]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-boundary-discipline/SKILL.md
[ps-principle-build-the-lever]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-build-the-lever/SKILL.md
[ps-principle-encode-lessons-in-structure]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-encode-lessons-in-structure/SKILL.md
[ps-principle-exhaust-the-design-space]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-exhaust-the-design-space/SKILL.md
[ps-principle-experience-first]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-experience-first/SKILL.md
[ps-principle-fix-root-causes]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-fix-root-causes/SKILL.md
[ps-principle-foundational-thinking]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-foundational-thinking/SKILL.md
[ps-principle-guard-the-context-window]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-guard-the-context-window/SKILL.md
[ps-principle-laziness-protocol]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-laziness-protocol/SKILL.md
[ps-principle-make-operations-idempotent]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-make-operations-idempotent/SKILL.md
[ps-principle-migrate-callers-then-delete-legacy-apis]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md
[ps-principle-minimize-reader-load]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-minimize-reader-load/SKILL.md
[ps-principle-model-the-domain]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-model-the-domain/SKILL.md
[ps-principle-never-block-on-the-human]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-never-block-on-the-human/SKILL.md
[ps-principle-outcome-oriented-execution]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-outcome-oriented-execution/SKILL.md
[ps-principle-prove-it-works]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-prove-it-works/SKILL.md
[ps-principle-redesign-from-first-principles]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-redesign-from-first-principles/SKILL.md
[ps-principle-separate-before-serializing-shared-state]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md
[ps-principle-sequence-verifiable-units]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-sequence-verifiable-units/SKILL.md
[ps-principle-subtract-before-you-add]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-subtract-before-you-add/SKILL.md
[ps-principle-test-behavior-not-implementation]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-test-behavior-not-implementation/SKILL.md
[ps-principle-type-system-discipline]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-type-system-discipline/SKILL.md
[ps-recall]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/recall/SKILL.md
[ps-reflect]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/reflect/SKILL.md
[ps-runtime-forensics]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/runtime-forensics.md
[ps-setup-pstack]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/setup-pstack/SKILL.md
[ps-show-me-your-work]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/show-me-your-work/SKILL.md
[ps-swarm]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/swarm/SKILL.md
[ps-tdd]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/tdd/SKILL.md
[ps-teach]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/teach/SKILL.md
[ps-technical-writing]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/technical-writing/SKILL.md
[ps-trace-forensics]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/trace-forensics.md
[ps-typescript-best-practices]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/typescript-best-practices/SKILL.md
[ps-unslop]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/unslop/SKILL.md
[ps-visual-parity]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/visual-parity.md
[ps-why]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/SKILL.md
[public-aikit]: https://github.com/EpiLogos/ai-kit/issues/110
[public-flavio]: https://flaviocopes.com/pstack/
[public-hysen]: https://hysenlabs.com/en/projects/ericlitman-open-pstack
[public-interview]: https://the-agent-daily.org/agentnews/deep-dives/matt-pocock-agentic-engineering-workflow
[public-kayvane]: https://www.kayvane.com/posts/building-a-multi-skill-system
[public-mervin]: https://mer.vin/news/mattpocock-skills-the-skill-pack-topping-github-trending/
[public-neuron]: https://www.theneuron.ai/explainer-articles/pstack-explained-lauren-tans-system-for-trustworthy-ai-agents/
[public-rob]: https://www.youtube.com/watch?v=lUhXa8GiXns
[public-shin]: https://shin13.github.io/notes/learning-from-matt-pocock-agent-skills/
[public-theo]: https://www.youtube.com/watch?v=0oXOOlqVu5M
[public-tosea]: https://tosea.ai/blog/matt-pocock-skills-claude-code-guide
