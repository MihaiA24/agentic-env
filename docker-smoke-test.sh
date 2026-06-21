#!/usr/bin/env sh
set -eu

SKIP_INSTALL=${SKIP_INSTALL:-0}

if [ "$SKIP_INSTALL" != "1" ]; then
  echo "[1/5] Installing agent CLIs"
  uv run --script install-agents.py --all --yes

  echo "[2/5] Installing MCP/tooling"
  uv run --script install-skills-mcps.py --all-mcps --yes

  echo "[3/5] Configuring agent MCP servers"
  uv run --script configure-agent-mcps.py --yes
fi

if [ "$SKIP_INSTALL" != "1" ]; then
  echo "[4/5] Verifying installed binaries"
else
  echo "[4/5] Verifying installed binaries (SKIP_INSTALL=1)"
fi

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

require_command hermes
require_command omp
require_command codex
require_command claude
require_command lean-ctx
require_command codebase-memory-mcp
require_command agentmemory


echo "[5/5] Verifying Hermes and OMP config artifacts"
node - <<'JS'
const fs = require('fs');
const path = require('path');
const home = process.env.HOME;

if (!home) {
  throw new Error('HOME is not set');
}

const hermes = path.join(home, '.hermes', 'config.yaml');
if (!fs.existsSync(hermes)) {
  throw new Error('missing ~/.hermes/config.yaml');
}
const text = fs.readFileSync(hermes, 'utf8');
for (const name of ['lean-ctx', 'codebase-memory-mcp', 'agentmemory']) {
  if (!text.includes(`${name}:`)) {
    throw new Error(`~/.hermes/config.yaml missing ${name} MCP entry`);
  }
}
if (!/^\s*provider:\s*agentmemory\s*$/m.test(text)) {
  throw new Error('~/.hermes/config.yaml missing memory.provider=agentmemory');
}

const settings = path.join(home, '.pi', 'agent', 'settings.json');
if (!fs.existsSync(settings)) {
  throw new Error('missing ~/.pi/agent/settings.json');
}

const obj = JSON.parse(fs.readFileSync(settings, 'utf8'));
const extensions = obj && obj.extensions;
if (!Array.isArray(extensions)) {
  throw new Error('~/.pi/agent/settings.json extensions is not a list');
}
const extRefTilde = '~/.pi/agent/extensions/agentmemory';
const extRefAbs = path.join(home, '.pi', 'agent', 'extensions', 'agentmemory');
if (!extensions.includes(extRefTilde) && !extensions.includes(extRefAbs)) {
  throw new Error('~/.pi/agent/settings.json missing agentmemory extension');
}

const extPath = path.join(home, '.pi', 'agent', 'extensions', 'agentmemory', 'index.ts');
if (!fs.existsSync(extPath)) {
  throw new Error('missing OMP agentmemory extension index.ts');
}

for (const mcpPath of [
  path.join(home, '.omp', 'agent', 'mcp.json'),
  path.join(home, '.pi', 'agent', 'mcp.json'),
]) {
  if (!fs.existsSync(mcpPath)) {
    throw new Error(`missing ${mcpPath}`);
  }
  const mcp = JSON.parse(fs.readFileSync(mcpPath, 'utf8'));
  if (!mcp || typeof mcp.mcpServers !== 'object' || Array.isArray(mcp.mcpServers)) {
    throw new Error(`${mcpPath} missing mcpServers object`);
  }
  for (const name of ['lean-ctx', 'codebase-memory-mcp', 'agentmemory']) {
    if (!mcp.mcpServers[name]) {
      throw new Error(`${mcpPath} missing ${name} MCP entry`);
    }
  }
}

for (const skillsRoot of [
  path.join(home, '.hermes', 'skills'),
  path.join(home, '.omp', 'agent', 'skills'),
  path.join(home, '.pi', 'agent', 'skills'),
]) {
  for (const name of ['lean-ctx', 'codebase-memory-mcp', 'agentmemory']) {
    const skillPath = path.join(skillsRoot, name, 'SKILL.md');
    if (!fs.existsSync(skillPath)) {
      throw new Error(`missing skill ${skillPath}`);
    }
  }
}
JS

if [ "$failures" -ne 0 ]; then
  echo "Failed checks: $failures"
  exit 1
fi

echo "Smoke test complete"
exit 0
