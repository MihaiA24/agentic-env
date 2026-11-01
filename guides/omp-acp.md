# OMP in T3 Code and PyCharm

OMP provides ACP v1 through `omp acp`. The native configurations live in [pycharm.json](../agentic_env/acp/pycharm.json) and [t3code.json](../agentic_env/acp/t3code.json).

## Copy the JSON

From this checkout:

```sh
uv run --frozen agentic-configure-acp \
  --client pycharm --client t3code --output-dir ./acp-config
```

This writes `acp-config/pycharm.json` and `acp-config/t3code.json`. The CLI replaces `omp` with its absolute executable path. It refuses existing output files. Pass `--omp /absolute/path/to/omp` if OMP is not on PATH.

Installed users can run `agentic-configure-acp` directly. The module entry is `python -m agentic_env.configure_acp`.

## Configure the clients

Close T3 Code before changing its settings. Omit `--output-dir` to add the registrations to their native files:

```sh
uv run --frozen agentic-configure-acp --client pycharm --client t3code
```

| Client | Configuration file |
|---|---|
| PyCharm and other JetBrains IDEs | `~/.jetbrains/acp.json` |
| T3 Code | `${T3CODE_HOME:-~/.t3}/userdata/settings.json` |

The command adds missing registrations and preserves other agents, settings, and extra fields. Matching entries remain byte-for-byte unchanged. Conflicting OMP entries or malformed JSON stop the operation before any selected file changes. Existing files receive `.agentic-env.bak` backups when changed. Working configuration symlinks keep their links; dangling symlinks fail.

Preview either mode with `--dry-run`. Repeat `--client` to select both clients. The command does not install clients, log in, or change credentials, MCP servers, or approval policy.

After configuration, select **Oh My Pi** in PyCharm's AI Chat or T3 Code's model picker. T3's Providers page shows the local command and discovered models. PyCharm may need a restart to refresh its agent list.

OMP uses the credentials and configuration of the OS user running the agent. Existing working credentials need no login. Otherwise run `omp login` on that machine. A remote T3 environment uses its server's installation and credentials. Do not copy tokens into client JSON. A JetBrains AI subscription is not required for custom ACP agents.

## Permissions and MCP

Client permission modes answer requests OMP emits. "Supervised" does not require approval before every edit and is not a sandbox.

- `acp` inherits OMP's approval policy. Extra arguments `--approval-mode write` allow reads/writes while gating execution. Some execution tools require client form elicitation.
- `always-ask` requires form elicitation for ordinary edit approvals. Without it, those edits fail closed. Explicit `yolo` bypasses ordinary ACP permission requests.
- ACP's default/plan selector does not select approval policy. Plan approval can auto-accept without client form elicitation.
- ACP clients supply MCP servers through `session/new.mcpServers`. OMP's normal on-disk MCP discovery is disabled in this mode.

T3 ACP providers do not supply its app-owned title, commit-message, or PR-description generation. Keep another provider for those actions if needed.

## Verify

```sh
python3 omp/acp_smoke.py
python3 omp/acp_smoke.py --live
```

The first command checks initialization and session creation/closure without a model prompt. `--live` spends current model quota to copy random file contents in a temporary workspace. It checks the files, streamed answer, and tool events. Both commands keep their session artifacts in that workspace and remove it afterward. They never grant client permission requests.

Previously verified on Linux with OMP 18.14.2 and T3 Code 0.1.6: native live read/write, T3's README read with the correct project root, and saved-thread restoration after a UI reload. This does not establish PyCharm UI behavior.

## Manual client acceptance

In each client, use a disposable project to check:

1. Read a file containing a unique value. Confirm the value, project root, and visible tool action.
2. Edit that file, inspect the diff and approval behavior, then undo and inspect the file again.
3. Attach a selected code range and ask about that selection.
4. Cancel a longer answer, send another prompt, and reopen the thread.

Report the client/version, selected model, and result for each step. PyCharm's **AI Chat menu → Get ACP Logs** collects failure details. Redact source, prompts, and credentials before sharing logs.

## Sources

- [OMP ACP implementation](https://github.com/can1357/oh-my-pi/blob/v18.14.2/packages/coding-agent/src/modes/acp/acp-agent.ts) and [approval behavior](https://github.com/can1357/oh-my-pi/blob/v18.14.2/docs/approval-mode.md#acp-sessions).
- [JetBrains custom agents](https://www.jetbrains.com/help/ai-assistant/acp.html#add-a-custom-agent).
- [T3 Code local ACP commands](https://github.com/pingdotgg/t3code/blob/v0.1.6/docs/user/providers-acp.md#add-a-local-command) and [settings schema](https://github.com/pingdotgg/t3code/blob/v0.1.6/packages/provider-acp-registry/src/settings.ts).
