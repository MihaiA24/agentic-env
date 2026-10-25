# Ponytail skills provenance

Source: [DietrichGebert/ponytail at `v4.9.0`](https://github.com/DietrichGebert/ponytail/tree/v4.9.0) (commit `0a4dd63ad4541f4f655c4108a295916f3c1d8fda`, 2026-08-08). Licence: [MIT, DietrichGebert](LICENSE).

The [manifest](../../skill-packs.json) selects four complete packages from `skills/`: `ponytail`, `ponytail-audit`, `ponytail-debt` and `ponytail-review`. `ponytail-gain` and `ponytail-help` are omitted (dropped 2026-10-26, see [Decisions §6](../../../DECISIONS_AI_TOOLING.md#6-skills)).

The force-injected ponytail descriptor in [`skill_bodies/`](../../skill_bodies) is separate: `agentic-configure-agent-mcps` installs it, and this pack does not replace it.

## Local adaptations

None. Every file is byte-identical to the tag.

## Updating

Re-copy the selected complete packages from a reviewed tag, update this record and the manifest `upstream.ref`, then record the reviewed fingerprints with `agentic-skill-drift --update-baseline`.
