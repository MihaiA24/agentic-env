# Skills fit review — 2026-09-13

**Historical (2026-09-15):** superseded by [ADR-0010](adr/0010-pstack-vendored-into-the-repo.md) and the current [§6 roster](../DECISIONS_AI_TOOLING.md#6-skills); kept as the installation evidence of 2026-09-13. Counts, pins, and the `implement`/`lean-ctx` references below describe that date, not the stack.

Status: research and recommendations, not an adoption decision. No skills, pins, agent configuration, or memory ownership were changed. [DECISIONS_AI_TOOLING.md](../DECISIONS_AI_TOOLING.md#6-skills) remains operative; the [stack overview](stack-overview.md) describes the intended stack.

**Scope update:** this report contains the earlier host-relative installation assessment. The [host-independent skills development comparison](skills-development-comparison.md) evaluates both catalogues without using installed state, invocation history, or prior adoption decisions. Its recommendations supersede this report's selection ranking, not the installation evidence recorded here. Existing adoption decisions remain unchanged.

## Earlier host-relative recommendation

Keep Matt Pocock's skills as the main engineering workflow. Use pstack for specific missing work products, not as a second operating mode. The strongest curated addition is `codebase-design`, which fills a conditional dependency of the existing `tdd` skill. The biggest pstack opportunity is reliable user-journey verification. The biggest installation risk is assuming that an installed skill is self-contained and portable to OMP.

- **Core:** `grill-with-docs`, then `wayfinder` or `implement` when needed, then `code-review`; `grilling` and `domain-modeling` support the design conversation. Use `diagnosing-bugs`, `resolving-merge-conflicts`, `research`, and `tdd` when the task calls for them, not as a mandatory slash-command sequence.
- **Best pstack fit:** `create-verification-skill`, followed by its verification-maintenance workflow once a real project check exists. `show-me-your-work` is useful for long unattended work; `reflect` for repeated agent mistakes. Their concepts fit better than their Cursor-specific packaging.
- **Situational, not daily:** `prototype`, Matt's `teach`, deliberate `handoff`, targeted architecture work, technical writing, historical rationale investigation, and competing-design experiments.
- **Skip a second style stack:** keep Ponytail/Caveman. Do not bulk-install pstack principles, a second `tdd`/`teach`, or Cursor setup tooling into an OMP-first environment.
- **Keep `recall` exceptional:** pstack's transcript-reconstruction skill is not OMP's Mnemopi recall tool, and pstack `reflect` is not Mnemopi's reflect tool. Neither should become a second automatic memory owner.

Coverage: **37 current Matt Pocock skills + 47 registered pstack skills = 84**, plus three dormant pstack automation bodies considered separately.

These are fit judgments, not measured productivity gains. The review uses the documented work mix: product/backend/data work, issue/PR delivery, benchmarking, stack maintenance, and course preparation. It did not re-mine private project histories or treat August usage figures as current. The previous [Pocock](pocock-skills-fit-report.html) and [pstack](pstack-skills-audit.html) audits have adjudication addenda; this report does not adopt their uncorrected counts or superseded “install everything in Tier 1” conclusions.

## What is actually installed

Method: parse the checkout's [skill-pack manifest](../agentic_env/skill-packs.json), then inspect each named skill directory for a real `SKILL.md`, resolve symlinks, inspect invocation frontmatter, and compare the curated Claude-root copies with the skill store. Counts below are top-level valid skill directories, not usage counts, unique skills summed across agents, or a runtime registry dump. Nested Hermes bundles are not counted.

| Surface | Valid skill directories | Curated 25 present? | Meaning |
|---|---:|---|---|
| `~/.agents/skills` | 39 | All 25 | Canonical store plus 14 extras |
| `~/.claude/skills` | 33 | All 25 | Root OMP is configured to discover, plus 8 extras |
| `~/.hermes/skills` | 50 | All 25 | Larger secondary-agent collection; top-level only |
| `~/.omp/agent/skills` | 2 | Not a curated-pack root | `ponytail`, `codebase-memory-mcp` descriptors |
| `~/.pi/agent/skills` | 17 | Not a curated-pack root | Descriptors plus additional Pocock copies/links |

The default manifest is exactly **25 = Matt 13 + Ponytail 6 + Caveman 2 + pstack 4**. It is a required roster, not a ceiling on what is installed. [The doctor's skill check](../agentic_env/stack_doctor.py) checks required files and the explicit lean-ctx exclusion. It does not reject every extra skill or prove that all skill dependencies resolve.

**Extra skills in the Claude root:** `codebase-design`, `codebase-memory`, `graphify`, `improve-codebase-architecture`, `to-spec`, `to-tickets`, `wait-what`, `wizard`. So “pruned from the default manifest” does not mean “removed from this workstation.”

**Additional store-only extras relative to that root:** `diagnose`, `grill-me`, `loop-me`, `triage`, `write-a-skill`, `writing-great-skills`, `zoom-out`. The store also has old entries without a `SKILL.md`; this review did not count a directory name alone as an installed skill.

### Discovery and ownership caveats

1. `~/.omp/agent/config.yml` sets `enableClaudeUser: true` and `enableAgentsUser: false`. OMP does not mount the store directly as a root.
2. Nine curated Claude-root skills are **real directories, not symlinks**: `code-review`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`, `grilling`, `implement`, `resolving-merge-conflicts`, `tdd`, `wayfinder`. Their `SKILL.md` contents currently match the store. That proves equal bodies today, not shared ownership or future convergence. The overview's all-symlink description is the intended model, not this machine's state.
3. **All four pstack picks** contain `disable-model-invocation: true`. The same flag appears on curated `grill-with-docs`, `wayfinder`, `implement`, `teach`, and `handoff`. They are manual entry points; installing them does not route tasks to them. A composed workflow can still request another skill explicitly. The flag shows the authored invocation contract, not successful execution in every harness.
4. The local skills lock records source, path, folder hash, and timestamps, but no source commit/ref for the inspected entries. A pinned installer manifest does not prove that every live body matches that pin. Source comparisons below distinguish installed text, the pin, and current upstream.
5. `graphify` is installed as an extra even though DECISIONS describes it as on-demand; it is not one of the four managed packs. This review needed no graph build, server activation, or catalogue-wide installation.

### Read-only verification

Ran from `agentic-env`:

```text
uv run --frozen agentic-stack-doctor
curated roster (default) under ~/.claude/skills: PASS — 25 skills
built-in descriptors in ~/.omp/agent/skills: PASS
built-in descriptors in ~/.pi/agent/skills: PASS
config.yml stack contract: PASS — 10 settings
process exit: 1 — OMP version mismatch

omp --version
omp/18.1.19
```

The checkout pins OMP `18.1.14`; the installed binary reports `18.1.19`. The doctor fails on that mismatch, though the overview says versions ahead of pins only warn. It also warned about Hermes/Claude/Codex versions and Hermes's agentmemory arguments. These findings were recorded, not repaired. Skill-presence checks passed; the whole-stack doctor did **not**. This is an installation/source review, not an end-to-end test of all skills or a new usage benchmark.

## How to choose a skill for this workflow

Use three independent questions:

1. **Fit:** does it solve a concrete recurring task, or a valuable occasional task? Rare does not mean unsuitable.
2. **Marginal value:** what does it add beyond native OMP tools, the existing Pocock workflow, Ponytail/Caveman, and Mnemopi?
3. **Portability:** are its required skills, paths, tools, models, scripts, and external services available? “Good idea” and “runs as written” are different judgments.

The labels **core**, **situational**, and **skip as a default** below are recommendations, not replacements for the glossary's Installed/Wired/Adopted skill states. A new ADR or glossary change waits for an actual decision.

## Practical workflow, without a mandatory ceremony

| Situation | Reach for | Stop condition / avoid |
|---|---|---|
| Ambiguous, load-bearing change | `grill-with-docs` | Resolve real decisions; do not interview about facts the agent can inspect |
| Multi-session decisions with unresolved dependencies | `wayfinder` | A shared decision map and next unblocked question/experiment; native OMP owns implementation scheduling |
| Agreed task with testable behavior | `implement` / `tdd` | Observable acceptance, not test scaffolding for every line |
| Regression, exception, performance failure | `diagnosing-bugs` | A discriminating reproduction and demonstrated fix; no blind edit loop |
| Review before merge | `code-review` | Standards and originating spec both covered; keep Ponytail review a distinct complexity lens only when needed |
| Conflicted merge/rebase | `resolving-merge-conflicts` | Preserve both branches' intent and verify the merged behavior |
| Product UI or course-site change | Project-specific verification workflow created with pstack | Drive the actual user journey; lint/test success alone is not the journey |
| Long work the user reviews later | `show-me-your-work` concept | Record meaningful decisions and durable evidence; no second log for routine one-line changes |
| Same agent mistake recurring | `reflect` concept | One reviewed instruction/skill change at the owning source; no unreviewed global rewrite |
| Uncertain state model or interface | `prototype` | Answer the design question, then discard the experiment unless deliberately promoted |
| Learning mission / course preparation | Matt's `teach` | Use its mission and learning records when helpful; distinguish teaching the user from authoring student material |
| Context transfer to another person/harness | `handoff` | A portable state capsule; OMP automatic compaction already handles ordinary context pressure |

## What should not change merely because of this audit

- Do not add more memory providers or make pstack `recall` run on every task.
- Do not install `setup-pstack` or replace OMP's role/model configuration to satisfy a skill.
- Do not convert low invocation counts into an automatic pruning rule.
- Do not silently edit shared skill-store files during a retrospective. Through a Claude-root symlink the edit reaches every agent; in a real copy it makes the copies diverge.
- Do not treat “upstream has no tags” as a reason pinning is impossible. A reviewed commit can be pinned. Choosing and verifying that pin is separate from this source snapshot.

## Matt Pocock: what the source changes in the recommendation

**Snapshot:** current `3cca18b368ae95cdbdebbff572ccafa662551015` (September 4); latest published release remains **v1.2.3**, `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e` (August 6). Current tree contains **37 skills: 25 promoted, 8 beta, 4 misc**. `implement-spec` and `retro` are new since the pin. [Current tree][mp-tree], [release][mp-release], [comparison][mp-compare].

All 13 curated installed bodies match inspected current main. Only `implement` also matches the pinned body; the other twelve differ. This verifies text identity, not installation provenance. The high-fit reference assets are present and current; local `triage` and `loop-me` keep older interview instructions. Local `writing-great-skills` is an obsolete predecessor, not an alias for current `writing-for-agents`. [Changelog][mp-changelog].

### Strongest addition: codebase-design

Recommend adding it to the curated set once implementation is authorized. `tdd` calls it for interface and seam design, but the manifest does not list it; the locally installed extra copy hides that gap. It decides where complexity and observable tests belong, which a generic simplicity rule does not. Use it when a change touches too many callers or a regression has no sensible public seam. Its deepening guide prefers replacing shallow tests once higher-level behavior is covered, rather than adding another layer. OMP still supplies navigation and parallel design execution. [TDD][mp-tdd], [design][mp-codebase-design], [deepening][mp-deepening].

### Important limits of the core composition

- **Grill-with-docs does not itself publish specs or tickets.** It combines an interview with domain documentation. **Wayfinder is a decision map**, not an implementation scheduler: research/prototype/grilling/task tickets resolve uncertainty. Upstream offers `to-spec` and `to-tickets` separately. Leaving them out of the local default is a workflow choice, not proof the contracts are identical. Reopen them if a persistent, independently executable spec or task graph is wanted. [Wrapper][mp-grill-with-docs], [wayfinder][mp-wayfinder], [router][mp-ask-matt].
- **Review scope can miss WIP.** `implement` requests review before committing, while `code-review` prescribes `git diff <fixed-point>...HEAD`. That diff excludes uncommitted, staged, and untracked changes. Keep Standards + Spec review, but include the actual WIP when asked. This is a static source-contract finding, not a reproduced review failure. [Implement][mp-implement], [review][mp-code-review].
- **Tracker setup is a precondition, not a reason to install everything.** `code-review` hard-codes `docs/agents/issue-tracker.md`; wayfinder also needs tracker conventions. The uncurated setup skill supplies GitHub/GitLab/local templates, but the repository's existing configuration may already meet the requirement. Check it before running a skill that writes configuration. [Setup][mp-setup-matt-pocock-skills], [GitLab template][mp-gitlab-template].
- **Safety overrides blanket instructions.** The merge skill says to stage everything and never abort. Do not stage unrelated work or override a user's request to abort. Diagnosis's feedback loop should trust user-established failures, not reconfirm them. [Merge][mp-resolving-merge-conflicts], [diagnosis][mp-diagnosing-bugs].
- **Literal tool names need translation.** Current compositions say “Call the Skill tool”; OMP uses `read skill://…`. That is a portability requirement, not evidence the workflow failed here. [Invocation contract][mp-invocation].

### Useful outside the daily path

- **improve-codebase-architecture:** target a subsystem that keeps causing pain. Ponytail asks what can be deleted; this skill asks which boundaries would make changes and tests local. It is not a scheduled cleanup pass. Its HTML template loads third-party CDN scripts, so its report is not offline despite the self-contained wording. [Survey][mp-improve-codebase-architecture], [HTML asset][mp-architecture-html].
- **writing-for-agents:** a better candidate for deliberate prompt/skill authoring than the obsolete `writing-great-skills`. It covers triggers, pointers, completion criteria, and environment facts. It is still not an automatic doc-drift detector; that earlier rejection stands. [Skill][mp-writing-for-agents].
- **wizard / triage / to-questionnaire:** respectively human-only setup, incoming requests needing clarification, and asynchronous stakeholder questions. Each is a distinct job, so keep them situational. Wizard's template assumes GitHub CI, and triage can comment on and close issues, so neither is read-only advice. [Wizard][mp-wizard], [template][mp-wizard-template], [triage][mp-triage], [questionnaire][mp-to-questionnaire].
- **teach / prototype:** a learning workspace and experimental design evidence. Matt's teach mainly teaches the user; it does not generate arbitrary courses. Prototype's browser-based branches do not cover native mobile UI. [Teach][mp-teach], [prototype][mp-prototype].
- **scaffold-exercises:** downgrade the old sleeper recommendation. It requires Matt's `ai-hero-cli`, TS `main.ts`, and specific course layout/lint; SQL or notebook teaching alone does not make it fit. [Source][mp-scaffold-exercises].
- **retro:** a public beta exists, but the bucket README says “STUB: design notes only, not functional yet.” Its body proposes broader environment improvements, requires the absent `writing-for-agents`, and lacks reflect's approved-patch loop. Keep it on the watchlist, not as a `reflect` replacement. [Retro][mp-retro], [beta status][mp-beta].

### Complete Matt catalogue

**Legend:** U = upstream user-only (`disable-model-invocation: true`); M = model or user. E/P = promoted engineering/productivity; B = beta; X = misc. **C** = one of the current 13 curated names. “Recommended” means keep or propose for Mihai's fit decision, not adopt automatically or run every time. “Skip” means skip from the default, not delete the installed copy.

### Recommended for the relevant OMP workflow

| Skill | Class | Concrete use and why | Limit / overlap |
|---|---|---|---|
| [grill-with-docs][mp-grill-with-docs] **C** | E/U | Decision front door: the interview plus durable terminology/ADRs Mihai already wants | Just a two-skill wrapper; no spec/ticket publication in its own body |
| [grilling][mp-grilling] **C** | P/M | Resolve genuine human decisions in dependency-ordered rounds; facts come from tools | Do not grill facts already discoverable, or treat every small edit as a design interview |
| [domain-modeling][mp-domain-modeling] **C** | E/M | Clarify installed/wired/adopted-style terms and record non-obvious irreversible trade-offs | Glossary/ADR owner, not general narrative memory or a spec scratchpad |
| [wayfinder][mp-wayfinder] **C** | E/U | Multi-session, foggy engineering/course decisions with a shared issue map | Decision graph, **not** implementation ticket executor; heaviest flow |
| [research][mp-research] **C** | E/M | Primary-source reading with a cited durable note before a decision | Uses OMP-native delegation; not a new search/memory system |
| [prototype][mp-prototype] **C** | E/M | Let a domain expert click a state model, or compare portal/course UI structures | Experimental evidence, not production code or ongoing UI regression coverage |
| [implement][mp-implement] **C** | E/U | Short agreed execution contract: build, targeted feedback, review, commit | Mostly orchestration over native OMP; auto-commit/current branch must fit request |
| [tdd][mp-tdd] **C** | E/M | Test-first uncertain behaviour at consumer-visible seams; independent expected values | Conditional interface-design dependency; not a reason to add permanent tests everywhere |
| [code-review][mp-code-review] **C** | E/M | Keep Standards and Spec findings independent for branch/PR review | See HEAD-only WIP blind spot and tracker-path assumption below |
| [resolving-merge-conflicts][mp-resolving-merge-conflicts] **C** | E/M | Preserve both sides' intent using commits/issues/PRs, then finish the operation | Blanket stage-everything and never-abort language cannot override safe scope |
| [diagnosing-bugs][mp-diagnosing-bugs] **C** | E/M | Tight exact-symptom feedback before hypothesis churn; debugger/perf branch | Trust reported failures; don't ritualistically re-confirm already-established facts |
| [codebase-design][mp-codebase-design] | E/M | Best manifest addition: shared test/design vocabulary and a live `tdd` dependency | Use during a real interface/seam choice, not a second forced Ponytail style layer |

### Situational: distinct trigger, deliberate use

| Skill | Class | Concrete use and why | Limit / overlap |
|---|---|---|---|
| [teach][mp-teach] **C** | P/U | Multi-session learning workspace, cited HTML lessons, retrieval practice | Primarily teaches **Mihai**; not a generic student-course scaffolder; local learning records need bounded ownership |
| [handoff][mp-handoff] **C** | P/U | Portable transfer to another harness, directory, colleague, or detached side task | Same-session continuity belongs to automatic compaction; don't add a habit |
| [improve-codebase-architecture][mp-improve-codebase-architecture] | E/U | Target a repeatedly changed subsystem with poor locality/testability; visual candidate survey | Not interchangeable with Ponytail audit; CDN report and three-plus design agents have costs |
| [writing-for-agents][mp-writing-for-agents] | P/M | Author/review skill triggers, steering pointers, doc structure after observed instruction friction | New text can be useful without adopting another default; no automatic drift detector |
| [wizard][mp-wizard] | E/M | Human-only dashboard/credential/approval sequence; reusable or ephemeral script | Bash/template, `.env`, GitHub Actions bias; no GitLab CI writer in template |
| [triage][mp-triage] | E/U | Turn **incoming** bug reports/features/external PRs into durable agent-ready briefs | Requires tracker/labels; not for own already-specified tickets; publishes/comments/closes |
| [setup-matt-pocock-skills][mp-setup-matt-pocock-skills] | E/U | One-time per-repo tracker/label/doc configuration if missing | Existing conventions first; writes docs/instructions; no need to rerun configured repos |
| [to-questionnaire][mp-to-questionnaire] | P/U | Ask a stakeholder who knows something neither Mihai nor the repo knows; async handoff | Grill the recipient/desired answer, not an unknowable subject; not ordinary grilling |
| [wait-what][mp-wait-what] | P/U | Recover a message missing context, not just shorten it | Distinct from Caveman's brevity, but plain “re-pitch with context” often suffices |
| [loop-me][mp-loop-me] | B/U | Design recurring human/automation workflows into `workflows/*.md` | Overlaps grill-with-docs; introduces `NOTES.md`; beta and old installed interview rhythm |
| [implement-spec][mp-implement-spec] | B/U | Whole-spec task graph → one PR via concurrent worktrees | Near-exact overlap with existing OMP fan-out/integration; candidate only if scheduling repeatedly fails |
| [setup-ts-deep-modules][mp-setup-ts-deep-modules] | B/U | Enforce root entry-point imports when a TS project chooses that package layout | Adds dependency-cruiser, committed example, boundary checks/docs; never generic cleanup |
| [writing-fragments][mp-writing-fragments] | B/U | Interview for raw material before writing a course narrative/article | Human-writing exploration, not agent technical documentation |
| [writing-shape][mp-writing-shape] | B/U | Shape supplied raw material paragraph by paragraph with reader prerequisites | Conversation-heavy editorial work; skip for routine implementation reports |
| [writing-beats][mp-writing-beats] | B/U | Choose next narrative beat from grounded concepts, one at a time | Alternative to writing-shape, not an additional mandatory stage |

### Skip from the OMP default / defer pending a specific need

| Skill | Class | Why skip now | What would change the decision |
|---|---|---|---|
| [ask-matt][mp-ask-matt] | E/U | Broad router for the full suite; curated subset makes its prescribed flow partly unavailable, and Mihai already knows his front door | User wants a suite-discovery menu; adapt to actual roster rather than route to absent skills |
| [grill-me][mp-grill-me] | P/U | Wrapper duplicates grilling without domain docs | Truly stateless/non-repo interview; still not needed beside direct grilling |
| [to-spec][mp-to-spec] | E/U | Separate synthesis/publication step already pruned; long user-story template can add weight | Explicitly want an independently buildable spec from a large map/conversation |
| [to-tickets][mp-to-tickets] | E/U | Separate ticket publisher overlaps current planning/native decomposition | Need persistent execution blocking edges, not transient subagent tasks or decision tickets |
| [retro][mp-retro] | B/U | Unreleased beta, README says stub, requires absent writing-for-agents, not an approved-patch loop | Reassess one retrospective front door after upstream maturity is clarified |
| [claude-handoff][mp-claude-handoff] | B/U | Hard-coded `claude --bg --name`, managed with `claude agents`; wrong harness | Deliberately handing off to Claude Code, not native OMP work |
| [git-guardrails-claude-code][mp-git-guardrails-claude-code] | X/M | Claude `PreToolUse`, `Bash` matcher, `.claude/settings.json`; does not guard OMP tool execution | Explicit Claude-only safety-hook request, separately scoped |
| [migrate-to-shoehorn][mp-migrate-to-shoehorn] | X/M | Adds `@total-typescript/shoehorn` using npm and searches TS test assertions; specialized migration not general test quality | Existing shoehorn convention or a demonstrated partial-test-data pain |
| [scaffold-exercises][mp-scaffold-exercises] | X/M | Hard dependency on `ai-hero-cli` course grammar/lint, TS `main.ts`, stubs + commit | Repo actually uses Matt's course toolchain; teaching alone is insufficient |
| [setup-pre-commit][mp-setup-pre-commit] | X/M | Installs Husky/lint-staged/Prettier; full typecheck/tests at commit; not stack-neutral | Explicit JS repo hook setup with no adequate existing hook/check pattern |

## pstack: useful methods, uneven OMP portability

**Snapshot:** `5bf2b1544db739998121a306340631963c2ff3de` (September 13), plugin metadata **0.15.2**, **47 registered skills**, including 23 principles. The prior audit covered 44. The three additional names are `make-bot-ui`, `principle-attack-the-premise`, and `principle-test-behavior-not-implementation`. [Manifest][ps-manifest]. The tags API still returns no tags; that does not prevent pinning a commit.

The installed verification generator and its three examples match current upstream byte-for-byte. `show-me-your-work`, `reflect`, and `recall` bodies differ; show's helper/template are unchanged, while reflect's four reviewer references differ. Most changes are wording/model defaults; the local copies already have the approval and transcript-boundary concerns. The comparisons do not reveal the installed commit.

### The four curated picks, honestly described

| Pick | Actual product | Why it fits | What must be resolved for OMP |
|---|---|---|---|
| [create-verification-skill][ps-create-verification-skill] | A project Launch/Doctor/Drive/Evidence/Cleanup recipe, feature index and seed feature files; one feature must be exercised before delivery | Strongest gap: real action → visible result → persistence/external effect, rather than lint/test-only confidence | Writes `.cursor/skills/verify-<app>` as authored; use a discovered project root, actual platform driver, managed processes, isolated data, and private durable evidence |
| [show-me-your-work][ps-show-me-your-work] | TSV decision trail: timestamp, phase, decision, why, evidence, result; subsequent transcript/reviewer audit | Useful for long work the user reviews later; records pivots, not every tool call | Cursor transcript path and independent-model review require real mapping. Use one canonical writer and existing Run Record destination |
| [reflect][ps-reflect] | Judgment/tooling/divergent reviews → synthesis → Accepted/Rejected/Backlog; selected skill edits require approval | Turns repeated agent corrections into a reviewed, reusable change | Cursor Task/model/transcript/create-skill assumptions; map to canonical authoring ownership. **Backlog ticket filing is automatic in the source, separate from approval-gated skill edits** |
| [recall][ps-recall] | Scoped reconstruction from chats plus shared records, checked against current branches/PRs/issues | Useful after a retention incident or stale handoff, not routine memory retrieval | Cursor history layout and GitLab/GitHub status mapping; normally requires **why's source investigators** for a named technical topic, absent from the four-pick roster |

**Verification is not supplied by installing the generator.** A browser driver is not a native mobile driver. The generated seed map does not prove all features were exercised. First create and run one relevant project recipe; keep its evidence through cleanup. [Feature-map example][ps-feature-map].

**Decision trail is not sealed proof.** The TSV helper does not capture artifacts, hash them to a revision, ensure freshness, publish them, or consume the verification-recorder table. It can point to existing proof but cannot replace its provenance mechanism. The helper has no multi-writer initialization protocol; [INFERENCE] concurrent first writers can race on header creation. One coordinator is the simple safe owner. [Helper][ps-log-helper].

**Reflection is manual and has two write boundaries.** Approved skill edits and automatically filed tracker backlog are separate actions. Recommend local proposals first; no public transcript-derived ticket or global skill edit without the selected scope. Its read-only reviewers and untrusted-transcript handling are worth keeping. The existing digest fallback makes an OMP adaptation easier than copying a Cursor transcript path. [Reflect][ps-reflect], [synthesizer][ps-synthesizer].

**Recall is not self-contained.** Its technical-topic path requires `why`; it also names `unslop` and routes some requests to other pstack workflows. Show/reflect/technical-writing likewise reference siblings or Cursor authoring tools. That is no reason to install every dependency. Either keep a selected contract with explicit supported equivalents, or borrow a narrower method into an existing owner. Do not label a silently reduced workflow “vanilla pstack.”

### Best candidates to try, not a bulk-install list

1. **[maintain-verification-skill][ps-maintain-verification-skill]** — strongest companion **after** a real recipe exists. Source analysis can fan out; one coordinator drives every feature live. It distinguishes stale harness/maps from real product regressions and must not redefine a bug as expected behavior. This is verification maintenance, not proof resealing.
2. **[technical-writing][ps-technical-writing]** — strong for runbooks, explanations, reference and tutorials. Separating document purposes adds something Caveman's brevity lacks. Repository style, explicit uncertainty and Spanish-language needs outrank its personal English/punctuation rules. It references `unslop`; the whole style stack is not needed.
3. **[why][ps-why]** — historical intent from commits, issues, docs and other available records, with Direct/Supported/Inferred/Speculative/Unknown confidence. Code shows what happens, not why its author chose it. Use it before removing a defensive path or changing a threshold. Report unavailable integrations as gaps; do not enable seven services just because source categories exist. [Epistemics][ps-epistemics].
4. **[blast-radius][ps-blast-radius]** — reconsider the old “just fan-out” rejection. Its distinctive question is: **which one or two facts make this change safe, and can we execute code that proves them?** Wire formats, teardown order and dependency patches go beyond symbol references. It suits a tiny diff with wide effects. Native OMP supplies execution, not the choice of safety fact. This recommends reopening the question, not a policy change.
5. **[arena][ps-arena] / [interrogate][ps-interrogate]** — occasional high-stakes alternatives. Arena compares isolated candidates against one rubric, picks a base and grafts in the best parts; it is more than a race. Interrogate gives independent model families the same intent/diff/rubric and returns judgments, not fixes. **It assumes the goal is correct, so it is not a replacement for grilling the plan.** Model diversity must come from real routing, not different agent names.
6. **[automate-me][ps-automate-me]** — only when deliberately consolidating/exporting conventions. It mines histories and writes a personal routing profile, with commit/PR side effects. Existing Ponytail/Caveman/Mnemopi ownership and private transcripts make it a poor routine default.

### Skip as installed defaults, retain the useful ideas

- **poteto-mode/setup-pstack:** a Cursor-oriented workflow router and model configuration, not just style text. It assumes unbundled tools and automation and would add a second operating layer. **Swarm** has useful coverage/race/dropout semantics, but defaults to Cursor cloud workers, not native OMP fan-out. Do not silently upload local context to satisfy it. [Mode][ps-poteto-mode], [setup][ps-setup-pstack], [swarm][ps-swarm].
- **Style/principle cluster:** some distinctions, like indirection versus mutable state or isolating ownership before serializing, can inform the existing owner. That does not justify injecting both. `no-comments` conflicts with load-bearing rationale/ceiling markers. Keep one `tdd` and one `teach` name/owner. [No-comments][ps-no-comments].
- **New attack-the-premise:** keep as a diagnostic idea when two fixes fail under the same assumption and worker/shard/actor imbalance may explain it. It is not the answer to every repeated failure. [Source][ps-principle-attack-the-premise].
- **New test-behavior principle:** its observable-behavior intent fits, but its blanket “still passes when the function returns undefined” classification includes assertions that would fail on undefined. Do not import that heuristic as an automatic test-deletion rule. [Source][ps-principle-test-behavior-not-implementation].
- **make-bot-ui:** a Cursor/Grok Bot webhook dashboard with connector credentials, Tailscale and server exposure, not generic product UI work. It is the wrong default, with large external side effects. [Source][ps-make-bot-ui].
- **Dormant Benny automation:** three auxiliary bodies (`setup-benny`, `triage-issue-reports`, `reproduce-and-fix-issues`) are outside the 47 registered skills. Their product is Slack/tracker/app-control/PR automation, not a free OMP capability. Keep them parked unless that exact integration is requested. [Automation README][ps-benny].

### Complete pstack catalogue

Compatibility labels: **Portable guidance** covers the method; sibling dependencies may be unresolved. **Mostly portable** keeps style/sibling assumptions. **Adapt** needs substantive path/tool/model/write-contract mapping. **Cursor-specific / not as written** is not a direct OMP workflow.

“Recommended” means a fit for Mihai to consider or keep, not installation/wiring/adoption. Every row links to the immutable inspected body.

### Recommended (7)

| Skill | OMP compatibility | Concrete trigger, incremental value and limit |
|---|---|---|
| [create-verification-skill](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/create-verification-skill/SKILL.md) | Adapt | Create a Paw portal/course-site user-journey driver where no reusable real-app recipe exists. Captures action, result and persistence; generated paths are Cursor-specific. |
| [maintain-verification-skill](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/maintain-verification-skill/SKILL.md) | Adapt | After feature/routes/auth changes, or before trusting an old verification map. Audits every feature in source and live; product regressions are reported, not rewritten as expected behavior. |
| [show-me-your-work](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/show-me-your-work/SKILL.md) | Adapt | An unattended migration or multi-phase run needs a reviewable decision trail. Reuse the existing Run Record destination, not a competing log. |
| [reflect](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/reflect/SKILL.md) | Adapt | After a correction or costly dead-end exposed a durable workflow gap, explicitly request a retrospective; review proposed skill changes before applying any. |
| [why](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/SKILL.md) | Adapt | Before changing a defensive path, threshold or puzzling design decision, reconstruct the historical reason and translate it into Preserve/Change/Avoid/Risk constraints. |
| [blast-radius](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/blast-radius/SKILL.md) | Adapt | Before merging a small diff touching cache eviction, teardown, schema/wire format or shared library behavior, execute the safety fact symbol search cannot prove. |
| [technical-writing](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/technical-writing/SKILL.md) | Mostly portable | When revising a source-backed runbook, ADR explanation, beginner tutorial or PR brief, separate document purposes and remove ambiguity without compressing away grammar. |

### Situational (17)

| Skill | OMP compatibility | Concrete trigger, incremental value and limit |
|---|---|---|
| [recall](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/recall/SKILL.md) | Adapt | Explicit forensic recovery after a retention-canary alert or a stale handoff. Bound topic, workspace and time; keep Mnemopi the only narrative memory owner. |
| [automate-me](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/automate-me/SKILL.md) | Adapt | When deliberately consolidating or exporting Mihai’s cross-harness conventions, mine repeated corrections and let the user approve the resulting routing profile. Not another everyday style layer. |
| [interrogate](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/interrogate/SKILL.md) | Adapt | A high-stakes PR needs independent different-model adversarial reviews against one intent statement. Not plan grilling: it explicitly assumes the goal is correct. |
| [arena](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/arena/SKILL.md) | Adapt | Two plausible module/UI/document shapes remain after grounding; produce competing artifacts, choose a base against a rubric, and graft specific winning ideas. |
| [swarm](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/swarm/SKILL.md) | Not as written | An explicit coverage matrix, model race or best-of run needs a declared selection rule and dropout accounting. Use OMP native workers; upstream defaults to Cursor cloud workers. |
| [how](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/how/SKILL.md) | Adapt | Onboarding into an unfamiliar subsystem needs a coherent runtime/ownership explanation, not just graph results. Retain the explain-output contract; native tools handle discovery. |
| [teach](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/teach/SKILL.md) | Adapt | Explain a change/subsystem to a learner who needs mechanism plus rationale, layered diagrams and follow-up pacing. Not a substitute for Spanish course authoring. |
| [figure-it-out](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/figure-it-out/SKILL.md) | Adapt | An unusual, unattended cross-repo migration has no narrower playbook and needs falsifiable completion, hypothesis loops and a decision trail. Existing planning remains the entry point. |
| [typescript-best-practices](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/typescript-best-practices/SKILL.md) | Mostly portable | A TS domain model admits contradictory state or unvalidated external data. Useful concrete syntax; apply selectively against repo idioms, not on every .ts read. |
| [principle-attack-the-premise](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-attack-the-premise/SKILL.md) | Portable guidance | Two fixes sharing an assumption fail the same gate and imbalance is concentrated in certain actors. Write the assumption and measure per actor before another compensating fix. |
| [principle-boundary-discipline](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-boundary-discipline/SKILL.md) | Portable guidance | While designing an API/CLI/config boundary, parse external data once and keep business logic independent of framework wiring. Do not interpret trust internally as eliminating real runtime invariants. |
| [principle-build-the-lever](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-build-the-lever/SKILL.md) | Portable guidance | Repeated edits or proof collection can become a small rerunnable codemod/query. Valuable reproducibility lens; reject its unconditional file-in-diff requirement for every nontrivial task. |
| [principle-exhaust-the-design-space](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-exhaust-the-design-space/SKILL.md) | Portable guidance | A novel UI interaction or architecture has no established pattern; compare structurally distinct prototypes. Existing prototype/grill workflow can own the method. |
| [principle-experience-first](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-experience-first/SKILL.md) | Portable guidance | Choosing Paw UX, course exercises or an internal API: weigh the consumer and next maintainer, not just implementation effort. Broader than the prior audit’s UI-only framing. |
| [principle-make-operations-idempotent](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-make-operations-idempotent/SKILL.md) | Portable guidance | Designing update/install/cleanup commands or crash-restarted processing; ask whether reruns converge after partial completion. Not a mandate to add retries. |
| [principle-separate-before-serializing-shared-state](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md) | Portable guidance | Multiple agents/processes write state; first separate owned files/keys, then serialize only a genuinely canonical writer. Useful design review beyond native fan-out scheduling. |
| [principle-type-system-discipline](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-type-system-discipline/SKILL.md) | Portable guidance | A new typed boundary or domain model needs sum types, branded values or exhaustive variants. Its strongest nuance is to strengthen types only where an operation is otherwise partial. |

### Skip (23)

| Skill | OMP compatibility | Concrete trigger, incremental value and limit |
|---|---|---|
| [architect](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/architect/SKILL.md) | Adapt | For a new deep-module seam, use existing codebase-design/domain-modeling/grill flow. Caller-first sketches are useful, but mandatory how→arena and default implementation overshoot a design-only request. |
| [bro](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/bro/SKILL.md) | Portable guidance | If the last answer is jargon-heavy, ask for plain language directly. One restatement instruction needs no additional installed skill. |
| [make-bot-ui](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/make-bot-ui/SKILL.md) | Cursor-specific | Only reconsider for an explicitly requested Cursor/Grok Bot webhook dashboard exposed over Tailscale, not a generic Paw UI or OMP dashboard. |
| [no-comments](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/no-comments/SKILL.md) | Cursor-specific | During comment cleanup, keep Ponytail’s judgment and load-bearing why/ceiling markers. Upstream delegates to Comment Sicko and deletes ambiguous comments/constraints; not a safe style replacement. |
| [poteto-mode](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/SKILL.md) | Cursor-specific | Only reconsider a complete Cursor workflow pilot. It is an extensive router/control system, not merely concise style, and conflicts with the OMP-first ownership already chosen. |
| [setup-pstack](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/setup-pstack/SKILL.md) | Cursor-specific | Configure pstack inside a deliberate Cursor pilot only. It writes an always-applied ~/.cursor/rules/pstack-models.mdc; it does not configure OMP role models. |
| [tdd](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/tdd/SKILL.md) | Mostly portable | A bug has a cheap regression path: use the installed Pocock TDD/diagnosis flow and existing harness verification rules, not a second skill with the same name. |
| [unslop](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/unslop/SKILL.md) | Portable guidance | Human-facing prose needs editing: borrow literal mechanisms, stable terminology and no vague attribution into the existing writing owner. Do not force its punctuation/whole-sentence policy alongside Caveman. |
| [principle-encode-lessons-in-structure](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-encode-lessons-in-structure/SKILL.md) | Portable guidance | A recurring instruction should become a lint/metadata/runtime check. Already embedded in reflect’s routing and the environment’s engineering rules; retain the principle there. |
| [principle-fix-root-causes](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-fix-root-causes/SKILL.md) | Portable guidance | A bug repeats or a guard would mask it: installed diagnosing-bugs and Ponytail already own reproduce/instrument/fix-at-source. |
| [principle-foundational-thinking](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-foundational-thinking/SKILL.md) | Portable guidance | Choosing data shape and phase order: existing domain-modeling/design handles it. Do not add a separate scaffold-first policy. |
| [principle-guard-the-context-window](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-guard-the-context-window/SKILL.md) | Portable guidance | Bulk results threaten context: native read selectors, artifact pointers, delegation and automatic compaction already manage it; the skill adds no memory mechanism. |
| [principle-laziness-protocol](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-laziness-protocol/SKILL.md) | Portable guidance | A refactor grows layers/signal threading: Ponytail/codebase-design can apply flat traceability and one decision owner without duplicate forced style. |
| [principle-migrate-callers-then-delete-legacy-apis](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Portable guidance | An internal API cutover is authorized: current harness already mandates caller inventory, migration and old-path deletion in one cutover. |
| [principle-minimize-reader-load](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-minimize-reader-load/SKILL.md) | Portable guidance | A reviewer cannot trace value origin or mutation: keep its two-axis indirection/state test inside existing design/review, not another style trigger. |
| [principle-model-the-domain](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-model-the-domain/SKILL.md) | Portable guidance | Stateful branches and synchronized booleans proliferate: existing domain-modeling already owns domain vocabulary and structure. |
| [principle-never-block-on-the-human](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-never-block-on-the-human/SKILL.md) | Portable guidance | A reversible implementation choice is answerable from context: current harness already proceeds; this skill does not grant permission for external actions. |
| [principle-outcome-oriented-execution](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-outcome-oriented-execution/SKILL.md) | Portable guidance | A planned migration allows temporary broken states: existing clean-cutover contract and explicit verification boundaries own this decision. |
| [principle-prove-it-works](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-prove-it-works/SKILL.md) | Portable guidance | Before calling work done, exercise the real artifact: native verification rules and recorder already own this norm, while create/maintain add the missing project recipes. |
| [principle-redesign-from-first-principles](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-redesign-from-first-principles/SKILL.md) | Portable guidance | A new requirement repeatedly fights an old design: use existing design/grill/Ponytail review rather than broadening every change into a redesign. |
| [principle-sequence-verifiable-units](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-sequence-verifiable-units/SKILL.md) | Portable guidance | A serial migration can be proven unit by unit: borrow the delivery order, not its always-rebase and verify-every-edit prescription that conflicts with concurrent OMP waves. |
| [principle-subtract-before-you-add](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-subtract-before-you-add/SKILL.md) | Portable guidance | A scoped refactor has dead weight: Ponytail already removes it before adding, without new prompt weight or unrelated cleanup. |
| [principle-test-behavior-not-implementation](https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-test-behavior-not-implementation/SKILL.md) | Portable guidance | Reviewing weak or mock-only tests: existing observable-contract rules already cover it, and upstream’s blanket undefined-return heuristic has incorrect examples. |

## Proposed order and watchlist

No item below has been adopted by this report.

| Priority | Recommendation | Revisit/use trigger |
|---|---|---|
| 1 | Complete the curated `tdd` → `codebase-design` dependency, and explicitly scope pre-commit review to WIP | Next authorized curated-roster/skill-contract maintenance; local extras should not mask default gaps |
| 2 | Use `create-verification-skill` on one real project, with OMP-compatible ownership/driver/evidence paths | A concrete user journey lacks repeatable real-surface evidence |
| 3 | Add the maintenance workflow to that project rather than another unused global promise | A verification map exists and app/harness behavior changes |
| 4 | Try `technical-writing` for an actual runbook/tutorial, and `why` before a historical design reversal | Named document or unresolved past rationale; not default chat styling or every tiny why question |
| 5 | Reconsider `blast-radius` as a targeted safety-fact review | Small diff with broad lifecycle/schema/dependency consequences |
| 6 | Use decision trails and approved retrospectives on consequential runs | Work will be reviewed asynchronously, or an agent mistake has recurred |
| Watch | `arena`, `interrogate`, targeted architecture survey, wizard, triage, questionnaire | Competing designs, independent high-stakes review, poor locality, human-only setup, incoming requests, or unavailable stakeholder knowledge |
| Watch | `writing-for-agents` and Matt `retro` | Deliberate agent-doc authoring; for retro, clarify upstream maturity and compare one retrospective front door |
| Skip by default | Whole pstack mode/style stack, duplicate skill names, Cursor-only bot/cloud/Slack automation, specialized Matt course/JS setup scripts | Reopen only for the actual matching harness/toolchain/integration—not because the skill title sounds relevant |

## Questions for the next decision round

**Q1 — First pstack trial:** should the first real exercise target user-journey verification, historical/safety review, or documentation/teaching? **Recommendation:** verification first, because it produces an observable artifact the existing generic verification rules do not supply.

**Q2 — Retrospective publication boundary:** should retrospective findings remain local proposals until approved, or may they automatically create backlog tickets in a named tracker? **Recommendation:** local proposals; approve skill patches and external ticket publication separately. This boundary is independent of which capability is tried first.

The answers choose the next work. They do not implicitly authorize global skill rewrites, tracker writes, or removal of installed extras.

## Source references

Skill links point at the exact inspected commits, not the moving `main`. Local installation facts come from the filesystem/lock/frontmatter inventory and the read-only doctor run above. Historical fit context comes from the two adjudicated reports and the operative DECISIONS document. Supporting scripts were read where relevant, not executed or fully security-audited. This report claims no end-to-end OMP port and no productivity benchmark.

[mp-architecture-html]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/improve-codebase-architecture/HTML-REPORT.md
[mp-ask-matt]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/ask-matt/SKILL.md
[mp-beta]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/README.md
[mp-changelog]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/CHANGELOG.md
[mp-claude-handoff]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/claude-handoff/SKILL.md
[mp-code-review]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/code-review/SKILL.md
[mp-codebase-design]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/codebase-design/SKILL.md
[mp-compare]: https://github.com/mattpocock/skills/compare/6acc160e4e0cd062dbbbd7a1b26ae92855edf07e...3cca18b368ae95cdbdebbff572ccafa662551015
[mp-deepening]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/codebase-design/DEEPENING.md
[mp-diagnosing-bugs]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/diagnosing-bugs/SKILL.md
[mp-domain-modeling]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/domain-modeling/SKILL.md
[mp-git-guardrails-claude-code]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/git-guardrails-claude-code/SKILL.md
[mp-gitlab-template]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md
[mp-grill-me]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grill-me/SKILL.md
[mp-grill-with-docs]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/grill-with-docs/SKILL.md
[mp-grilling]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling/SKILL.md
[mp-handoff]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/handoff/SKILL.md
[mp-implement]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/implement/SKILL.md
[mp-implement-spec]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/implement-spec/SKILL.md
[mp-improve-codebase-architecture]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/improve-codebase-architecture/SKILL.md
[mp-invocation]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/.agents/invocation.md
[mp-loop-me]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/loop-me/SKILL.md
[mp-migrate-to-shoehorn]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/misc/migrate-to-shoehorn/SKILL.md
[mp-prototype]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/prototype/SKILL.md
[mp-release]: https://github.com/mattpocock/skills/releases/tag/v1.2.3
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
[mp-wizard-template]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/wizard/template.sh
[mp-writing-beats]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-beats/SKILL.md
[mp-writing-for-agents]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/writing-for-agents/SKILL.md
[mp-writing-fragments]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-fragments/SKILL.md
[mp-writing-shape]: https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/in-progress/writing-shape/SKILL.md
[ps-arena]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/arena/SKILL.md
[ps-automate-me]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/automate-me/SKILL.md
[ps-benny]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/automations/benny/README.md
[ps-blast-radius]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/blast-radius/SKILL.md
[ps-create-verification-skill]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/create-verification-skill/SKILL.md
[ps-epistemics]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/references/epistemics.md
[ps-feature-map]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/create-verification-skill/references/feature-map-example/README.md
[ps-interrogate]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/interrogate/SKILL.md
[ps-log-helper]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/show-me-your-work/scripts/log.sh
[ps-maintain-verification-skill]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/maintain-verification-skill/SKILL.md
[ps-make-bot-ui]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/make-bot-ui/SKILL.md
[ps-manifest]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/.cursor-plugin/plugin.json
[ps-no-comments]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/no-comments/SKILL.md
[ps-poteto-mode]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/SKILL.md
[ps-principle-attack-the-premise]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-attack-the-premise/SKILL.md
[ps-principle-test-behavior-not-implementation]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/principle-test-behavior-not-implementation/SKILL.md
[ps-recall]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/recall/SKILL.md
[ps-reflect]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/reflect/SKILL.md
[ps-setup-pstack]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/setup-pstack/SKILL.md
[ps-show-me-your-work]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/show-me-your-work/SKILL.md
[ps-swarm]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/swarm/SKILL.md
[ps-synthesizer]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/reflect/references/synthesizer.md
[ps-technical-writing]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/technical-writing/SKILL.md
[ps-why]: https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/SKILL.md
