/**
 * Smoke test for verification-recorder.
 * Run: bun test omp/hooks/verification-recorder.test.ts
 *
 * Exercises the same `handleToolResult` path the hook uses, against a real SQLite file
 * in a temp directory (via OMP_VERIFICATION_DB); the global store is untouched.
 */

import { afterAll, expect, test } from "bun:test";
import { Database } from "bun:sqlite";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import hook, { canonicalize, classify, handleToolResult, parseExitCode } from "./verification-recorder.ts";

const root = mkdtempSync(join(tmpdir(), "verification-recorder-"));
const DB_PATH = join(root, "verification_evidence.db");
// The hook reads this lazily on first record, so setting it after import is safe.
process.env.OMP_VERIFICATION_DB = DB_PATH;

test("classify recognises verification commands and ignores the rest", () => {
	expect(classify("pnpm run lint")).toBe("lint");
	expect(classify("uv run pytest -q tests/")).toBe("test");
	expect(classify("npx tsc --noEmit")).toBe("typecheck");
	expect(classify("cargo build --release")).toBe("build");
	// Not verification — must be ignored so the store stays a quality signal.
	expect(classify("git status")).toBeNull();
	expect(classify("ls -la")).toBeNull();
	expect(classify("cat README.md")).toBeNull();
});

test("parseExitCode reads OMP's failure line, defaults to success", () => {
	expect(parseExitCode("all good", false)).toBe(0);
	expect(parseExitCode("boom\nCommand exited with code 2", false)).toBe(2);
	// isError with no exit line still counts as a failure.
	expect(parseExitCode("killed", true)).toBe(1);
});

test("canonicalize strips cd-prefix and chaining so commands group", () => {
	expect(canonicalize("cd /tmp/x && pnpm run lint -- --fix")).toBe("pnpm run lint --");
	expect(canonicalize("pytest -q && echo done")).toBe("pytest -q");
});

test("handleToolResult records a failing test run and skips non-verification", () => {
	const recorded = handleToolResult(
		{
			toolName: "bash",
			input: { command: "uv run pytest -q" },
			content: [{ type: "text", text: "1 failed\nCommand exited with code 1" }],
			isError: false,
		},
		{ cwd: "/tmp/proj", sessionId: "smoke-test" },
	);
	expect(recorded).toBe(true);

	const skipped = handleToolResult(
		{ toolName: "bash", input: { command: "git log --oneline" }, content: [] },
		{ cwd: "/tmp/proj", sessionId: "smoke-test" },
	);
	expect(skipped).toBe(false);

	const db = new Database(DB_PATH, { readonly: true });
	const { c } = db.query("select count(*) c from verification_events where session_id='smoke-test'").get() as {
		c: number;
	};
	expect(c).toBe(1);

	const row = db
		.query(
			"select kind, status, exit_code, canonical_command from verification_events where session_id='smoke-test' order by id desc limit 1",
		)
		.get() as { kind: string; status: string; exit_code: number; canonical_command: string };
	db.close();
	expect(row.kind).toBe("test");
	expect(row.status).toBe("failed");
	expect(row.exit_code).toBe(1);
	expect(row.canonical_command).toBe("uv run pytest -q");
});

test("default export registers a tool_result handler that records", () => {
	let handler: ((e: unknown, c: unknown) => unknown) | undefined;
	hook({
		on: (event, fn) => {
			expect(event).toBe("tool_result");
			handler = fn as (e: unknown, c: unknown) => unknown;
		},
	});
	expect(handler).toBeDefined();

	handler?.(
		{
			toolName: "bash",
			input: { command: "pnpm run lint" },
			content: [{ type: "text", text: "ok" }],
			isError: false,
		},
		{ cwd: "/tmp/proj", sessionManager: { getSessionFile: () => "hook-entry-test" } },
	);

	const db = new Database(DB_PATH, { readonly: true });
	const row = db
		.query(
			"select kind, status, session_id from verification_events where session_id='hook-entry-test' order by id desc limit 1",
		)
		.get() as { kind: string; status: string; session_id: string } | null;
	db.close();
	expect(row?.kind).toBe("lint");
	expect(row?.status).toBe("passed");
});

afterAll(() => rmSync(root, { recursive: true, force: true }));
