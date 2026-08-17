/**
 * Smoke test for retention-canary.
 * Run: bun test omp/hooks/retention-canary.test.ts
 *
 * Exercises the real `checkRetention` path against real SQLite files and session mtimes
 * in a temp directory; nothing global is touched.
 */

import { afterAll, expect, test } from "bun:test";
import { Database } from "bun:sqlite";
import { mkdirSync, mkdtempSync, rmSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { checkRetention } from "./retention-canary.ts";

const root = mkdtempSync(join(tmpdir(), "retention-canary-"));
const banksDir = join(root, "banks");
const sessionsDir = join(root, "sessions", "-proj");
mkdirSync(banksDir, { recursive: true });
mkdirSync(sessionsDir, { recursive: true });

afterAll(() => rmSync(root, { recursive: true, force: true }));

function makeBank(name: string, createdAtDaysAgo: number | null): void {
	const dir = join(banksDir, name);
	mkdirSync(dir, { recursive: true });
	const db = new Database(join(dir, "mnemopi.db"));
	db.run("create table working_memory (created_at text)");
	db.run("create table episodic_memory (created_at text)");
	db.run("create table facts (created_at text)");
	if (createdAtDaysAgo !== null) {
		const stamp = new Date(Date.now() - createdAtDaysAgo * 86_400_000)
			.toISOString()
			.slice(0, 19)
			.replace("T", " "); // mnemopi stores UTC 'YYYY-MM-DD HH:MM:SS'
		db.run("insert into working_memory values (?)", [stamp]);
	}
	db.close();
}

function makeSession(name: string, daysAgo: number): string {
	const path = join(sessionsDir, name);
	writeFileSync(path, "{}\n");
	const t = new Date(Date.now() - daysAgo * 86_400_000);
	utimesSync(path, t, t);
	return path;
}

const current = makeSession("current.jsonl", 0);

test("fresh bank stays silent despite old sessions", () => {
	makeBank("fresh-abc123", 0);
	makeSession("old1.jsonl", 20);
	makeSession("old2.jsonl", 10);
	expect(checkRetention({ cwd: "/x/fresh", sessionFile: current, banksDir })).toBeNull();
});

test("stale bank with sessions since fires a loud warning", () => {
	makeBank("stale-abc123", 30);
	const dir = join(root, "sessions", "-stale");
	mkdirSync(dir, { recursive: true });
	const cur = join(dir, "current.jsonl");
	writeFileSync(cur, "{}\n");
	// Two sessions after the last retain, newest ≥7 days past it.
	for (const [name, daysAgo] of [["s1.jsonl", 5], ["s2.jsonl", 2]] as const) {
		const p = join(dir, name);
		writeFileSync(p, "{}\n");
		const t = new Date(Date.now() - daysAgo * 86_400_000);
		utimesSync(p, t, t);
	}
	const warning = checkRetention({ cwd: "/x/stale", sessionFile: cur, banksDir });
	expect(warning).toContain("[retention-canary]");
	expect(warning).toContain("stale-abc123");
	expect(warning).toContain("2 sessions");
});

test("current session file is excluded from the count", () => {
	makeBank("solo-abc123", 30);
	const dir = join(root, "sessions", "-solo");
	mkdirSync(dir, { recursive: true });
	const cur = join(dir, "current.jsonl");
	writeFileSync(cur, "{}\n");
	const old = join(dir, "old.jsonl");
	writeFileSync(old, "{}\n");
	const t = new Date(Date.now() - 8 * 86_400_000);
	utimesSync(old, t, t);
	// Only one prior session — below MIN_SESSIONS_SINCE, must stay silent.
	expect(checkRetention({ cwd: "/x/solo", sessionFile: cur, banksDir })).toBeNull();
});

test("no matching bank (new project) stays silent", () => {
	expect(checkRetention({ cwd: "/x/never-seen", sessionFile: current, banksDir })).toBeNull();
});

test("empty bank counts as never retained and fires", () => {
	makeBank("empty-abc123", null);
	const warning = checkRetention({ cwd: "/x/empty", sessionFile: current, banksDir });
	expect(warning).toContain("never (empty bank)");
});

test("leading dots are stripped from the project slug", () => {
	makeBank("dotted-abc123", 0);
	expect(checkRetention({ cwd: "/x/.dotted", sessionFile: current, banksDir })).toBeNull();
});
