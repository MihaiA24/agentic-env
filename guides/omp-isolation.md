# Opt-in OMP isolation on the Chuwi server

`agentic-omp-isolated` runs OMP and its descendants under nono, using the existing operator UID. It is separate from ordinary `omp`, bootstrap, updater, doctor and ACP registration. Installing agentic-env does not enable sandboxing. Linux/macOS/Windows machines used only as SSH clients need no sandbox installation.

## Deploy and authenticate

Run from a trusted shell on the Linux x86_64 server. Requirements: Python 3.12+, uv, the standalone OMP ELF executable, `/usr/bin/python3`, curl, normal `/usr` toolchain files, Landlock ABI **6 or later**, unprivileged user namespaces, seccomp user notification and pathname Unix-socket mediation. Unsupported enforcement fails; there is no unsandboxed fallback. The reviewed target is CachyOS, not macOS, Windows or every Linux distribution.

Install this checkout outside the project you intend to grant:

```bash
cd /path/to/agentic-env
uv tool install --force .

# Choose one existing project, not your entire home or every private checkout.
project="$HOME/code/agent-workspaces/example"
isolation="$HOME/.local/share/agentic-env/isolated-omp-example"
agentic-omp-isolated --instance "$isolation" init --project "$project"
agentic-omp-isolated --instance "$isolation" check
agentic-omp-isolated --instance "$isolation" run -- login openai-codex-device
agentic-omp-isolated --instance "$isolation" run -- --model openai-codex/gpt-5.6-luna
```

Use an available model returned by `run -- models openai-codex`. The model above was exercised in the recorded acceptance run, not promised for every account. From an uninstalled management checkout, prefix commands with `uv run --frozen`; the management checkout must remain outside the granted project. The module entry point is `python -m agentic_env.isolated_omp` in an environment with this package installed.

`init` refuses existing instance paths, symlinked instance components, overlapping project/control directories, the operator home or an ancestor, and a project containing the launcher source. It downloads checksum-pinned **nono 0.81.0** into this instance, snapshots the selected OMP executable (`--omp` overrides PATH discovery), creates a policy/integrity manifest, and proves an enforced `omp --version` launch. Failed initialization removes only its newly created instance. No personal settings, authentication stores, skills or hooks are copied. Project-local instructions/extensions remain project input: the sandbox constrains them, not their intentions.

The normal browser callback flow (`login openai-codex`) cannot bind port 1455 under this policy. OMP misleadingly describes this denial as a busy port. Use its supported **device flow**, which stores credentials as `openai-codex` without a local callback listener. Open the displayed provider URL and enter the code manually in a trusted browser; the sandbox cannot open the operator browser. The operator chooses the account and authorizes quota use.

## Effective authority

The generated `policy.json` is the exact instance policy. Review it before login. The launcher removes nono's implicit system/home/tool/scratch grant groups and retains mandatory deny groups.

| Surface | Grant |
|---|---|
| Writable directories | Exactly the canonical selected project and `INSTANCE/runtime` |
| Read-only directories | `/usr` and `/etc/ssl/certs` |
| Read-only files | Snapshotted OMP; `/etc/ld.so.cache`, `/etc/passwd`, `/etc/group`, CA bundle and OpenSSL configuration; `/dev/random`, `/dev/urandom`; `/proc/self/maps` |
| Read/write devices | `/dev/null`, `/dev/tty`, `/dev/ptmx` |
| HTTPS destinations | `auth.openai.com`, `chatgpt.com`, `github.com`, `codeload.github.com`, `objects.githubusercontent.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org` |
| Inherited workload environment | `PATH`, `TERM`, `LANG`, `USER`, `LOGNAME` only; PATH is fixed to `/usr/bin:/bin` |
| Explicit workload state | HOME, TMPDIR, `PI_CODING_AGENT_DIR` and XDG config/data/state/cache/runtime paths point into `INSTANCE/runtime` |
| Kernel/broker controls | Network, IPC and UTS namespaces; pathname Unix-socket mediation; same-sandbox signal scope; canonical-path command mediation; capability elevation disabled |

