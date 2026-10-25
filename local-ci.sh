#!/usr/bin/env sh
# Local stand-in for the GitHub workflow, which runs only on manual dispatch since
# 2026-10-25. Like the workflow it tests the committed HEAD, never uncommitted edits:
# unit suites first, then Debian and Arch acceptance in containers, plus native macOS
# acceptance on an Apple Silicon Mac, in parallel. Runs on Linux or macOS with Docker.
# On success it writes local-ci.attestation; commit that file with the change.
#   ./local-ci.sh                 run every check, write the attestation
#   ./local-ci.sh --verify [REF]  pass only if REF (default HEAD) carries a matching attestation
set -eu

ATTESTATION=local-ci.attestation
ROOT="$(CDPATH= cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Every tracked file except the attestation: committing it keeps it valid,
# any other change invalidates it.
tree_hash() {
  git ls-tree -r "$1" | awk -F '\t' -v skip="$ATTESTATION" '$2 != skip' | git hash-object --stdin
}

if [ "${1:-}" = --verify ]; then
  ref=${2:-HEAD}
  want=$(tree_hash "$ref")
  have=$(git show "$ref:$ATTESTATION" 2>/dev/null | sed -n 's/^tree //p')
  if [ "$have" = "$want" ]; then
    echo "$ref: attested (tree $want)"
    exit 0
  fi
  echo "$ref: not attested (tree $want, recorded ${have:-none}); run ./local-ci.sh and commit $ATTESTATION" >&2
  exit 1
fi
[ "$#" -eq 0 ] || { echo "Usage: $0 [--verify [REF]]" >&2; exit 2; }
docker info >/dev/null 2>&1 || { echo "Start Docker first" >&2; exit 1; }
legs="debian arch"
if [ "$(uname -s)/$(uname -m)" = Darwin/arm64 ]; then
  legs="$legs macos"
  host="macOS $(sw_vers -productVersion) arm64"
  if [ -z "${AGENTIC_PREREQ_PATH:-}" ]; then
    brew list --versions uv python@3.12 node@24 xz >/dev/null 2>&1 || {
      echo "Native acceptance needs: brew install uv python@3.12 node@24 xz ca-certificates (or set AGENTIC_PREREQ_PATH)" >&2
      exit 1
    }
    AGENTIC_PREREQ_PATH="$(brew --prefix uv)/bin:$(brew --prefix python@3.12)/libexec/bin:$(brew --prefix node@24)/bin:$(brew --prefix xz)/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  fi
  export AGENTIC_PREREQ_PATH
else
  host="$(uname -s) $(uname -r) $(uname -m)"
  echo "Not an Apple Silicon Mac: skipping native macOS acceptance (dispatch the workflow to cover it)"
fi

sha=$(git rev-parse HEAD)
work=$(mktemp -d "${TMPDIR:-/tmp}/agentic-env-local-ci.XXXXXX")
mkdir "$work/tree"
git archive "$sha" | tar -x -C "$work/tree"
cd "$work/tree"
echo "Testing commit $sha (uncommitted changes are not part of it) in $work"

# clean-acceptance.sh reads the revision from GITHUB_SHA: the export has no .git.
export GITHUB_SHA="$sha" COMPOSE_PROJECT_NAME=agentic-env-local-ci
UV_PROJECT_ENVIRONMENT="$work/venv" uv run --frozen pytest -q -p no:cacheprovider
bun test omp/hooks/

linux_leg() {  # service [compose flags]: one container through all three passes
  service=$1
  shift
  container=$COMPOSE_PROJECT_NAME-$service
  docker rm -f "$container" >/dev/null 2>&1 || true
  docker compose "$@" run --build -d --name "$container" "$service" sleep infinity
  # Explicit cleanup: an EXIT trap in this backgrounded function does not fire under macOS /bin/sh.
  rc=0
  docker exec "$container" /bin/sh ./clean-acceptance.sh \
    && docker exec "$container" /bin/sh ./clean-acceptance.sh --update \
    && docker exec -e SKIP_INSTALL=1 "$container" /bin/sh ./clean-acceptance.sh \
    || rc=$?
  docker rm -f "$container" >/dev/null
  return "$rc"
}

macos_leg() {  # native, in a fresh acceptance HOME inside $work
  export AGENTIC_SMOKE_HOME="$work/macos-home"
  sh ./clean-acceptance.sh
  sh ./clean-acceptance.sh --update
  SKIP_INSTALL=1 sh ./clean-acceptance.sh
}

linux_leg fresh-install >"$work/debian.log" 2>&1 &
debian=$!
linux_leg fresh-install-arch --profile arch >"$work/arch.log" 2>&1 &
arch=$!
macos=
case $legs in *macos) macos_leg >"$work/macos.log" 2>&1 & macos=$! ;; esac
echo "Acceptance legs running ($legs); logs in $work"

failed=
collect() {  # leg pid
  if wait "$2"; then
    echo "pass $1"
  else
    failed="$failed $1"
    echo "FAIL $1, last lines of $work/$1.log:"
    tail -n 30 "$work/$1.log"
  fi
}
collect debian "$debian"
collect arch "$arch"
[ -z "$macos" ] || collect macos "$macos"
[ -z "$failed" ] || { echo "Failed:$failed. Logs kept in $work" >&2; exit 1; }

cd "$ROOT"
printf 'tree %s\ncommit %s\ndate %s\nhost %s\npassed pytest bun-hooks %s\n' \
  "$(tree_hash "$sha")" "$sha" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$host" "$legs" >"$ATTESTATION"
chmod -R u+w "$work" && rm -rf "$work"
echo "All checks passed. Commit it: git add $ATTESTATION && git commit -m 'chore: attest local checks'"
