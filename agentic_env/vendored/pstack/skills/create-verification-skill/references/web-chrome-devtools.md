# Web and Electron: wrap the chrome-devtools CLI

Use this route when a web or Electron app has no browser harness in the repo. The `chrome-devtools` command ships in the npm package `chrome-devtools-mcp` (Apache-2.0). These notes match version 1.13.0. After a version change, recheck every command name with `chrome-devtools --help`.

## Pin the version

Add `chrome-devtools-mcp` as a dev dependency with the repo's package manager, so every checkout runs the same CLI. In a repo without a Node manifest, call it as `npx -y -p chrome-devtools-mcp@<version> chrome-devtools`. The verifier CLI is the only caller; agents run the verifier, never `chrome-devtools` directly.

## Give each checkout its own daemon

Every `chrome-devtools` command talks to one background daemon, and that daemon owns one browser. The CLI finds the daemon through a socket in `$XDG_RUNTIME_DIR/chrome-devtools-mcp/`, and `chrome-devtools start` restarts whichever daemon owns that socket. Set `XDG_RUNTIME_DIR` on every call to a directory derived from the checkout and created with mode 700. Socket paths are limited to about 100 bytes, so keep it short, for example `/tmp/verify-<app>-<first 8 hex characters of a hash of the checkout path>`.

## Start it with the privacy flags

By default the daemon sends usage statistics to Google, and its performance tools send trace URLs to Google's CrUX API. Any command sent to a stopped daemon starts one without flags. So `launch` always starts the daemon first:

```sh
XDG_RUNTIME_DIR="$RUN_DIR" chrome-devtools start \
  --no-usage-statistics --no-performance-crux \
  --userDataDir "$PROFILE_DIR" \
  --workspace "$CHECKOUT" --workspace "$EVIDENCE_DIR"
```

- For Electron, or a browser the app launches itself, replace `--userDataDir` with `--browserUrl http://127.0.0.1:<port>`, using the port derived from the checkout.
- `--workspace` limits the CLI's file tools to the checkout and the evidence directory. Without it, the CLI can read and write any path.
- The verifier also exports `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS=1`, so a daemon that starts any other way still opts out of usage statistics.
- `doctor` passes only when `chrome-devtools status` lists `--no-usage-statistics` and `--no-performance-crux` in `args`, together with this checkout's profile or browser URL.

## Map the verifier's commands

Page commands take the page ID as their first argument; `list_pages` prints the IDs.

| Verifier command | chrome-devtools command |
|---|---|
| `snapshot` | `take_snapshot <page>`: the accessibility tree, with the element IDs that actions take |
| `screenshot` | `take_screenshot <page> --filePath <evidence path>` |
| `record` | `screencast_start <page> --filePath <evidence path>.mp4`, then `screencast_stop <page>` |
| `console` | `list_console_messages <page>` |
| `network` | `list_network_requests <page>`, and `get_network_request` for one request |
| `trace` | `performance_start_trace <page>`, then `performance_stop_trace <page>` |
| Drive actions | `navigate_page`, `click`, `fill`, `type_text`, `press_key`, with element IDs from `take_snapshot` |
| `feature-flag` | The app's own flag mechanism; the CLI has no flag command |

`cleanup` runs `chrome-devtools stop` with the same `XDG_RUNTIME_DIR`, then removes the run directory and the profile. The evidence directory stays.
