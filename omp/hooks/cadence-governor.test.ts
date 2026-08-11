/**
 * Smoke test for cadence-governor.
 * Run: bun test omp/hooks/cadence-governor.test.ts
 */

import { expect, test } from "bun:test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import hook, { createState, onToolCall, onToolResult } from "./cadence-governor.ts";

test("cadence nudge fires at threshold, re-arms, and resets on verification", () => {
	const state = createState();

	// 24 mundane calls: silence.
	for (let i = 0; i < 24; i++) {
		expect(onToolResult(state, { toolName: "read", content: [] })).toBeUndefined();
	}
	// 25th: nudge.
	const nudged = onToolResult(state, { toolName: "read", content: [{ type: "text", text: "x" }] });
	expect(nudged?.content?.at(-1)?.text).toContain("25 tool calls since the last verification");

	// 26th..49th: silence (re-arm window).
	for (let i = 0; i < 24; i++) {
		expect(onToolResult(state, { toolName: "read", content: [] })).toBeUndefined();
	}
	// 50th: second nudge.
	expect(onToolResult(state, { toolName: "grep", content: [] })?.content?.at(-1)?.text).toContain("50 tool calls");

	// A verification run resets everything.
	expect(
		onToolResult(state, { toolName: "bash", input: { command: "pnpm run lint" }, content: [] }),
	).toBeUndefined();
	expect(state.callsSinceVerify).toBe(0);
});

test("cadence nudge goes silent after three unheeded fires and re-arms on verification", () => {
	const state = createState();
	const texts: string[] = [];
	for (let i = 0; i < 150; i++) {
		const text = onToolResult(state, { toolName: "read", content: [] })?.content?.at(-1)?.text;
		if (text) texts.push(text);
	}
	// Fires at 25, 50, 75 — then silence, however long the session runs.
	expect(texts).toHaveLength(3);
	expect(texts[2]).toContain("75 tool calls");

	// A verification run re-arms the governor from zero.
	onToolResult(state, { toolName: "bash", input: { command: "pnpm run lint" }, content: [] });
	let lastText: string | undefined;
	for (let i = 0; i < 25; i++) {
		lastText = onToolResult(state, { toolName: "read", content: [] })?.content?.at(-1)?.text;
	}
	expect(lastText).toContain("25 tool calls");
});

test("write nudge fires only for pre-existing files of real size", () => {
	const dir = mkdtempSync(join(tmpdir(), "governor-"));
	const big = join(dir, "big.ts");
	writeFileSync(big, "x".repeat(2048));
	const fresh = join(dir, "new.ts");

	const state = createState();

	// Overwriting a 2 KiB existing file → steer to edit.
	onToolCall(state, { toolName: "write", input: { path: big } });
	const nudged = onToolResult(state, { toolName: "write", input: { path: big }, content: [] });
	expect(nudged?.content?.at(-1)?.text).toContain("Prefer the edit tool");

	// Creating a new file → silence.
	onToolCall(state, { toolName: "write", input: { path: fresh } });
	expect(onToolResult(state, { toolName: "write", input: { path: fresh }, content: [] })).toBeUndefined();

	// Failed write → silence.
	onToolCall(state, { toolName: "write", input: { path: big } });
	expect(
		onToolResult(state, { toolName: "write", input: { path: big }, content: [], isError: true }),
	).toBeUndefined();
});

test("default export registers both handlers and annotates through them", () => {
	type Result = { content?: Array<{ type: string; text?: string }> } | undefined;
	type Handler = (e: unknown, c: unknown) => Result;
	const handlers: Record<string, Handler> = {};
	// Test seam: the hook's overloaded `on` collapses to one shape when captured.
	const api = {
		on: (event: string, fn: unknown) => {
			handlers[event] = fn as Handler;
		},
	} as Parameters<typeof hook>[0];
	hook(api);
	expect(Object.keys(handlers).sort()).toEqual(["tool_call", "tool_result"]);

	let out: Result;
	for (let i = 0; i < 25; i++) {
		out = handlers.tool_result({ toolName: "read", content: [] }, {});
	}
	expect(out?.content?.at(-1)?.text).toContain("25 tool calls");
});
