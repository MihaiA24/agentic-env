/**
 * verification-recorder — records verification outcomes for OMP sessions.
 *
 * Why this exists: Hermes keeps a quality feedback loop (`~/.hermes/verification_evidence.db`,
 * 248 events, 83.9% pass rate). OMP records none — tool output spills to per-call logs with no
 * outcome, so no pass rate, edit-failure rate, or regression signal can be computed from a
 * session history. That gap makes a paired harness benchmark impossible, because one arm would
 * be unmeasurable.
 *
 * This hook mirrors the Hermes schema so the two are directly comparable.
 *
 * It only records commands that are verification-shaped (test / lint / typecheck / build).
 * Everything else is ignored, so the store stays a quality signal rather than a shell log.
 */

import { Database } from "bun:sqlite";
import { homedir } from "node:os";
import { join } from "node:path";

type Kind = "test" | "lint" | "typecheck" | "build";

interface ToolResultEvent {
	toolName: string;
	toolCallId?: string;
	input?: Record<string, unknown>;
	content?: Array<{ type: string; text?: string }>;
	isError?: boolean;
}

const DB_PATH = join(homedir(), ".omp", "agent", "verification_evidence.db");

/** Ordered longest-prefix-wins; first match decides the kind. */
const PATTERNS: Array<[Kind, RegExp]> = [
	["test", /\b(pytest|jest|vitest|mocha|go test|cargo test|bun test|phpunit|rspec|ctest)\b/],
	["test", /\b(npm|pnpm|yarn|bun|uv)\s+(run\s+)?tests?\b/],
	["lint", /\b(ruff|eslint|clippy|golangci-lint|shellcheck|hadolint|flake8|stylelint)\b/],
	["lint", /\b(npm|pnpm|yarn|bun)\s+(run\s+)?lint\b/],
	["lint", /\b(black|prettier|gofmt|rustfmt)\b.*--(check|list|diff)\b/],
	["typecheck", /\b(tsc|mypy|pyright|pyre)\b/],
	["typecheck", /\b(npm|pnpm|yarn|bun)\s+(run\s+)?(typecheck|type-check)\b/],
	["build", /\b(cargo build|go build|make\b|cmake --build)\b/],
	["build", /\b(npm|pnpm|yarn|bun)\s+(run\s+)?build\b/],
];

export function classify(command: string): Kind | null {
	const c = command.toLowerCase();
	for (const [kind, re] of PATTERNS) if (re.test(c)) return kind;
	return null;
}

/**
 * OMP's bash tool merges stderr and appends an exit line only on failure.
 * Absence of that line plus `isError !== true` means the command succeeded.
 */
export function parseExitCode(text: string, isError: boolean): number {
	const m = text.match(/Command exited with code (\d+)/i);
	if (m) return Number(m[1]);
	return isError ? 1 : 0;
}

/** Collapse a command to something groupable, e.g. `cd x && pnpm run lint -- --fix` -> `pnpm run lint`. */
export function canonicalize(command: string): string {
	let c = command.replace(/\s+/g, " ").trim();
	c = c.replace(/^(cd\s+\S+\s*&&\s*)+/i, "");
	c = c.split(/\s*(?:&&|\|\||;|\|)\s*/)[0] ?? c;
	return c.split(" ").slice(0, 4).join(" ").slice(0, 120);
}

let db: Database | null = null;
function open(): Database {
	if (db) return db;
	// Test seam: OMP_VERIFICATION_DB points the store at a temp file.
	db = new Database(process.env.OMP_VERIFICATION_DB ?? DB_PATH, { create: true });
	db.exec("PRAGMA journal_mode = WAL");
	db.exec(`CREATE TABLE IF NOT EXISTS verification_events (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		created_at TEXT NOT NULL,
		session_id TEXT,
		cwd TEXT,
		command TEXT NOT NULL,
		canonical_command TEXT NOT NULL,
		kind TEXT NOT NULL,
		status TEXT NOT NULL,
		exit_code INTEGER,
		output_summary TEXT
	)`);
	db.exec("CREATE INDEX IF NOT EXISTS idx_ve_kind_status ON verification_events(kind, status)");
	return db;
}

export function record(row: {
	sessionId?: string;
	cwd?: string;
	command: string;
	kind: Kind;
	exitCode: number;
	summary: string;
}): void {
	open()
		.query(
			`INSERT INTO verification_events
			 (created_at, session_id, cwd, command, canonical_command, kind, status, exit_code, output_summary)
			 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		)
		.run(
			new Date().toISOString(),
			row.sessionId ?? null,
			row.cwd ?? null,
			row.command.slice(0, 2000),
			canonicalize(row.command),
			row.kind,
			row.exitCode === 0 ? "passed" : "failed",
			row.exitCode,
			row.summary.slice(0, 500),
		);
}

/** Shared by the hook and the smoke test, so the test exercises the real path. */
export function handleToolResult(
	event: ToolResultEvent,
	ctx: { cwd?: string; sessionId?: string },
): boolean {
	if (event.toolName !== "bash" && event.toolName !== "eval") return false;
	const command = String(event.input?.command ?? event.input?.code ?? "");
	if (!command) return false;
	const kind = classify(command);
	if (!kind) return false;

	const text = (event.content ?? [])
		.filter((c) => c.type === "text" && typeof c.text === "string")
		.map((c) => c.text as string)
		.join("\n");
	const exitCode = parseExitCode(text, event.isError === true);

	record({
		sessionId: ctx.sessionId,
		cwd: ctx.cwd,
		command,
		kind,
		exitCode,
		summary: text.slice(-500),
	});
	return true;
}

interface HookContext {
	cwd?: string;
	sessionManager?: { getSessionFile?: () => string | undefined };
}

interface HookApi {
	on(
		event: "tool_result",
		handler: (event: ToolResultEvent, ctx: HookContext) => Promise<void> | void,
	): void;
}

export default function hook(pi: HookApi): void {
	pi.on("tool_result", (event, ctx) => {
		try {
			handleToolResult(event, {
				cwd: ctx?.cwd,
				sessionId: ctx?.sessionManager?.getSessionFile?.(),
			});
		} catch {
			// Never let instrumentation break a tool result.
		}
	});
}