`/usr` includes installed tools and libraries, not just a few executables: anything confidential placed there is in the read grant. The CA bundle's canonical target is also granted (on the reviewed host, `/etc/ca-certificates/extracted/tls-ca-bundle.pem`). Bun needs the narrow process-maps read grant; all of `/proc` is not granted. Grants do not make otherwise privileged files writable.

The nono supervisor receives a newly constructed environment and its own HOME/XDG directories under `INSTANCE/broker`, outside the workload write grants. Its short temporary broker sockets use host `/tmp` to fit Linux pathname limits; workload TMPDIR remains dedicated. Provider tokens, Proton PATs, SSH/GPG agent sockets, D-Bus, display/desktop authority, Python injection variables and ambient nono options are not inherited. No host SSH, keyring or container-runtime socket is delegated, even if its pathname is inside the writable project.

Direct TCP/UDP and proxy bypass are denied. Approved HTTPS travels through nono's proxy; everything else is default-deny. This is a destination policy, not URL/account authorization. Git/package downloads can redirect to other domains and fail; SSH Git, arbitrary package mirrors, web search, external MCP/memory services, browser relays and host-local development servers are not enabled. Cached tools or dependencies outside the grants are unavailable. Review new destinations rather than disabling the proxy or namespace.

Installed privilege/admin commands are deny-only: `sudo`, `su`, `doas`, `pkexec`, `mount`, `umount`, `nsenter`, `unshare`, `systemctl`, `machinectl`, `reboot`, `shutdown`, `poweroff`. Nono resolves these to canonical executables; absolute-path invocation is denied too. This is defense in depth, **not** a ban on equivalent behavior: Python, shell built-ins, copied binaries and permitted tools can perform equivalent operations within their actual filesystem/network/privilege authority. There are no command capability grants, interactive elevation or browser-opening brokers.

## Credentials and deliberate changes

**Dedicated direct OAuth is the selected boundary.** Access and refresh tokens reside in `INSTANCE/runtime/agent/agent.db`; OMP and project tools can read, replace or exfiltrate those dedicated credentials through allowed destinations. Provider-side scope, revocation and quota remain necessary. OAuth refresh is normal OMP behavior and may rotate these credentials. This profile does not protect them from the agent itself.

Nono's built-in OpenAI API-key injection is not an automatic broker for this Codex device-OAuth/refresh flow. OMP offers a separate auth broker (refresh tokens stay server-side, access tokens reach trusted clients) and gateway (provider tokens stay server-side). Using either requires a separately reviewed service, authentication and narrow transport policy; this launcher does not connect to the operator's broker or create such infrastructure. Direct dedicated credentials, rather than a new broker service, were explicitly accepted for this implementation.

The manifest hashes the policy and both executable snapshots; `run` and `check` reject altered, missing or redirected trusted files. These hashes detect changes relative to the trusted manifest, not malicious changes by an unsandboxed process with the same UID. Keep the launcher, instance control files and their parents trusted. The runtime and project are intentionally mutable.

There is no force-update, policy editor, credential import or repair flag. To change the project, policy, nono version or OMP snapshot:

1. Stop sessions using the old instance and preserve project work.
2. Review source/profile changes and the new release checksum/toolchain. Host OMP updates do not replace an existing snapshot; `/usr` and other system files still follow host updates.
3. Initialize a **new** instance path, review its generated grants and rerun `check`.
4. Authenticate the new dedicated instance deliberately and repeat provider/tool acceptance. Do not copy the personal database, broker token or private configuration.
5. Revoke old dedicated provider credentials when retiring the instance. Preserve needed work and non-secret evidence, then remove only the retired instance yourself.

## Failure, recovery and limits

