# Shared helpers for dotfiles setup scripts.
# Source this file from scripts that call run_cmd.

VERBOSE="${VERBOSE:-0}"
for arg in "$@"; do
  case "$arg" in
    -v|--verbose)
      VERBOSE=1
      ;;
    *)
      ;;
  esac
done
export VERBOSE

_run_log="$(mktemp -t dotfiles-run.XXXXXX)"
cleanup_run_log() {
  rm -f "$_run_log"
}
trap cleanup_run_log EXIT

run_cmd() {
  : >"$_run_log"
  if [ "$VERBOSE" != "1" ]; then
    echo "Running: $*"
  fi
  if [ "$VERBOSE" = "1" ]; then
    sh -c "$*"
    return
  fi

  if ! sh -c "$*" >"$_run_log" 2>&1; then
    echo "Command failed: $*" >&2
    cat "$_run_log" >&2
    return 1
  fi
}
