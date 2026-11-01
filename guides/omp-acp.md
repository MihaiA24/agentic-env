# OMP in T3 Code and PyCharm

Use OMP's built-in **Agent Client Protocol (ACP)** server, not a Claude Code/Codex adapter or a new transport wrapper:

```sh
command -v omp
omp acp --help
```

The executable is the absolute path printed by `command -v omp`; its single argument is `acp`. ACP uses newline-delimited JSON-RPC on stdin/stdout, not an HTTP port. The client launches OMP, and OMP retains its own model providers, tools, prompts, skills, and sessions.

## Credentials and workspace

Authenticate with OMP on the machine that will run the agent before opening a client session:

```sh
omp login
```

Existing working OMP credentials need no new login. OMP advertises **Use existing local credentials** through ACP. Do not copy provider tokens into either client configuration. The client process must run as the same OS user with the same OMP home/profile to share those credentials; a remote T3 environment uses that server's OMP installation and credentials, not the browser's machine.

The client's selected project directory becomes the OMP session workspace. OMP advertises its available models and thinking options through ACP configuration options; select them in the client rather than assuming the client's built-in Claude/Codex account or model applies.

## PyCharm

Requires PyCharm with the JetBrains AI Assistant ACP interface enabled. JetBrains documents ACP agents as usable without a JetBrains AI subscription; model-provider access is still required.

1. Open **AI Chat → menu → Add Custom Agent**. This opens `~/.jetbrains/acp.json`.
2. Merge this entry into `agent_servers`, using your real absolute OMP executable path. Preserve other agents and existing MCP settings:

   ```json
   {
     "agent_servers": {
       "Oh My Pi": {
         "command": "/absolute/path/to/omp",
         "args": ["acp"]
       }
     }
   }
   ```

3. Select **Oh My Pi** in AI Chat. Use the existing-local-credentials authentication method if asked.
4. Select a model OMP reports, then perform the manual checks below. Restart PyCharm if its agent list does not refresh.

This file is shared by JetBrains IDEs, not specific to one PyCharm project. A separate OMP IDE-bridge plugin is not needed to register the native ACP agent. Exposing the IntelliJ MCP server is optional and is not part of this baseline; do not enable it merely to make ACP work.

