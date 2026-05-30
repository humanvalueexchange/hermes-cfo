#!/usr/bin/env bash
# hermes-install.sh — Bootstrap Hermes CFO on a fresh DGX Spark
# Part of the bare-metal restore sequence (Phase 3 post-Timeshift)
# Run from: ~/hermes-cfo/scripts/hermes-install.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_PROFILE=~/.hermes/profiles/main
HERMES_HOOKS=~/.hermes/agent-hooks
ENV_FILE=~/.hermes-mcp.env

echo "╔══════════════════════════════════════════════════╗"
echo "║       Hermes CFO — Install / Bootstrap           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Verify Hermes agent is installed ──────────────────────────────────────
if ! command -v hermes &>/dev/null; then
  echo "ERROR: Hermes agent not found. Install from https://hermes.ai before running this script."
  exit 1
fi
echo "✅ Hermes agent found: $(hermes --version 2>/dev/null || echo 'version unknown')"

# ── 2. Verify secret env file exists ─────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo ""
  echo "⚠️  Secret env file not found: $ENV_FILE"
  echo "   Copy config/hermes-env.template and fill in your secrets:"
  echo "   cp $REPO_ROOT/config/hermes-env.template $ENV_FILE"
  echo "   nano $ENV_FILE"
  exit 1
fi

# Load secrets
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

if [ -z "${HVE_MCP_API_KEY:-}" ]; then
  echo "ERROR: HVE_MCP_API_KEY not set in $ENV_FILE"
  exit 1
fi
echo "✅ Secrets loaded from $ENV_FILE"

# ── 3. Ensure profile directory exists ───────────────────────────────────────
mkdir -p "$HERMES_PROFILE"
mkdir -p "$HERMES_HOOKS"

# ── 4. Apply config template → live config ───────────────────────────────────
echo ""
echo "→ Applying config template..."
sed "s/\${HVE_MCP_API_KEY}/$HVE_MCP_API_KEY/g" \
  "$REPO_ROOT/config/hermes-config.template.yaml" \
  > "$HERMES_PROFILE/config.yaml"
echo "✅ Config written to $HERMES_PROFILE/config.yaml"

# ── 5. Install SOUL.md ────────────────────────────────────────────────────────
cp "$REPO_ROOT/docs/SOUL.md" "$HERMES_PROFILE/SOUL.md"
echo "✅ SOUL.md installed to $HERMES_PROFILE/SOUL.md"

# ── 6. Install hooks ─────────────────────────────────────────────────────────
cp "$REPO_ROOT/src/hooks/inject-market-data.sh" "$HERMES_HOOKS/inject-market-data.sh"
chmod +x "$HERMES_HOOKS/inject-market-data.sh"
echo "✅ Market data hook installed"

# ── 7. Restart Hermes gateway ─────────────────────────────────────────────────
if systemctl --user is-active --quiet hermes-gateway.service 2>/dev/null; then
  echo ""
  echo "→ Restarting Hermes gateway..."
  systemctl --user restart hermes-gateway.service
  sleep 2
  systemctl --user status hermes-gateway.service --no-pager | head -8
  echo "✅ Hermes gateway restarted"
else
  echo ""
  echo "ℹ️  Hermes gateway service not running — start manually:"
  echo "   systemctl --user start hermes-gateway.service"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║       Hermes CFO install complete ✅              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Verify: hermes -p main 'get_node_diagnostic'"