- Enforcement/setup errors return nonzero. Fix the named prerequisite and retry; never rerun ordinary `omp` as an automatic fallback.
- Integrity failures require review and a new instance, not recalculating hashes to bless unknown changes. Initialization collisions preserve existing data.
- Network/TLS/tool failures can identify missing read grants, an unapproved redirect or a required executable absent from `/usr`. Review the specific need; do not grant HOME, all `/etc`, all `/proc`, host sockets or unrestricted egress.
- Instance state can be changed by a compromised session and persist into its next run. After suspected compromise, revoke its dedicated provider session and create fresh state; retain project work separately for review.
- Ordinary unsandboxed sessions, existing checkouts and personal configuration remain unchanged. They retain full operator authority and can alter this same-user sandbox's trusted files. Launch from trusted operator code; OS enforcement starts at nono's workload, not at arbitrary untrusted bootstrap code.
- This is a shared-kernel capability sandbox, not a microVM, separate UID, metadata-hiding filesystem or resource/quota isolation. Known-path metadata can remain observable. Terminal access and approved authenticated endpoints remain authority. Anything secret already inside the selected project or runtime is exposed. Host kernel vulnerabilities and authorized-destination misuse are outside this boundary.
- Only the recorded OMP login, streaming, read/Bash project task and explicit security probes are proven. A complete build toolchain, interactive TUI, ACP desktop session and every optional OMP feature were not exercised.

## Recorded disposable acceptance — 2026-11-10

CachyOS Linux `7.3.3-1-cachyos`, x86_64, operator UID 1000, measured Landlock ABI 11; nono 0.81.0; standalone OMP 18.18.7 / Bun 1.4.4. Everything was created below `/tmp/agentic-nono-40iczvfb`, not installed into normal startup.

- `init --project …/project`: exit 0, enforced `omp/18.18.7` startup.
- `check`: all 14 scenarios passed: project read/write; denied outside read/write, symlink escape, policy/snapshot modification, ambient credentials, a host pathname socket inside the writable project, direct TCP/UDP, unapproved HTTPS and explicit proxy bypass; approved npm HTTPS and canonical `/usr/bin/mount` denial.
- `run -- login openai-codex-device`: fresh operator-authorized OAuth, exit 0, dedicated runtime SQLite only. No personal auth was copied.
- `run -- --model openai-codex/gpt-5.6-luna --thinking low --no-session --no-pty --no-lsp --no-skills --no-extensions --no-title --no-context-files --tools read,bash --mode json --max-time 120 --max-cost 0.10 --print 'Read isolation-input.txt using the read tool. Then use the bash tool to copy its exact contents to isolation-output.txt with a standard shell command. Do not touch any other files. End with ISOLATION_OK and the value you read.'`: exit 0. JSON contained streamed text deltas, successful `read` and Bash `cp -- isolation-input.txt isolation-output.txt`, and `ISOLATION_OK nono-acceptance-7a94e3d261b8490c`. Independently read output matched the input, including its newline.

[Retained non-secret evidence](../docs/omp-isolation-acceptance-2026-11-10.json) records identities, digests and selected observed events. Disposable credentials and binaries are not deployment artifacts. The repository-wide local gate is separate from these live checks; no full-gate success or permanent rollout is implied.

## Primary contracts

- [nono 0.81.0 release](https://github.com/nolabs-ai/nono/releases/tag/v0.81.0), archive SHA256 `7ecc33ff9c349bdfa84b4496e7a7555f67bcc33f1e125c7df9efb653c6c4e569`. Checksum integrity is not an independent publisher signature.
- [Security model](https://nono.sh/docs/cli/internals/security-model.md), [namespace isolation](https://nono.sh/docs/cli/features/namespace-isolation.md), [Landlock/socket mediation](https://nono.sh/docs/cli/internals/landlock.md), [environment](https://nono.sh/docs/cli/features/environment.md), [networking](https://nono.sh/docs/cli/features/networking.md), [command denial](https://nono.sh/docs/cli/features/dangerous-command-blocking.md).
- [Versioned nono credential injection](https://github.com/nolabs-ai/nono/blob/v0.81.0/docs/cli/features/credential-injection.mdx).
- [OMP 18.18.7 device OAuth](https://github.com/can1357/oh-my-pi/blob/v18.18.7/packages/ai/src/registry/oauth/openai-codex.ts), [device provider registration](https://github.com/can1357/oh-my-pi/blob/v18.18.7/packages/catalog/src/compat/rules/auth/openai-codex-device.kdl), [broker/gateway contract](https://github.com/can1357/oh-my-pi/blob/v18.18.7/docs/auth-broker-gateway.md).