Official instructions: [JetBrains custom ACP agents](https://www.jetbrains.com/help/ai-assistant/acp.html#add-a-custom-agent).

## T3 Code

Use a T3 Code release with **Local ACP command** support. This route is documented in the official [T3 Code v0.1.6 ACP guide](https://github.com/pingdotgg/t3code/blob/v0.1.6/docs/user/providers-acp.md#add-a-local-command). T3 negotiates ACP v1 with OMP; its separate orchestration-protocol version is not the ACP version.

1. Open **Settings → Providers → Add provider → Show more → Local ACP command**.
2. On the environment that holds the project, set:

   | Setting | Value |
   |---|---|
   | Display name | `Oh My Pi` |
   | Executable | Absolute path printed by `command -v omp` on that environment |
   | Arguments | One row containing `acp` |
   | Environment overrides | None for existing default-profile credentials |

3. Save, choose the existing-local-credentials method if prompted, and select **Oh My Pi** for a new thread.
4. Choose a model reported by OMP, then perform the checks below.

The executable field is not a shell: do not enter `omp acp` as one executable, use `~`/`$HOME` substitutions, or put JSON quotes around an argument. Use a local command rather than a Registry Pi entry: Pi and OMP are different distributions. T3's server owns the agent process even when the UI is remote.

Use the supported settings UI to register providers. Do not edit a running T3 database or replace a complete provider list with a single OMP entry. ACP providers are not T3's app-owned text-generation providers, so T3 may still need another provider for titles, commit messages, or PR descriptions.

For a stopped local T3 installation, the native server settings file is `~/.t3/userdata/settings.json` (default T3 home). If absent, this sparse file registers OMP without removing default providers:

```json
{
  "providerInstances": {
    "acpRegistry_omp": {
      "driver": "acpRegistry",
      "displayName": "Oh My Pi",
      "enabled": true,
      "config": {
        "source": "local",
        "commandPath": "/absolute/path/to/omp",
        "commandArgs": ["acp"]
      }
    }
  }
}
```

If the file already exists, preserve its other settings and providers; do not overwrite a differing instance. Prefer the UI while T3 is running to avoid racing its settings writer. `acpRegistry` is also the correct driver for a **local** command. [Settings schema](https://github.com/pingdotgg/t3code/blob/v0.1.6/packages/provider-acp-registry/src/settings.ts) · [Default-provider hydration](https://github.com/pingdotgg/t3code/blob/v0.1.6/apps/server/src/provider/ProviderInstanceRegistryHydration.ts#L49-L76).

## Permissions and MCP differences

`acp` alone inherits OMP's approval policy. A client's **Supervised** mode does not force OMP to request approval for every action.

- OMP can issue standard ACP permission requests for bash and destructive file operations. Ordinary content edits do not all use that bridge.
- To explicitly allow file reads/writes while gating execution, use separate arguments `acp`, `--approval-mode`, `write`. This is approval policy, not a filesystem/process sandbox.
- `always-ask` requires client **form elicitation** for ordinary content-edit approvals; without it, those edits fail closed. Do not assume every ACP client supports that extension.
- Explicit `--yolo`/`--approval-mode yolo` bypasses ordinary ACP permission requests. Do not use it to fix a missing dialog.
- ACP's default/plan mode selector is not an approval-mode selector; plan approval can auto-accept when the client lacks form elicitation.
- OMP disables ordinary on-disk MCP discovery in ACP mode. Only MCP servers supplied by the client in `session/new.mcpServers` are attached; CLI MCP availability is not proof of ACP MCP availability.

See [OMP ACP approvals](https://github.com/can1357/oh-my-pi/blob/v18.14.2/docs/approval-mode.md#acp-sessions) and [ACP session creation](https://github.com/can1357/oh-my-pi/blob/v18.14.2/packages/coding-agent/src/main.ts#L555-L610). No new MCP servers or approval-policy overrides are installed by this integration.

## Runnable protocol checks

From this checkout, with Python 3.12+ and OMP already installed:

```sh
# Native handshake and session create/close; no model prompt.
python3 omp/acp_smoke.py

# Also uses the current OMP model/account quota for a real file-tool turn.
python3 omp/acp_smoke.py --live

# Test the exact executable configured in a GUI rather than the PATH lookup.
python3 omp/acp_smoke.py --omp /absolute/path/to/omp --live
```

The live check creates a random `input.txt` in a disposable workspace and asks the model to copy it to `output.txt`. It requires an exact byte-content match, unchanged input, a streamed answer containing the random value, ACP tool-call events, and a completed turn. Both checks close the session and stop their own OMP process. `--session-dir` keeps their session artifacts inside the disposable workspace; that workspace is removed afterward. OMP's normal configuration and auth store are still used. The check does not change credentials or automatically approve client requests.

These checks prove OMP's transport, model access, local file tools, and streaming independently of a GUI. They do **not** prove client rendering, project-context attachments, permission dialogs, cancellation, or reconnect behavior.

## Manual client acceptance

Use a disposable project in each client; do not run the edit checks on valuable files.

1. **Connection/model:** select Oh My Pi, choose a model reported by OMP, and ask it to identify the project root. Confirm the displayed model and workspace are correct.
2. **Read/streaming:** create `acp-check.txt` with a unique value. Ask OMP to read it and report the exact value. Confirm streamed text and a visible file-tool action.
3. **Edit:** ask OMP to append one known line to that file. Confirm the actual file, diff presentation, and any approval interaction. Undo the edit through the client and inspect the file again.
4. **Context:** attach a selected code range or file through the client and ask about that exact selection. Do not infer this works from ordinary workspace reads.
5. **Cancel/reopen:** start a longer answer, cancel it, then send a short prompt. Close/reopen the thread and check whether the client restores or explicitly starts a new OMP session.

Report the client/version, selected provider/model, observed result for each step, and any error. For PyCharm failures, use **AI Chat → menu → Get ACP Logs**. Logs can contain source and prompts: redact them before sharing.

## Recorded evidence

2026-11-01, Linux x86_64, OMP **18.14.2**:

- Native `initialize` negotiated ACP **v1**, identified `omp`/`18.14.2`, and advertised existing-local-credentials authentication.
- `python3 omp/acp_smoke.py` passed session creation and closure.
- `python3 omp/acp_smoke.py --live` passed with `openai-codex/gpt-6.1-sol`: real random-input file copy, streamed answer/tool events, completed turn, and session closure.
- The host's pre-existing `~/.jetbrains/acp.json` already registered **Oh My Pi** with `/home/mihai/.bun/bin/omp` and `["acp"]`; it was preserved unchanged.
- Created the previously absent `~/.t3/userdata/settings.json` with the local `acpRegistry_omp` entry, the same OMP executable, and `["acp"]`.
- Launched the installed T3 Code **0.1.6** desktop app. Its Providers UI showed **Oh My Pi → Available**, the configured executable/argument, and OMP's discovered models; the default Claude and Codex providers remained present.
- In T3's actual desktop UI, added this checkout as a project and ran **OMP ACP Integration Smoke** with **Oh My Pi / GPT-6.1 Sol**, low thinking, and Supervised permissions. The completed turn displayed a real `Read /home/mihai/code/agentic-env/README.md` tool action, `OMP_ACP_OK`, the correct first heading, and the correct project root. The saved thread and answer survived a client reload.
- `uv run --frozen pytest -q`: **146 passed, 213 subtests passed**. `bun test omp/hooks/`: **12 passed**. Both native smoke modes passed after isolating their session artifacts.
- PyCharm desktop acceptance remains manual, as do client edits/undo, context attachment, approval behavior, and cancellation. The T3 test app was closed after verification; its provider, project, and smoke thread remain available on the next normal launch.

Protocol implementation: [OMP v18.14.2 ACP command](https://github.com/can1357/oh-my-pi/blob/v18.14.2/packages/coding-agent/src/commands/acp.ts) and [ACP agent](https://github.com/can1357/oh-my-pi/blob/v18.14.2/packages/coding-agent/src/modes/acp/acp-agent.ts).
