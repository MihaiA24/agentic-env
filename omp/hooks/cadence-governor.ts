/**
 * cadence-governor — nudges toward Hermes-measured work-unit discipline on OMP.
 *
 * Two measured defects, one mechanism:
 *
 * 1. Verification cadence (Q-C): Hermes verifies every ~18 tool calls and ends 94.2% of
 *    sessions green; OMP verifies every ~37 and ends 91.2% green. When too many calls pass
 *    without a verification run, the next tool result gets a one-line nudge appended.
 *
 * 2. write-vs-edit (Q-D): OMP overwrites whole files 3.15× more often than it edits, against
 *    its own tool policy, on the top output-token consumer (output = 12.8% of billed cost).
 *    A `write` that clobbers a pre-existing file of real size gets a one-line steer to `edit`.
 *
 * Why a hook and not a skill: prose mandates measured 15.6% adherence even when repeated three
 * times (HERMES.md), and Ponytail self-activated 0/10 times as a plain skill. Only force-injected
 * wiring has local evidence of changing behavior. Annotations ride on the documented
 * `tool_result` content-override path, so nothing new is inserted into the session transcript.
 */

import { statSync } from "node:fs";
import { classify } from "./verification-recorder.ts";

// ponytail: constants over config — revisit only if the recorder shows the nudges misfiring.
// Hermes median cadence ~18, OMP ~37; 25 targets the midpoint (doc Q-C).
const CADENCE_THRESHOLD = 25;
// Round-3 read-out 2026-08-11: nudges past the third are never heeded (continuation
// 41%→65%→70%+, tails to N=1600 in sessions with nothing classifiable to verify);
// 60% of all fired nudges were spam beyond N=75. Silent after 3; verification re-arms.
const MAX_UNHEEDED_NUDGES = 3;
// Below 1 KiB a full rewrite is as cheap as an edit; only steer on files with real content.
const EXISTING_FILE_MIN_BYTES = 1024;

interface ContentChunk {
	type: string;
	text?: string;
}

interface ToolCallEvent {
	toolName: string;
	input?: Record<string, unknown>;
}

interface ToolResultEvent {
	toolName: string;
	input?: Record<string, unknown>;
	content?: ContentChunk[];
	isError?: boolean;
}

interface HookApi {
	on(
		event: "tool_call",
		handler: (event: ToolCallEvent, ctx: unknown) => Promise<unknown> | unknown,
	): void;
	on(
		event: "tool_result",
		handler: (
			event: ToolResultEvent,
			ctx: unknown,
		) => Promise<{ content?: ContentChunk[] } | undefined> | { content?: ContentChunk[] } | undefined,
	): void;
}

export interface GovernorState {
	callsSinceVerify: number;
	lastNudgeAt: number;
	/** path -> pre-write size in bytes, recorded at tool_call time. */
	preWriteSizes: Map<string, number>;
}

export function createState(): GovernorState {
	return { callsSinceVerify: 0, lastNudgeAt: 0, preWriteSizes: new Map() };
}

function verificationCommand(event: { toolName: string; input?: Record<string, unknown> }): string | null {
	if (event.toolName !== "bash" && event.toolName !== "eval") return null;
	const cmd = String(event.input?.command ?? event.input?.code ?? "");
	return cmd && classify(cmd) ? cmd : null;
}

/** Shared by the hook and the test so the test exercises the real path. */
export function onToolCall(state: GovernorState, event: ToolCallEvent): void {
	if (event.toolName !== "write") return;
	const path = String(event.input?.path ?? "");
	if (!path) return;
	try {
		state.preWriteSizes.set(path, statSync(path).size);
	} catch {
		state.preWriteSizes.set(path, 0); // new file
	}
}

export function onToolResult(
	state: GovernorState,
	event: ToolResultEvent,
): { content: ContentChunk[] } | undefined {
	if (verificationCommand(event)) {
		state.callsSinceVerify = 0;
		state.lastNudgeAt = 0;
		return undefined;
	}
	state.callsSinceVerify += 1;

	const nudges: string[] = [];

	if (event.toolName === "write" && event.isError !== true) {
		const path = String(event.input?.path ?? "");
		const before = state.preWriteSizes.get(path) ?? 0;
		state.preWriteSizes.delete(path);
		if (before >= EXISTING_FILE_MIN_BYTES) {
			nudges.push(
				`[cadence-governor] This write overwrote an existing ${(before / 1024).toFixed(1)} KiB file. Prefer the edit tool (anchored hashline) for modifying existing files — whole-file rewrites are the top output-token cost in this stack.`,
			);
		}
	}

	if (
		state.callsSinceVerify >= CADENCE_THRESHOLD &&
		state.callsSinceVerify - state.lastNudgeAt >= CADENCE_THRESHOLD &&
		state.callsSinceVerify <= CADENCE_THRESHOLD * MAX_UNHEEDED_NUDGES
	) {
		state.lastNudgeAt = state.callsSinceVerify;
		nudges.push(
			`[cadence-governor] ${state.callsSinceVerify} tool calls since the last verification run. Run the relevant test/lint now — sessions that verify frequently end green measurably more often.`,
		);
	}

	if (nudges.length === 0) return undefined;
	return { content: [...(event.content ?? []), { type: "text", text: `\n${nudges.join("\n")}` }] };
}

export default function hook(pi: HookApi): void {
	const state = createState();
	pi.on("tool_call", (event) => {
		try {
			onToolCall(state, event);
		} catch {
			// Instrumentation must never affect tool execution.
		}
		return undefined;
	});
	pi.on("tool_result", (event) => {
		try {
			return onToolResult(state, event);
		} catch {
			return undefined;
		}
	});
}
