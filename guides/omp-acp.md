# OMP in T3 Code and PyCharm

OMP provides ACP v1 through `omp acp`. The native configurations live in [pycharm.json](../agentic_env/acp/pycharm.json) and [t3code.json](../agentic_env/acp/t3code.json).

## Install the applications

On macOS with [Homebrew](https://brew.sh/) already installed:

```sh
uv run --frozen agentic-install-agents --client t3code --client pycharm --yes
```

This installs the `t3-code` and `pycharm` casks. Repeat `--client` to choose both, or select the unchecked desktop rows in the interactive installer. Desktop clients are opt-in: `--all` and noninteractive bootstrap still install only agent CLIs. Combine `--all` with explicit `--client` flags to install both.

Existing application bundles, PyCharm launchers (including JetBrains Toolbox), and installed casks are left alone; update them through their original app updater or package manager. For a Homebrew-managed installation, use `brew upgrade --cask t3-code pycharm`. Installation does not configure ACP, install OMP, sign in, or install/enable PyCharm's AI Assistant plugin. `agentic-update-stack` and doctor do not manage these optional applications.

On Linux/Windows, or without Homebrew, install [T3 Code](https://github.com/pingdotgg/t3code/releases) and [PyCharm](https://www.jetbrains.com/pycharm/download/) manually. An explicit unsupported automatic-install request fails rather than reporting success. Enable [JetBrains AI Assistant](https://www.jetbrains.com/help/ai-assistant/installation-guide-ai-assistant.html) for ACP chat. T3 Code 0.1.6 supports this registration; older versions without the `acpRegistry` provider must be upgraded first.


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

## OpenAI Standard/Fast

OMP 18.15.0 advertises only Mode, Model, and Thinking over ACP. T3's native Codex Standard/Fast footer is not provided by this integration; changing the registration JSON cannot add the missing OMP configuration option.

With an OpenAI model selected, send these provider commands in the conversation:

```text
/fast on
/fast status
/fast off
```

`on` selects OpenAI's `priority` tier when the model supports it; `off` clears priority/ultrafast, returning an otherwise unconfigured session to normal service. It does not clear another explicit tier such as `flex`. These commands update only the session, not global settings. Priority may cost more or consume quota faster; status confirms the configured tier, not a latency guarantee.

Verified directly over ACP with OMP 18.15.0 and `openai-codex/gpt-6.1-sol`: on → status on → off → status off, with priority/cleared-tier records in the disposable session. This is protocol evidence, not a T3/PyCharm UI check. A picker requires OMP to advertise and handle a service-tier config option upstream.


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
- [Homebrew T3 Code](https://formulae.brew.sh/cask/t3-code) and [PyCharm](https://formulae.brew.sh/cask/pycharm).
- [OMP ACP option builder](https://github.com/can1357/oh-my-pi/blob/v18.15.0/packages/coding-agent/src/modes/acp/acp-agent.ts#L2236-L2282), [`/fast` handler](https://github.com/can1357/oh-my-pi/blob/v18.15.0/packages/coding-agent/src/slash-commands/builtin-modes.ts#L75-L109), and [T3 agent-provided options](https://github.com/pingdotgg/t3code/blob/v0.1.6/docs/user/providers-acp.md#models-and-options).
