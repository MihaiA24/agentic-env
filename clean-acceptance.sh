#!/usr/bin/env sh
# Run the shared smoke contract without inheriting user tools, config or credentials.
set -eu

_SCRIPT_DIR="$(CDPATH= cd "$(dirname "$0")" && pwd)"
_dotfiles_root="$(CDPATH= cd "$_SCRIPT_DIR/.." && pwd)"
_prereq_path=${AGENTIC_PREREQ_PATH:-/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}
_skip_install=${SKIP_INSTALL:-0}
case "$_skip_install" in
  0|1) ;;
  *) echo "SKIP_INSTALL must be 0 or 1" >&2; exit 1 ;;
esac
if [ "$(id -u)" -eq 0 ]; then
  echo "Run clean acceptance as an ordinary user, not root" >&2
  exit 1
fi
if [ "$_skip_install" = 1 ]; then
  : "${AGENTIC_SMOKE_HOME:?Set AGENTIC_SMOKE_HOME to the already provisioned acceptance HOME}"
  [ -d "$AGENTIC_SMOKE_HOME" ] || { echo "Acceptance HOME does not exist" >&2; exit 1; }
else
  AGENTIC_SMOKE_HOME=${AGENTIC_SMOKE_HOME:-$(mktemp -d "${TMPDIR:-/tmp}/agentic-env-smoke.XXXXXX")}
  mkdir -p "$AGENTIC_SMOKE_HOME"
fi
_smoke_home="$(CDPATH= cd "$AGENTIC_SMOKE_HOME" && pwd -P)"
if [ "$_smoke_home" = "$(CDPATH= cd "$HOME" && pwd -P)" ]; then
  echo "Acceptance HOME must not be your real HOME" >&2
  exit 1
fi
if [ "$_skip_install" = 0 ]; then
  for entry in "$_smoke_home"/* "$_smoke_home"/.[!.]* "$_smoke_home"/..?*; do
    if [ -e "$entry" ] || [ -L "$entry" ]; then
      echo "Clean acceptance requires an empty AGENTIC_SMOKE_HOME: $_smoke_home" >&2
      exit 1
    fi
  done
fi
mkdir -p "$_smoke_home/.tmp"
printf 'Acceptance HOME (retained for checks-only): %s\n' "$_smoke_home"

cd "$_SCRIPT_DIR"
exec env -i \
  HOME="$_smoke_home" USER="$(id -un)" LOGNAME="$(id -un)" \
  PATH="$_smoke_home/.local/bin:$_smoke_home/.bun/bin:$_prereq_path" \
  SHELL=/bin/bash TERM=dumb CI=1 PYTHONUTF8=1 \
  TMPDIR="$_smoke_home/.tmp" \
  XDG_CONFIG_HOME="$_smoke_home/.config" XDG_CACHE_HOME="$_smoke_home/.cache" \
  XDG_DATA_HOME="$_smoke_home/.local/share" XDG_STATE_HOME="$_smoke_home/.local/state" \
  UV_CACHE_DIR="$_smoke_home/.cache/uv" UV_TOOL_DIR="$_smoke_home/.local/share/uv/tools" \
  UV_TOOL_BIN_DIR="$_smoke_home/.local/bin" UV_PYTHON_INSTALL_DIR="$_smoke_home/.local/share/uv/python" \
  UV_PROJECT_ENVIRONMENT="$_smoke_home/.venv" UV_NO_CONFIG=1 \
  npm_config_prefix="$_smoke_home/.local" npm_config_cache="$_smoke_home/.cache/npm" \
  npm_config_userconfig="$_smoke_home/.npmrc" npm_config_globalconfig="$_smoke_home/.npmrc-global" \
  BUN_INSTALL="$_smoke_home/.bun" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
  AGENTIC_DOTFILES_ROOT="$_dotfiles_root" \
  AGENTIC_SMOKE_RUN_ID="${GITHUB_RUN_ID:-local}/${GITHUB_RUN_ATTEMPT:-1}" \
  AGENTIC_SMOKE_REVISION="${GITHUB_SHA:-$(git -c safe.directory="$_dotfiles_root" -C "$_dotfiles_root" rev-parse HEAD)}" \
  SKIP_INSTALL="$_skip_install" VERBOSE="${VERBOSE:-0}" \
  /bin/sh ./docker-smoke-test.sh "$@" </dev/null
