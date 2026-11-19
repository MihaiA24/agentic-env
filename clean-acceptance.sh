#!/usr/bin/env sh
# Run the shared smoke contract without inheriting user tools, config or credentials.
set -eu

_SCRIPT_DIR="$(CDPATH= cd "$(dirname "$0")" && pwd -P)"
_prereq_path=${AGENTIC_PREREQ_PATH:-/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}
_skip_install=${SKIP_INSTALL:-0}
case "$_skip_install" in
  0|1) ;;
  *) echo "SKIP_INSTALL must be 0 or 1" >&2; exit 1 ;;
esac
if [ "$#" -eq 0 ]; then
  set -- /bin/sh ./docker-smoke-test.sh
elif [ "$#" -eq 1 ] && [ "$1" = --update ]; then
  _skip_install=1
  set -- agentic-bootstrap
else
  echo "Usage: $0 [--update]" >&2
  exit 1
fi
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
_real_home="$(CDPATH= cd "$HOME" && pwd -P)"
if [ "$_smoke_home" = "$_real_home" ]; then
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
_uv_cache="$_smoke_home/.cache/uv"
_npm_cache="$_smoke_home/.cache/npm"
if [ -n "${AGENTIC_ACCEPTANCE_CACHE:-}" ]; then
  case "$AGENTIC_ACCEPTANCE_CACHE" in
    /*) ;;
    *) echo "AGENTIC_ACCEPTANCE_CACHE must be an absolute path" >&2; exit 1 ;;
  esac
  mkdir -p "$AGENTIC_ACCEPTANCE_CACHE"
  _cache="$(CDPATH= cd "$AGENTIC_ACCEPTANCE_CACHE" && pwd -P)"
  case "$_cache/" in
    //|"$_real_home/"|"$_smoke_home/"*|"$_SCRIPT_DIR/"*)
      echo "Acceptance cache must be outside the checkout and acceptance HOME, not real HOME or /" >&2
      exit 1 ;;
  esac
  if [ "$(git -C "$_cache" rev-parse --is-inside-work-tree 2>/dev/null || true)" = true ]; then
    echo "Acceptance cache must not be inside a Git worktree" >&2
    exit 1
  fi
  for _directory in "$_cache/artifacts" "$_cache/uv" "$_cache/python-downloads" "$_cache/npm" "$_cache/npm/_cacache"; do
    [ ! -L "$_directory" ] || { echo "Acceptance cache directory must not be a symlink: $_directory" >&2; exit 1; }
    mkdir -p "$_directory"
  done
  mkdir -p "$_npm_cache"
  if [ -L "$_npm_cache/_cacache" ]; then
    [ "$(readlink "$_npm_cache/_cacache")" = "$_cache/npm/_cacache" ] || {
      echo "Acceptance npm content cache points to another cache" >&2; exit 1;
    }
  elif [ -e "$_npm_cache/_cacache" ]; then
    echo "Acceptance npm content cache is not a shared-cache symlink" >&2
    exit 1
  else
    ln -s "$_cache/npm/_cacache" "$_npm_cache/_cacache"
  fi
  _uv_cache="$_cache/uv"
  set -- AGENTIC_ARTIFACT_CACHE="$_cache/artifacts" UV_PYTHON_CACHE_DIR="$_cache/python-downloads" "$@"
fi
mkdir -p "$_smoke_home/.tmp"
printf 'Acceptance HOME (retained for checks-only): %s\n' "$_smoke_home"

cd "$_SCRIPT_DIR"
# Command-scope config survives isolation. Older Git/libcurl pairs can corrupt
# GitHub ref advertisements over HTTP/2; do not depend on ignored system config.
exec env -i \
  HOME="$_smoke_home" USER="$(id -un)" LOGNAME="$(id -un)" \
  PATH="$_smoke_home/.local/bin:$_smoke_home/.bun/bin:$_prereq_path" \
  SHELL=/bin/bash TERM=dumb CI=1 PYTHONUTF8=1 \
  TMPDIR="$_smoke_home/.tmp" \
  XDG_CONFIG_HOME="$_smoke_home/.config" XDG_CACHE_HOME="$_smoke_home/.cache" \
  XDG_DATA_HOME="$_smoke_home/.local/share" XDG_STATE_HOME="$_smoke_home/.local/state" \
  UV_CACHE_DIR="$_uv_cache" UV_TOOL_DIR="$_smoke_home/.local/share/uv/tools" \
  UV_TOOL_BIN_DIR="$_smoke_home/.local/bin" UV_PYTHON_INSTALL_DIR="$_smoke_home/.local/share/uv/python" \
  UV_PROJECT_ENVIRONMENT="$_smoke_home/.venv" UV_NO_CONFIG=1 \
  npm_config_prefix="$_smoke_home/.local" npm_config_cache="$_npm_cache" \
  npm_config_userconfig="$_smoke_home/.npmrc" npm_config_globalconfig="$_smoke_home/.npmrc-global" \
  BUN_INSTALL="$_smoke_home/.bun" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
  GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.version GIT_CONFIG_VALUE_0=HTTP/1.1 \
  AGENTIC_ENV_ROOT="$_SCRIPT_DIR" \
  AGENTIC_SMOKE_RUN_ID="${GITHUB_RUN_ID:-local}/${GITHUB_RUN_ATTEMPT:-1}" \
  AGENTIC_SMOKE_REVISION="${GITHUB_SHA:-$(git -c safe.directory="$_SCRIPT_DIR" -C "$_SCRIPT_DIR" rev-parse HEAD)}" \
  SKIP_INSTALL="$_skip_install" VERBOSE="${VERBOSE:-0}" \
  "$@" </dev/null
