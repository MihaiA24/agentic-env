# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, the invocation choice, and router skills). Everything else about writing it is the universal reference in `SKILL.md`.

## Invocation

Two choices, trading the two loads:

- A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation always _includes_ user reach; a description only ever adds agent discovery, never removes the human's. The description is the skill's top-level context pointer, forced to stay loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is also one home for shared reference: another skill can invoke it, so reference needed by several skills lives in one place. Mechanics: omit `disable-model-invocation`, and write a model-facing description carrying the trigger branches (the pointer-writing rules in `SKILL.md` apply in full).
- A **user-invoked** skill runs only on the user's request or as a named step in a recipe the user explicitly invoked. Set `disable-model-invocation: true` and keep a short human-facing description. OMP hides it from the model's automatic skill listing but still resolves `skill://<name>`; hiding is not an access-control boundary. The installed Hermes runtime does not honor that flag in its listing, so prefix the description `Manual only:` and put the same invocation guard in the body. Do not claim zero context load or mechanically enforced manual invocation there.

Pick model-invocation when the agent should choose the method autonomously on a narrow trigger. Keep manual methods manual; an explicitly invoked recipe may load a named dependency without turning that dependency into an automatic trigger.

Shared reference may stay in an existing package and be loaded by an explicit path. OMP uses `skill://<name>/<file>`; Hermes uses `skill_view` with the skill name and `file_path`. Preserve supporting files at installation. Do not split out another public skill merely to share a reference.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): split off a model-invoked skill when a distinct job needs its own automatic trigger. You pay context load for the new description, so independent discovery must justify it. Named composition alone does not require another automatic skill.

## Router skills

When several manual skills become hard to remember, a manual router can name their jobs and explicitly compose the relevant method under the user's request. Keep direct tasks direct; do not make a router a universal prerequisite. Routing does not grant permission to read credentials, mutate infrastructure or publish.
