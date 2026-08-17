/**
 * retention-canary — warns when Mnemopi silently stops retaining for this project.
 *
 * Why this exists: the dotfiles bank took zero retains 07-19→08-10 while 11 sibling banks
 * retained fine on the same days and omp versions (17.1.5→17.3.5). The failure was
 * project-local, produced no errors, and self-healed — post-hoc root-causing eliminated
 * every suspect (forensics: agentic-env/docs/memory-backend-research.md). Nothing inside
 * the pipeline reports retention death, so the only defense is external detection: compare
 * the bank's newest memory row against session activity and warn in-context at the next
 * session start in the affected project.
 *
 * Bank lookup is by slug (basename of cwd, leading dots stripped) because the bank-id hash
 * suffix is not derivable from the compiled omp binary.
 * ponytail: basename collisions check every matching bank; a rare false warn on a sibling
 * project is acceptable for a tripwire. Upgrade path: exact hash if omp ever exposes it.
 */

import { Database } from "bun:sqlite";
import { readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join } from "node:path";

const BANKS_DIR = join(homedir(), ".omp", "agent", "memories", "mnemopi", "banks");
// The real gap ran 07-19→08-10 and was found 08-11. Replayed against these thresholds it
// would have fired on 07-26: ≥7 days silent across ≥2 sessions is anomalous because
// retention is automatic per completed turn.
const STALE_DAYS = 7;
const MIN_SESSIONS_SINCE = 2;
const DAY_MS = 86_400_000;

/** Newest memory timestamp in a bank (ms epoch), or null when empty/unreadable. */
export function newestMemoryMs(dbPath: string): number | null {
	try {
		const db = new Database(dbPath, { readonly: true });
		try {
			// Union of all three stores: consolidation prunes working_memory rows, so any
			// single table can false-fire.
			const row = db
				.query(
					`select max(created_at) m from (
						select created_at from working_memory
						union all select created_at from episodic_memory
						union all select created_at from facts)`,
				)
				.get() as { m: string | null } | null;
			if (!row?.m) return null;
			const ms = Date.parse(`${row.m.replace(" ", "T")}Z`); // stored as UTC 'YYYY-MM-DD HH:MM:SS'
			return Number.isNaN(ms) ? null : ms;
		} finally {
			db.close();
		}
	} catch {
		return null;
	}
}

/** Shared by the hook and the test so the test exercises the real path. */
export function checkRetention(opts: {
	cwd: string;
	/** Current session jsonl — its directory is the project's session history; itself excluded. */
	sessionFile: string;
	banksDir?: string;
}): string | null {
	const banksDir = opts.banksDir ?? BANKS_DIR;
	const slug = basename(opts.cwd).replace(/^\.+/, "");
	if (!slug) return null;

	let banks: string[];
	try {
		banks = readdirSync(banksDir).filter(
			(n) => n.startsWith(`${slug}-`) && /^[a-z0-9]+$/.test(n.slice(slug.length + 1)),
		);
	} catch {
		return null;
	}
	if (banks.length === 0) return null; // no bank yet — nothing to canary

	const current = basename(opts.sessionFile);
	const sessionsDir = dirname(opts.sessionFile);
	let mtimes: number[];
	try {
		mtimes = readdirSync(sessionsDir)
			.filter((n) => n.endsWith(".jsonl") && n !== current)
			.map((n) => statSync(join(sessionsDir, n)).mtimeMs);
	} catch {
		return null;
	}
	if (mtimes.length === 0) return null;
	const newestSession = Math.max(...mtimes);

	const warnings: string[] = [];
	for (const bank of banks) {
		// Empty bank counts as "never retained": sessions accumulating against an empty
		// bank is exactly the anomaly (retention is automatic per turn).
		const last = newestMemoryMs(join(banksDir, bank, "mnemopi.db")) ?? 0;
		const sessionsSince = mtimes.filter((t) => t > last).length;
		if (newestSession - last >= STALE_DAYS * DAY_MS && sessionsSince >= MIN_SESSIONS_SINCE) {
			const when = last
				? `${new Date(last).toISOString().slice(0, 10)} (${Math.floor((newestSession - last) / DAY_MS)} days before the latest session)`
				: "never (empty bank)";
			warnings.push(
				`[retention-canary] Mnemopi bank ${bank} last retained ${when}, but ${sessionsSince} sessions ran since. ` +
					`Retention may be silently dead (07-19→08-10 class gap). Check memory wiring; keep decisions in committed docs (ADR-0002).`,
			);
		}
	}
	return warnings.length ? warnings.join("\n") : null;
}

interface ContentChunk {
	type: string;
	text?: string;
}

interface ToolResultEvent {
	content?: ContentChunk[];
}

interface HookContext {
	cwd?: string;
	sessionManager?: { getSessionFile?: () => string | undefined };
}

interface HookApi {
	on(
		event: "tool_result",
		handler: (
			event: ToolResultEvent,
			ctx: HookContext,
		) => { content?: ContentChunk[] } | undefined,
	): void;
}

export default function hook(pi: HookApi): void {
	// No session_start event exists; run once on the first tool result instead.
	let checked = false;
	pi.on("tool_result", (event, ctx) => {
		if (checked) return undefined;
		checked = true;
		try {
			const sessionFile = ctx?.sessionManager?.getSessionFile?.();
			if (!sessionFile) return undefined;
			const warning = checkRetention({ cwd: ctx?.cwd ?? process.cwd(), sessionFile });
			if (!warning) return undefined;
			return { content: [...(event.content ?? []), { type: "text", text: `\n${warning}` }] };
		} catch {
			// Instrumentation must never break a tool result.
			return undefined;
		}
	});
}
