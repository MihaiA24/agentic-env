#!/usr/bin/env python3
"""Exercise installed OMP over ACP; --live also spends model quota in a scratch project."""

import argparse
import asyncio
import json
import secrets
import shutil
import tempfile
from pathlib import Path


async def smoke(command: str, live: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="omp-acp-smoke-") as directory:
        workspace = Path(directory)
        token = secrets.token_hex(16)
        (workspace / "input.txt").write_text(token, encoding="utf-8")
        with tempfile.TemporaryFile() as stderr:
            process = await asyncio.create_subprocess_exec(
                command, "acp", "--session-dir", str(workspace / ".sessions"),
                cwd=workspace, limit=4 * 1024 * 1024,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=stderr,
            )
            sequence = 0
            chunks: list[str] = []
            tool_calls: set[str] = set()

            async def request(method: str, params: dict) -> dict:
                nonlocal sequence
                sequence += 1
                request_id = sequence
                process.stdin.write((json.dumps({
                    "jsonrpc": "2.0", "id": request_id,
                    "method": method, "params": params,
                }) + "\n").encode())
                await process.stdin.drain()
                while line := await process.stdout.readline():
                    message = json.loads(line)
                    if message.get("id") == request_id and "method" not in message:
                        if "error" in message:
                            raise RuntimeError(f"{method}: {message['error']}")
                        return message["result"]
                    if "id" in message:
                        # Never silently grant a permission or execute a client-side tool.
                        raise RuntimeError(f"Client interaction required: {message.get('method')}")
                    if message.get("method") == "session/update":
                        update = message["params"]["update"]
                        if update["sessionUpdate"] == "agent_message_chunk":
                            content = update.get("content", {})
                            if content.get("type") == "text":
                                chunks.append(content["text"])
                        if update["sessionUpdate"] in ("tool_call", "tool_call_update"):
                            tool_calls.add(update["toolCallId"])
                raise RuntimeError(f"OMP exited before replying to {method}")

            try:
                initialized = await request("initialize", {
                    "protocolVersion": 1,
                    "clientInfo": {"name": "agentic-env-smoke", "version": "1"},
                    "clientCapabilities": {
                        "fs": {"readTextFile": False, "writeTextFile": False},
                        "terminal": False,
                    },
                })
                if initialized["protocolVersion"] != 1 or initialized["agentInfo"]["name"] != "omp":
                    raise RuntimeError(f"Unexpected ACP agent: {initialized}")
                print(f"PASS initialize: omp {initialized['agentInfo']['version']}, ACP v1")
                session = await request("session/new", {"cwd": directory, "mcpServers": []})
                session_id = session["sessionId"]
                selected = {option["id"]: option["currentValue"] for option in session.get("configOptions", [])}
                print(f"PASS session/new: model={selected.get('model', 'not advertised')}, mode={selected.get('mode', 'not advertised')}")
                if live:
                    print("Running live read/write check using the current OMP model and credentials...", flush=True)
                    result = await request("session/prompt", {
                        "sessionId": session_id,
                        "prompt": [{"type": "text", "text": (
                            "Integration smoke check in this disposable project. Use your file tools "
                            "to read input.txt and create output.txt with exactly the same contents, "
                            "without adding a newline. Do not run shell commands or change any other "
                            "files. Reply with the copied contents."
                        )}],
                    })
                    if result.get("stopReason") != "end_turn":
                        raise RuntimeError(f"Prompt did not complete: {result}")
                    if (workspace / "input.txt").read_text(encoding="utf-8") != token:
                        raise RuntimeError("The input file was unexpectedly changed")
                    if (workspace / "output.txt").read_text(encoding="utf-8") != token:
                        raise RuntimeError("The output file does not match the unread random input")
                    if token not in "".join(chunks) or not tool_calls:
                        raise RuntimeError("Missing streamed answer or ACP tool-call events")
                    print("PASS session/prompt: random input copied exactly; answer and tool calls streamed")
                await request("session/close", {"sessionId": session_id})
                print("PASS session/close")
            finally:
                if process.returncode is None:
                    process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), 10)
                except TimeoutError:
                    process.kill()
                    await process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--omp", default=shutil.which("omp"), help="Absolute OMP executable (default: PATH lookup)")
    parser.add_argument("--live", action="store_true", help="Use current model credentials/quota to exercise file tools and streaming")
    args = parser.parse_args()
    if not args.omp:
        parser.error("omp is not on PATH; install OMP or supply --omp")
    try:
        asyncio.run(asyncio.wait_for(smoke(str(Path(args.omp).resolve()), args.live), 180 if args.live else 60))
    except (OSError, RuntimeError, ValueError, KeyError, TimeoutError) as exc:
        parser.exit(1, f"FAIL ACP smoke: {exc or 'deadline exceeded'}\n")


if __name__ == "__main__":
    main()
