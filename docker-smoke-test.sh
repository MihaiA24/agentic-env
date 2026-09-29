#!/usr/bin/env sh
set -eu

SKIP_INSTALL=${SKIP_INSTALL:-0}
_SCRIPT_DIR="$(CDPATH= cd "$(dirname "$0")" && pwd)"
. "$_SCRIPT_DIR/setup_helpers.sh"

echo "[1/5] Recording host and prerequisite evidence"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
uname -srm
id
if [ -f /etc/os-release ]; then cat /etc/os-release; fi
if [ "$(uname -s)" = Darwin ]; then sw_vers; fi
printf 'Run: %s\nRevision: %s\nHOME: %s\n' \
  "${AGENTIC_SMOKE_RUN_ID:-local}" "${AGENTIC_SMOKE_REVISION:-unknown}" "$HOME"
for prerequisite in uv python3 node npm npx curl git bash tar gzip xz unzip ps make cc c++; do
  command -v "$prerequisite" || { echo "Missing prerequisite: $prerequisite" >&2; exit 1; }
done
# Keep the prerequisite interpreter: Hermes installs a managed Python 3.11 that uv prefers.
_python="$(command -v python3)"
"$_python" -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ required"; print(sys.version)'
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) throw new Error("Node.js 20+ required"); console.log(process.version)'
uv --version
npm --version
git --version
curl --version

if [ "$SKIP_INSTALL" != "1" ]; then
  for command in hermes omp codex claude codebase-memory-mcp agentmemory skills \
    agentic-bootstrap agentic-install-agents agentic-install-skills-mcps \
    agentic-configure-agent-mcps agentic-update-stack agentic-stack-doctor \
    agentic-skill-drift; do
    if command -v "$command" >/dev/null 2>&1; then
      echo "Clean-host precondition failed: $command is already on PATH" >&2
      exit 1
    fi
  done
  for path in .hermes .omp .claude .claude.json .codex .agents .config/hermes .config/omp; do
    if [ -e "$HOME/$path" ] || [ -L "$HOME/$path" ]; then
      echo "Clean-host precondition failed: $HOME/$path already exists" >&2
      exit 1
    fi
  done
  echo "Clean-host preconditions passed: no agent binaries or configuration"
fi

_python_script="$(mktemp "${TMPDIR:-/tmp}/dotfiles-smoke-check.XXXXXX")"
cleanup() {
  cleanup_run_log
  rm -f "$_python_script"
}
trap cleanup EXIT

# Hermes-side wiring is secondary (doctor only warns); the smoke still pins it.
cat >"$_python_script" <<'PY'
from pathlib import Path
import subprocess

from agentic_env.configure_agent_mcps import (
    HERMES_SKILL_ROOT, MCP_SERVERS, SKILLS, load_yaml_object, validate_hermes_config,
)
from agentic_env.common import version_at_least
from agentic_env.stack_metadata import SKILLS_CLI_PACKAGE, STACK_VERSION_FLOORS

config_path = Path.home() / ".hermes" / "config.yaml"
config = load_yaml_object(config_path)
assert config, "~/.hermes/config.yaml must be a non-empty mapping"

required_servers = [
    MCP_SERVERS[name] for name in ("codebase-memory-mcp", "agentmemory")
]
assert validate_hermes_config(
    config, required_servers, required_provider="agentmemory"
), "~/.hermes/config.yaml has invalid Hermes MCP wiring"

for name in SKILLS:
    descriptor = HERMES_SKILL_ROOT / name / "SKILL.md"
    assert descriptor.is_file(), f"Missing Hermes skill descriptor: {descriptor}"
print("Hermes MCP wiring and matching skill descriptors verified")

version = subprocess.check_output(
    ["npx", "--yes", SKILLS_CLI_PACKAGE, "--version"], text=True,
).strip()
floor = STACK_VERSION_FLOORS["skills"]
assert version_at_least(version, floor), (
    f"skills CLI below the reviewed floor {floor}: {version}"
)
print(f"skills CLI: {version}")
PY

if [ "$SKIP_INSTALL" != "1" ]; then
  echo "[2/5] Installing agentic-env CLI"
  run_cmd "uv tool install --force --python \"$_python\" ."
fi

if [ "$SKIP_INSTALL" != "1" ]; then
  echo "[3/5] Running one-shot bootstrap"
  run_cmd "agentic-bootstrap"
fi

echo "[4/5] Verifying package module entry points and installed binaries"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.bootstrap --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.install_agents --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.install_skills_mcps --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.configure_agent_mcps --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.update_agentic_stack --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.stack_doctor --help"
run_cmd "uv run --frozen --python \"$_python\" python -m agentic_env.skill_drift --help"

failures=0

require_command() {
  cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "✓ command exists: $cmd"
    if "$cmd" --help >/dev/null 2>&1 || "$cmd" -h >/dev/null 2>&1 || "$cmd" --version >/dev/null 2>&1 || "$cmd" -V >/dev/null 2>&1 || "$cmd" version >/dev/null 2>&1; then
      echo "✓ smoke callable: $cmd"
    else
      echo "✗ smoke callable failed: $cmd"
      failures=$((failures + 1))
    fi
  else
    echo "✗ missing command: $cmd"
    failures=$((failures + 1))
  fi
}

require_command agentic-bootstrap
require_command agentic-install-agents
require_command agentic-install-skills-mcps
require_command agentic-configure-agent-mcps
require_command agentic-update-stack
require_command agentic-stack-doctor
require_command agentic-skill-drift

require_command hermes
require_command omp
require_command codex
require_command claude
require_command codebase-memory-mcp
require_command agentmemory

for command in hermes omp codex claude codebase-memory-mcp agentmemory; do
  echo "Version evidence: $command"
  "$command" --version
done

echo "[5/5] Verifying stack wiring (agentic-stack-doctor) and Hermes artifacts"
if [ "$SKIP_INSTALL" = "1" ]; then
  # Exercise forced updates on every host, including an already-compliant OMP.
  # OMP resolves release assets without the rate-limited GitHub REST API.
  run_cmd "agentic-update-stack"
fi
run_cmd "agentic-stack-doctor"
run_cmd "uv run --frozen --python \"$_python\" python \"$_python_script\""

if [ "$failures" -ne 0 ]; then
  echo "Failed checks: $failures"
  exit 1
fi

echo "Smoke test complete"
exit 0
